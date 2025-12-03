## KVCache Chatbot 概觀

KVCache Chatbot 是一個以「文件輔助多輪對話」為核心的聊天系統，採用前後端分離架構。它同時支援本地與遠端的 LLM，提供高效的文件問答體驗，並透過 KV 快取最佳化推論效能。

- **前端（`src/web`）– Gradio 介面**
  - 文件上傳與管理
  - 文件選擇與快取控制
  - 支援串流的聊天介面
  - 模型管理面板（啟動 / 停止 / 重啟、狀態、日誌）

- **後端（`src/api`）– FastAPI REST API**
  - 多輪對話的 Session 管理
  - 文件上傳、解析、切塊 / 分組與 RAG 檢索
  - 本地模型伺服器的生命週期管理
  - 透過 OpenAI 相容 API 串接 LLM（OpenAI、Gemini、本地伺服器等）
  - 以文件內容進行 KV 快取預熱

高階流程如下：

1. 使用者在前端上傳文件。
2. 後端抽取並儲存文件內容（檔案寫入 `uploads/`，中介資料存於記憶體）。
3. 使用者按下「Cache」按鈕後，後端會將「套用系統提示模板後的文件內容」送給模型做一次短推論，以預先填充 KV 快取。
4. 在聊天過程中，使用者選擇文件；後端會將該文件內容注入系統提示（system prompt），並連同對話歷史一起送往 LLM 服務。
5. LLM 的回應以串流方式返回前端顯示。

---

## 架構設計重點

### 入口與應用程式生命週期

- **主程式（`src/api/main.py`）**
  - 建立 FastAPI 應用程式實例並掛載各個 router：
    - `session` – 對話 Session 管理
    - `document` – 文件管理與快取操作
    - `model` – 本地模型伺服器啟停與狀態
    - `logs` – 模型日誌查詢
    - `upload` – 傳統（legacy）上傳端點，為相容性保留
  - 定義 `async` 生命週期管理（`lifespan`）：
    - 確保上傳目錄（`settings.documents.upload_dir`）存在。
    - 啟動背景工作，用以定期清理過期的對話 Session。
    - 建立模型日誌 Session，並輸出模型伺服器將使用的日誌檔路徑。
    - 從 `env.yaml` 載入模型設定，並以**第一個已設定的模型**初始化全域 LLM 服務：
      - 若沒有任何模型，或第一個模型沒有正確設定 API key，後端會在啟動時直接失敗並提供清楚錯誤訊息。
      - 會合併該模型的完整 completion 參數（含 `custom_params`），並傳入 LLM 服務。
    - 啟動時會記錄目前使用的模型名稱、Base URL 以及關鍵 completion 參數，以提升可觀測性。
  - 在關閉階段：
    - 停止 Session 清理的背景工作。
    - 若本地模型伺服器仍在執行，則進行優雅關閉。

### Session 層

- **Session 服務（`src/api/services/session_service.py`）**
  - `SessionManager` 使用記憶體中的字典儲存所有對話 Session。
  - 每個 `ConversationSession` 具備：
    - `session_id`
    - 訊息列表
    - 建立時間與最後活躍時間戳
    - 可選的文件內容與檔名（保留舊版「Session 綁文件」的能力）
  - 透過背景工作定期清理過期 Session：
    - 超時秒數可設定（預設為 3600 秒）。
    - 每 5 分鐘掃描一次。
  - 設計上刻意保持簡單，方便未來替換為 Redis / 資料庫等外部儲存。

### LLM 層

- **LLM 服務（`src/api/services/llm_service.py`）**
  - 封裝了對 OpenAI 相容 `/chat/completions` API 的呼叫，使用 `httpx.AsyncClient` 進行非同步請求。
  - 支援：
    - 透過 SSE 進行串流回應（`data: ...` 與 `[DONE]`）。
    - 以泛型 `completion_params` 字典方式，傳入所有 completion 相關參數（如 `temperature`、`max_tokens`、`top_p`、`repeat_penalty`、`chat_template_kwargs` 等）。
  - 全域實例 `llm_service`：
    - 在啟動階段由 `settings.all_models` 的第一個模型進行初始化。
    - 之後可在執行期間透過 `reconfigure(model, api_key, base_url, **completion_params)` 重新設定，而不需重新建立新實例。
  - 自動配置保護機制：
    - 若 `api_key` 缺失或為 `"empty"`，服務會嘗試從 `settings.all_models` 中選出一個可用模型並自動重設配置。
    - 若找不到任何合適模型，會拋出清楚的錯誤訊息，提示使用者正確設定 `env.yaml`。
  - 所有 API 呼叫都會透過 `model_log_service` 紀錄：
    - 請求的 metadata 與部分回應片段，以利除錯與行為追蹤。

### RAG（檢索增強生成）層

- **RAG 服務（`src/api/services/rag_service.py`）**
  - 採用輕量級的 BM25 檢索機制，而非 embedding 型相似度。
  - 為支援中英混合文本，使用可配置的 tokenizer：
    - 優先嘗試使用進階 tokenizer（如 Jieba + OpenCC）。
    - 若不可用則退回簡單的正則切詞（英文單字、中文字元與數字）。
  - 提供兩種主要檢索方法：
    - `retrieve_most_similar_group`：
      - 以**群組（group）**為單位運作，輸入包含 `group_id`、`merged_content`、`chunk_ids`、`total_tokens` 等欄位。
      - 對每個群組計算 BM25 分數並回傳前 k 筆結果。
    - `retrieve_by_chunk_with_group`：
      - 先在**切塊（chunk）**層級做 BM25 檢索，取得分數最高的 chunk。
      - 再將每個命中的 chunk 映射回其所屬的群組，回傳群組內容給 LLM，同時附帶 chunk 層級資訊（便於前端高亮顯示等）。
  - 具備詳細的日誌輸出：
    - 記錄斷詞結果、中間的 BM25 分數、排序結果與最終選擇。
    - 讓檢索行為透明且易於調校與除錯。

