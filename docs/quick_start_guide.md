# Quick Start Guide

## Overview

The KVCache Chatbot is a multi-turn conversation system with document upload support. Key features:

- 💬 **Multi-turn Conversations**: Maintains conversation history
- 📄 **Document Management**: Upload and select documents independently
- ⚡ **Streaming Responses**: Real-time chat experience
- 🚀 **KV Cache Integration**: Optimized document processing
- 🔧 **Model Management**: Start/stop local model servers

## Getting Started

### Step 1: Start the Application

**Option A: Using Make (Recommended)**
```bash
make start
```

**Option B: Using npm**
```bash
npm start
```

**Option C: Manual start**
```bash
# Terminal 1 - Backend
cd src/api && python main.py

# Terminal 2 - Frontend
cd src/web && python app.py --backend-port 8000
```

### Step 2: Access the Interface

Open your browser and navigate to: **http://localhost:7860**

### Step 2: Upload a Document

1. Look at the left sidebar "Document Management" section
2. Click on the file upload area under "Upload Document"
3. Select a `.txt` file
4. Click the "Upload" button
5. You'll see a success message with the filename and size

### Step 3: Select a Document

1. In the "Select Document" section below, you'll see a dropdown menu
2. Click the dropdown to see all uploaded documents
3. Select the document you want to use
4. If you upload more documents, click "Refresh List" to update the dropdown

### Step 4: Chat with Document Context

1. With a document selected in the dropdown
2. Type your message in the chat input box
3. Press Enter or click Send
4. The LLM will receive your message with the document content as context

### Step 5: Switch Documents

1. Simply select a different document from the dropdown
2. Your next message will use the newly selected document
3. Previous chat history remains in the session

### Step 6: Chat Without Documents

1. Select "No document selected" from the dropdown
2. Your messages will be sent without document context

## Example Workflow

### Basic Document Chat
```
1. Upload "product_manual.txt"
   ✅ Document 'product_manual.txt' uploaded successfully

2. Select "product_manual.txt" from dropdown

3. Ask: "What is the return policy?"
   → System: [product_manual.txt content]
   → User: "What is the return policy?"
   → Assistant: [response based on document]

4. Ask follow-up: "How long is the warranty?"
   → Conversation continues with document context
```

### Multi-Document Workflow
```
1. Upload "product_manual.txt" and "faq.txt"

2. Select "product_manual.txt"
   → Ask: "What are the main features?"

3. Switch to "faq.txt"
   → Ask: "How do I contact support?"

4. Switch back to "product_manual.txt"
   → Previous chat history is preserved
```

### KV Cache Optimization
```
1. Upload document with "Cache" button
   ✅ Document cached successfully. KV Cache ready for prefix matching.

2. Ask questions about the document
   → Faster responses due to pre-cached content

3. Upload another document with "Cache"
   → Both documents optimized for performance
```

## Tips

- **Multiple documents**: Upload as many documents as needed
- **Reusable**: Documents persist across sessions (until backend restarts)
- **Easy switching**: Change documents anytime via dropdown
- **No document mode**: Select "No document selected" for regular chat
- **KV Cache**: Use "Cache" button for faster document processing
- **Model management**: Start/stop model servers from the interface
- **Refresh**: Click "Refresh List" to update document dropdown

## Model Management

### Starting Model Server
1. Click "Restart Model" button in the left sidebar
2. Monitor status in "Model Status" section
3. Check deployment logs for any issues

### Model Server Modes
- **Without Reset**: Preserves existing configuration and cache
- **With Reset**: Clears cache and starts fresh (recommended for new documents)

### Stopping Model Server
1. Click "Stop Model" button
2. Model server shuts down gracefully
3. All cached documents are cleared

## Supported File Types

Currently supported:
- `.txt` (Plain text files)

Coming soon:
- `.pdf` (PDF documents)
- `.docx` (Word documents)
- `.md` (Markdown files)

## Troubleshooting

### Document not showing in dropdown
- Click the "Refresh List" button
- Check the upload status message for errors

### Upload fails
- Check file size (limit: see backend config)
- Ensure file type is `.txt`
- Make sure backend is running

### Chat not using document
- Verify a document is selected (not "No document selected")
- Check backend logs for errors

## API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload document
- `POST /api/v1/documents/upload_and_cache` - Upload and cache document
- `GET /api/v1/documents/list` - List all documents
- `GET /api/v1/documents/{doc_id}` - Get document info
- `DELETE /api/v1/documents/{doc_id}` - Delete document
- `POST /api/v1/documents/cache/{doc_id}` - Cache existing document

### Chat Sessions
- `GET /api/v1/session/{session_id}` - Get session info
- `DELETE /api/v1/session/{session_id}` - Delete session
- `GET /api/v1/session/{session_id}/messages` - Get chat history
- `POST /api/v1/session/{session_id}/messages` - Send message (non-streaming)
- `POST /api/v1/session/{session_id}/messages/stream` - Send message (streaming)

### Model Management
- `POST /api/v1/model/up/without_reset` - Start model without reset
- `POST /api/v1/model/up/reset` - Start model with reset
- `POST /api/v1/model/down` - Stop model
- `GET /api/v1/model/status` - Get model status

### Logs
- `GET /api/v1/logs/current` - Get current model logs
- `GET /api/v1/logs/recent` - Get recent logs
- `GET /api/v1/logs/sessions` - List log sessions

## Troubleshooting

### Document not showing in dropdown
- Click "Refresh List" button
- Check upload status for errors
- Verify file type is `.txt`

### Upload fails
- Check file size (limit: 10MB)
- Ensure file type is `.txt`
- Make sure backend is running

### Chat not using document
- Verify document is selected (not "No document selected")
- Check backend logs for errors
- Ensure model server is running

### Model server issues
- Check model configuration in `.env` file
- Verify model server executable path
- Check deployment logs for error messages
- Try restarting with "Reset" mode

## Next Steps

- See [GETTING_STARTED.md](GETTING_STARTED.md) for installation instructions
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture overview
- Check the API documentation at http://localhost:8000/docs
- Explore the test documents in `testcases/docs/` directory

