# Local and Remote Models Support

This document explains the new local/remote model architecture and how to use it.

## Overview

The system now supports two types of models:

1. **Local Models**: Self-hosted models running on the local machine (e.g., llama-server)
2. **Remote Models**: External models accessed via API (e.g., OpenAI, Google Gemini, other computers)

## Configuration

### YAML Structure

```yaml
models:
  local_models:
    - model_name_or_path: C:\path\to\model.gguf
      serving_name: my-local-model
      tokenizer: meta-llama/Llama-3.1-8B-Instruct
      base_url: http://localhost:13141/v1
      api_key: not-needed
      completion_params:
        temperature: 0.0
        max_tokens: 20000

  remote_models:
    # Google Gemini
    - provider: google
      model: gemini-2.0-flash-exp
      serving_name: gemini-2.0-flash
      tokenizer: null
      base_url: https://generativelanguage.googleapis.com/v1beta/openai/
      api_key: your-google-api-key
      completion_params:
        temperature: 0.5
        max_tokens: 8000

    # OpenAI
    - provider: openai
      model: gpt-4o-mini
      serving_name: gpt-4o-mini
      base_url: https://api.openai.com/v1
      api_key: your-openai-api-key

    # Other computer (local remote)
    - provider: local_remote
      model: llama-3.1-8b
      serving_name: remote-llama-3.1-8b
      base_url: http://192.168.1.100:13141/v1
      api_key: not-needed
```

## Key Differences

### Local Models

- **Startup Required**: Must click "Start with Reset" or "Start without Reset" before use
- **KV Cache**: Supports KV cache for document caching
- **Cache Operation**: Actually caches documents in local KV memory for prefix matching acceleration
- **Stop Operation**: Can be stopped to free resources

### Remote Models

- **Ready Immediately**: No startup required, ready to use immediately after selection
- **No Local KV Cache**: Does not use local KV cache
- **Cache Operation**: Actually calls remote model API with document content (no local KV cache effect, but content is processed by remote model)
- **Stop Operation**: Returns info message (cannot stop remote services)

## API Endpoints

### List Models

```http
GET /api/v1/model/list
```

Returns all models (both local and remote) with their type and provider information.

### Switch Model

```http
POST /api/v1/model/switch
{
  "serving_name": "model-name"
}
```

Switch to a different model. For remote models, ready to use immediately. For local models, still need to start.

### Start Model (Local Only)

```http
POST /api/v1/model/up/without_reset
POST /api/v1/model/up/reset
{
  "serving_name": "model-name"
}
```

For local models only. Remote models will return an info message.

### Stop Model (Local Only)

```http
POST /api/v1/model/down
```

For local models only. Remote models will return an info message.

### Cache Document

```http
POST /api/v1/documents/cache/{doc_id}
```

- **Local models**: Actually caches document in KV memory for prefix matching acceleration
- **Remote models**: Actually calls remote model API with document content (no local KV cache, but content is sent to remote model)

## Usage Workflow

### Using Local Models

1. Select model from dropdown
2. Click "Start with Reset" or "Start without Reset"
3. Wait for model to load
4. Upload and cache documents (actual KV caching for prefix matching)
5. Chat with documents (with prefix matching acceleration)
6. Stop model when done

### Using Remote Models

1. Select model from dropdown
2. **No need to start** - ready immediately
3. Upload and cache documents (sends content to remote API for processing)
4. Chat with documents (uses remote API)
5. No need to stop - always available

## Frontend Integration

The frontend should:

1. **Model Selection**: Show both local and remote models in dropdown with type indicator
2. **Start/Stop Buttons**: Disable for remote models or show info message
3. **Chat**: Works immediately for remote models, requires start for local models
4. **Cache**: Works for both types (local: KV cache, remote: sends to remote API)

## Code Examples

### Check Model Type

```python
from config import settings

model = settings.get_model_by_serving_name("my-model")
if model.model_type == "remote":
    # Remote model - ready to use
    print(f"Remote model ({model.provider})")
else:
    # Local model - needs to be started
    print("Local model - please start")
```

### Switching Models

```python
# Frontend calls /api/v1/model/switch
# Backend reconfigures LLM service
# For remote: ready immediately
# For local: need to start separately
```