### KV 快取機制

- **設計目標**
  - 透過 KV 快取加速針對同一份（或同一組）文件的重複查詢。
  - 確保快取階段與實際聊天時使用的前綴提示完全一致，使模型能重用既有的 key/value 狀態。

- **驗證流程**
  - 在執行任何快取操作（例如 `POST /api/v1/documents/cache/{doc_id}`）之前，系統會：
    - 確認本地模型伺服器目前正在執行。
    - 比對 `llm_service.model` 與 `model_server.config.alias` 是否相同，確保 LLM 服務與模型伺服器指向同一個模型設定。
    - 記錄當前的模型名稱、Base URL 與 completion 參數。
  - 若模型伺服器未啟動或設定不一致，API 會回傳 HTTP 503 並附上具體的錯誤說明。

- **系統提示模板對齊**
  - 一個關鍵修正是確保「快取操作」與「一般聊天請求」：
    - 都使用設定中的 `system_prompt_template`。
    - 以**相同方式包裝文件內容**來建立系統訊息。
  - 如此可以保證快取時與聊天時的文件前綴在位元層級上完全一致，讓 KV 快取的前綴重用生效。

- **生命週期**
  - KV 快取與本地模型伺服器進程綁定：
    - 當使用者對文件執行「Cache」操作時，透過短推論填充快取。
    - 快取在模型伺服器存活期間可被多個 Session、多次請求重複使用。
    - 當模型伺服器以「重置」方式重啟時，KV 快取也會被清空。

---

## 技術棧與系統特性

### 後端

- **主要框架與函式庫**
  - FastAPI：定義 API 端點與主要 Web 框架。
  - Pydantic：請求 / 回應模型與資料驗證。
  - Uvicorn：執行後端的 ASGI 伺服器。
  - httpx：非同步 HTTP 客戶端，用於呼叫 LLM API 與處理串流。
  - PyYAML：載入 `env.yaml`，管理模型與伺服器設定。
  - aiofiles：處理文件上傳時的非同步檔案 I/O。

- **後端特性**
  - 清楚區分：
    - Router：HTTP 端點與路由層。
    - Service：業務邏輯（Session、文件、LLM、模型、RAG、日誌等）。
    - 外部整合：模型伺服器、檔案系統、第三方 API。
  - 透過 `env.yaml` 的統一格式，同時支援本地與遠端模型設定。

### 前端

- **框架**
  - Gradio：建置聊天介面與操作面板的 Web UI 框架。
  - HTTP 客戶端（如 httpx 或等效工具）：與後端 API 溝通。

- **UI 功能**
  - 具檔案驗證的文件上傳區。
  - 文件清單與下拉選單（支援重新整理）。
  - 支援串流回應的聊天介面。
  - 模型管理控制項與狀態顯示。
  - 展示模型部署與執行狀態的日誌檢視功能。

### 模型設定與管理

- **模型定義（`env.yaml`）**
  - 同時支援：
    - `local_models`：由本地模型伺服器（例如 llama.cpp）提供的模型。
    - `remote_models`：OpenAI 相容 API（OpenAI、Gemini 等）。
  - 每個模型項目可包含：
    - `serving_name`
    - `tokenizer`
    - `base_url`
    - `api_key`
    - `completion_params`（如 temperature、max_tokens，以及任意自訂參數）
    - 適用於本地伺服器的 `serving_params`（如 `ctx_size`、`reasoning_format`、`n_gpu_layers` 等）。

- **執行時行為**
  - 後端啟動時，會從 `settings.all_models` 中取出第一個模型並配置 `llm_service`。
  - 當使用者透過模型管理端點切換模型時，後端會：
    - 呼叫 `reconfigure` 重新設定 `llm_service`。
    - 視情況啟動或停止本地模型伺服器。
  - KV 快取與快取驗證邏輯都會依照目前的作用中模型設定運作。

### 儲存策略

- **記憶體**
  - Session：
    - 儲存在 `SessionManager._sessions` 中。
    - 包含訊息歷史、時間戳與（舊版）綁定的文件資訊。
  - 文件：
    - 文件中介資料與預處理後內容儲存在文件管理服務中（記憶體）。

- **檔案系統**
  - 上傳的原始檔案寫入 `uploads/` 目錄。
  - 模型日誌寫入 `src/api/logs/` 目錄下的檔案，並以 Session 區分模型伺服器的日誌。

- **擴充性考量**
  - 目前的實作主要針對本機或單例部署優化：
    - 以記憶體為主的儲存方式簡單且快速，但不具分散式能力。
    - 模型伺服器以單一進程執行，並發量有限。
  - 設計與文件皆預留未來擴充空間，例如：
    - 將 Session 搬移到 Redis 或其他外部儲存。
    - 以資料庫管理持久化的文件中介資料。
    - 使用物件儲存（如 S3）保存文件內容。
    - 水平擴充多個模型伺服器實例並透過負載平衡進行調度。


