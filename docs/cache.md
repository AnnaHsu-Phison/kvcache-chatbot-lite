# Cache Model Validation

## Overview

All cache operations now validate that the LLM service configuration matches the currently running model server. This ensures cache operations use the correct model and parameters consistent with the chatbot's current model selection.

## Validation Mechanism

### What is Validated

1. **Model Server Status**: Checks if model server is running
2. **Model Name Match**: Verifies `llm_service.model` matches `model_server.config.alias`
3. **Configuration Logging**: Logs current model, base_url, and completion_params

### When Validation Occurs

Validation happens at the start of all cache operations:
- `POST /api/v1/documents/cache/{doc_id}` - Cache existing document
- `POST /api/v1/documents/upload_and_cache` - Upload and cache new document
- `POST /api/v1/documents/cache_group` - Cache single group
- `POST /api/v1/documents/cache_all_groups` - Cache all groups

## Error Handling

### Model Server Not Running

If model server is not running, returns HTTP 503:
```json
{
  "detail": "Model server is not running. Please start the model server first."
}
```

### Model Configuration Mismatch

If LLM service is configured for a different model than the running model server, returns HTTP 503:
```json
{
  "detail": "Model configuration mismatch. LLM service is configured for 'model-A' but model server is running 'model-B'. Please restart the model."
}
```

## Model Configuration Flow

### 1. Initial Startup
```
1. Backend starts
2. LLM service initialized with first model from env.yaml
3. Model server NOT running yet
```

### 2. User Starts Model
```
1. User selects model from dropdown (e.g., "Meta-Llama-3.1-8B-Instruct-Q4_K_M")
2. User clicks "Start with Reset" or "Start without Reset"
3. Backend:
   - Calls llm_service.reconfigure() with selected model config
   - Starts model_server with selected model
   - Both now use same model and parameters
```

### 3. Cache Operation
```
1. User uploads document and clicks "Cache"
2. Backend validates:
   - ✓ Model server is running
   - ✓ llm_service.model == model_server.config.alias
   - ✓ Completion params logged
3. Cache operation proceeds with validated configuration
```

## Logging

Cache operations now log:
```
Cache operation using model: Meta-Llama-3.1-8B-Instruct-Q4_K_M
Model base_url: http://localhost:8080/v1
Completion params: {'temperature': 0.7, 'max_tokens': 2048, ...}
```

This appears in:
- Backend terminal
- Model log files (`src/api/logs/model_*.log`)

## Benefits

1. **Consistency**: Cache always uses the same model as chat
2. **Error Prevention**: Catches mismatches before wasting compute
3. **Transparency**: Clear error messages guide users
4. **Debugging**: Logs show exact model/params used
5. **Reliability**: Prevents cache corruption from wrong model

## Example Scenarios

### ✅ Correct Flow
```
1. Start "Model-A" → llm_service reconfigured to Model-A
2. Upload + Cache doc → Validates Model-A, success
3. Chat with doc → Uses Model-A cache, fast!
```

### ❌ Error: Model Not Started
```
1. Backend starts (no model running)
2. Upload + Cache doc → Error: "Model server is not running"
3. User must start model first
```

### ❌ Error: Configuration Mismatch
```
1. Start "Model-A"
2. Manually edit config (rare edge case)
3. Cache doc → Error: "Model configuration mismatch"
4. Restart model to fix
```

## System Prompt Template Alignment

### Critical Fix: Prefix Matching Optimization

To ensure KV Cache prefix matching works correctly, the cache operation now formats document content using the same `system_prompt_template` as actual chat requests.

#### Before (Broken):
**Cache operation:**
```python
messages = [{"role": "system", "content": "raw document content..."}]
```

**Actual chat:**
```python
messages = [{"role": "system", "content": "### Task:\n...\n<context>\nraw document content...\n</context>"}]
```

❌ **Result**: Prefix mismatch → No KV Cache acceleration

#### After (Fixed):
**Both cache and chat now use:**
```python
formatted_content = settings.prompts.system_prompt_template.format(
    doc_context=content
)
messages = [{"role": "system", "content": formatted_content}]
```

✅ **Result**: Prefix match → Full KV Cache acceleration

### Benefits

1. **Cache Efficiency**: Prefix matching works as intended
2. **Performance**: Subsequent queries benefit from cached KV states
3. **Consistency**: Cache and chat use identical message formatting
4. **Correctness**: System prompt instructions are included in cache

## Code Changes

Modified files:
- `src/api/routers/document.py`:
  - `_cache_content_in_kv()` - **Added system_prompt_template formatting** (Critical fix)
  - `cache_document()` - Added model validation
  - `upload_document_and_cache()` - Added model validation
  - `cache_single_group()` - Added model validation
  - `cache_all_document_groups()` - Added model validation

All cache functions now:
1. Check `model_server._is_running()`
2. Compare `llm_service.get_current_config()['model']` vs `model_server.config.alias`
3. **Format content using `system_prompt_template` for prefix matching**
4. Log model configuration details
5. Raise HTTP 503 if mismatch

## Future Enhancements

Potential improvements:
- Add model version validation
- Support multi-model caching
- Cache persistence across restarts
- Model-specific cache namespaces

