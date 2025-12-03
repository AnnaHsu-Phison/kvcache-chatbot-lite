# KVCache Chatbot

A modern multi-turn conversation chatbot with document upload support and KV cache optimization, featuring a clean separation between frontend (Gradio) and backend (FastAPI).

## ✨ Key Features

- 💬 **Multi-turn Conversations**: Maintains conversation history for context-aware responses
- 📄 **Document Management**: Upload and select documents independently from chat sessions with PDF support
- ⚡ **Streaming Responses**: Real-time streaming for better user experience
- 🚀 **KV Cache Integration**: Optimized document processing with pre-caching for local models
- 🔧 **Flexible Model Management**: Support for both local and remote models with dynamic switching
- 🧠 **Reasoning Models Support**: Enhanced configuration for reasoning models (e.g., GPT-OSS-20B) with extended timeouts
- 🎨 **Configurable Prompts**: Customizable prompt templates for fine-tuned control over conversation and RAG contexts
- 🔌 **Clean Architecture**: RESTful API with frontend-backend separation

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** (recommended: Python 3.10+)
- **uv** package manager (recommended) or pip
- **Git** (for cloning the repository)

### Installation & Setup

**Manual Setup (Recommended for First-Time Setup)**

#### ⚙️ 1. Setup Configuration
```bash
cd src/api
cp env.example.yaml env.yaml
```
Overwrite or modify `env.yaml` with this [configuration](https://hackmd.io/@kenyo3023/SJJ11_dk-e)

---

#### 🛠️ 2. Start Service

##### 👁️ For better viewing experience, you can execute the frontend and backend separately

**Install Backend**
```bash
pip install -r src/api/requirements.txt
```

**Execute Backend**
```bash
cd src/api && python main.py --port 3023
# Use 'cd src/api && python main.py --help' to view the available options
```
Then view the **backend API docs** in browser through `http://localhost:3023/docs`

**Install Frontend**
```bash
pip install -r src/web/requirements.txt
```

**Execute Frontend**
```bash
cd src/web && python app.py --backend-port 3023
# Use 'cd src/web && python app.py --help' to view the available options
```
Then view the **frontend website** in browser through `http://localhost:7860`

> **Important**: The backend `--port` and frontend `--backend-port` must be aligned

##### 🔍 Monitor Model Deployment Progress

**Monitor Progress** (Windows)
```powershell
netstat -ano | findstr :13141  # This is the default model deployment port
# Command template: netstat -ano | findstr :{MODEL_DEPLOY_PORT:-13141}
```

**Monitor Progress** (Linux/macOS)
```bash
lsof -i :13141  # This is the default model deployment port
# Command template: lsof -i :{MODEL_DEPLOY_PORT:-13141}
```

### Access the Application
- **Frontend**: http://localhost:7860
- **Backend API**: http://localhost:8000 (default, customizable via `--port`)
- **API Documentation**: http://localhost:8000/docs

## 📚 Documentation

### 🛠️ Installation Guide
For detailed installation instructions, dependency management, and configuration:
**[📖 GETTING_STARTED.md](docs/quick_start_guide.md)**

### 🎯 Usage Guide
For comprehensive usage instructions, workflows, and troubleshooting:
**[📖 QUICK_START.md](docs/quick_start_guide.md)**

### 🏗️ Architecture Overview
For system architecture, data flow, and technical details:
**[📖 ARCHITECTURE.md](docs/arch.md)**

## 🎮 Basic Usage

1. **Configure Models**: Set up your models in `src/api/env.yaml` (local and/or remote)
2. **Select Model**: Choose from the model dropdown (shows type indicators)
3. **Start Local Models**: Click "Start with Reset" or "Start without Reset" for local models (remote models are ready immediately)
4. **Upload Documents**: Use the left sidebar to upload `.pdf` files
5. **Select Document**: Choose from dropdown to use document context
6. **Cache Documents**: Use "Cache" button for faster document processing (KV cache for local models)
7. **Chat**: Type messages and get responses with document context and streaming

## 🔧 Configuration

### Configuration File Setup

Create `env.yaml` in `src/api/` directory (copy from `env.example.yaml`):

```bash
cd src/api
cp env.example.yaml env.yaml
```

### YAML Configuration Structure

The system uses YAML format for flexible model and server configuration:

```yaml
server:
    exe_path: C:\path\to\llama-server.exe
    log_path: C:\path\to\logs\maestro_llama.log
    cache_dir: R:\

models:
    # Local models (self-hosted)
    local_models:
      - model_name_or_path: /path/to/model.gguf
        serving_name: my-local-model
        tokenizer: meta-llama/Llama-3.1-8B-Instruct
        base_url: http://localhost:13141/v1
        api_key: not-needed
        completion_params:
            temperature: 0.7
            max_tokens: 2000
        # Optional: Serving parameters for model server
        serving_params:
            ctx_size: 16384
            n_gpu_layers: 100
            timeout: 900  # Extended timeout for reasoning models

      # GPT-OSS-20B Reasoning Model - Recommended Configuration
      - model_name_or_path: /path/to/gpt-oss-20b-GGUF.gguf
        serving_name: ggml-org/gpt-oss-20b-GGUF
        tokenizer: openai/gpt-oss-20b
        base_url: http://localhost:13141/v1
        api_key: not-needed
        completion_params:
            temperature: 0.0
            max_tokens: 20000
            # Recommended completion parameters for GPT-OSS-20B reasoning model
            repeat_penalty: 1.1
            repeat_last_n: 64
            chat_template_kwargs:
                reasoning_effort: low
        serving_params: # Llamacpp serving args
            log_file: /path/to/logging.log
            # Recommended serving parameters for GPT-OSS-20B reasoning model
            # More details can visit https://llama-cpp-python.readthedocs.io/en/latest/api-reference/
            ctx_size: 131072
            reasoning_format: deepseek
            jinja: True
            swa_full: True

  # Remote models (APIs, other machines)
  remote_models:
        # OpenAI
      - provider: openai
        model: gpt-4o-mini
        serving_name: gpt-4o-mini
        base_url: https://api.openai.com/v1
        api_key: YOUR_OPENAI_API_KEY
        completion_params:
            temperature: 0.7
            max_tokens: 4000

        # Google Gemini (OpenAI-compatible)
      - provider: openai
        model: gemini-2.0-flash
        serving_name: gemini-2.0-flash
        base_url: https://generativelanguage.googleapis.com/v1beta/openai/
        api_key: YOUR_GOOGLE_GEMINI_API_KEY
        completion_params:
            temperature: 0.5
            max_tokens: 8000

# Optional: Custom prompt templates
prompts:
  system_prompt_template: |
    ### Task:
    Respond to the user query using the provided context.

    ### Guidelines:
    - If you don't know the answer, clearly state that.
    - Respond in the same language as the user's query.

    ### Output:
    Provide a clear and direct response.

    <context>
    {doc_context}
    </context>

  user_prompt_template: |
    <user_query>
    {user_query}
    </user_query>

# Optional: Document processing settings
documents:
  upload_dir: uploads
  max_file_size: 52428800  # 50MB
  allowed_extensions: [".pdf"]
  chunk_size: 10000
  chunk_overlap: 200
```

**Note**:
- For detailed configuration examples, see [env.example.yaml](src/api/env.example.yaml)
- Remote models are ready immediately, local models require starting the server
- Extended timeout (900s) recommended for reasoning models like GPT-OSS-20B

## 🛠️ Development

### Project Structure
```
src/
├── api/              # FastAPI backend
│   ├── main.py       # Main application
│   ├── config.py     # Configuration
│   ├── models.py     # Data models
│   ├── routers/      # API routes
│   │   ├── document.py    # Document management
│   │   ├── session.py     # Chat sessions
│   │   ├── model.py       # Model management
│   │   └── logs.py        # Log management
│   └── services/     # Business logic
│       ├── document_manager.py  # Document storage
│       ├── session_service.py   # Session management
│       ├── llm_service.py       # LLM integration
│       └── model.py             # Model server management
└── web/              # Gradio frontend
    └── app.py        # Gradio interface
```

### Available Commands
```bash
make start          # Start both frontend and backend
make stop           # Stop all services
make install        # Install dependencies
make test           # Health check
make clean          # Clean logs and uploads
```

## 🔗 API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload document
- `POST /api/v1/documents/upload_and_cache` - Upload and cache document
- `GET /api/v1/documents/list` - List all documents
- `DELETE /api/v1/documents/{doc_id}` - Delete document
- `POST /api/v1/documents/cache/{doc_id}` - Cache existing document

### Chat Sessions
- `GET /api/v1/session/{session_id}` - Get session info
- `POST /api/v1/session/{session_id}/messages/stream` - Send message (streaming)
- `GET /api/v1/session/{session_id}/messages` - Get chat history
- `DELETE /api/v1/session/{session_id}` - Delete session

### Model Management
- `GET /api/v1/model/list` - List all models (local and remote) with type information
- `POST /api/v1/model/switch` - Switch to a different model
- `POST /api/v1/model/up/reset` - Start local model with reset
- `POST /api/v1/model/up/without_reset` - Start local model without reset
- `POST /api/v1/model/down` - Stop local model
- `GET /api/v1/model/status` - Get current model status

## 🚨 Troubleshooting

### Common Issues
1. **Port already in use**: `make stop` or `npm run stop`
2. **Dependencies not installed**: `make install` or `npm run install-deps`
3. **Permission errors on Windows**: Run as Administrator or use WSL

### Health Check
```bash
make test
# or
npm test
```

## 🏗️ Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- Pydantic - Data validation and serialization
- Uvicorn - ASGI server
- httpx - Async HTTP client for full API parameter support
- PyYAML - YAML configuration parsing

**Frontend:**
- Gradio - ML/AI web interface framework
- httpx - HTTP client for API communication

**Development:**
- uv - Fast Python package manager
- Make - Cross-platform build automation
- npm - Node.js package management

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Need help?** Check out our detailed documentation:
- **[quick_start.md](docs/quick_start_guide.md)** - Usage guide and workflows
- **[arch.md](docs/arch.md)** - System architecture overview
- **[quick_start_for_model.md](docs/quick_start_for_model.md)** - Local and remote models configuration
- **[doc_and_rag.md](docs/doc_and_rag.md)** - Document processing and RAG implementation
