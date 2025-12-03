# Document Processing and RAG System

## Overview

The chatbot implements a comprehensive document processing and RAG (Retrieval-Augmented Generation) system that handles document ingestion, intelligent chunking, grouping, and similarity-based retrieval. The system supports both English and Chinese (Traditional/Simplified) documents and queries.

## Document Processing System

### Architecture

The document processing system consists of several key components:

1. **Document Service** (`services/document_service.py`)
   - Multi-format document processing (currently PDF)
   - Intelligent text chunking with overlap
   - Token counting and budget management
   - Two-stage grouping system

2. **Document Manager** (`services/document_manager.py`)
   - Document metadata management
   - Chunk storage and retrieval
   - Document lifecycle management

3. **Tokenizer Manager** (`services/tokenizer_manager.py`)
   - HuggingFace tokenizer integration
   - Token counting for various models
   - Dynamic tokenizer loading

### Document Processing Pipeline

#### 1. Document Upload and Validation
- File type validation (currently supports PDF)
- File size and security checks
- Unique document ID generation

#### 2. Text Extraction
- **PDF Processing**: Uses `pypdf` for text extraction
- **Page-by-page extraction**: Maintains page number information
- **Full text assembly**: Combines all pages into searchable text

#### 3. Text Chunking
- **Recursive Character Text Splitter**: Uses LangChain's `RecursiveCharacterTextSplitter`
- **Intelligent separators**: `["\n\n", "\n", " ", ""]` for natural breaks
- **Configurable parameters**:
  - `chunk_size`: Maximum characters per chunk (default: 1000)
  - `chunk_overlap`: Overlap between chunks (default: 200)

#### 4. Chunk Metadata
Each chunk includes:
```python
@dataclass
class DocumentChunk:
    chunk_id: int
    content: str
    page_numbers: List[int]
    char_count: int
    token_count: Optional[int]
    source_file: Optional[str]
    chunk_index: Optional[int]
    group_id: Optional[str]
    start_page: Optional[int]
    end_page: Optional[int]
    page_key: Optional[str]
```

#### 5. Two-Stage Grouping System

##### Stage 1: Token-Based Grouping
- **Purpose**: Group chunks based on token budget constraints
- **Parameters**:
  - `file_max_tokens`: Maximum tokens per group (default: 13,000)
  - `utilization_threshold`: Minimum utilization for final group (default: 0.8)
- **Algorithm**: Sequential grouping with token budget management
- **Result**: Creates `MergedGroup` objects with merged content

##### Stage 2: Similarity-Based Grouping
- **Purpose**: Group remaining ungrouped chunks by similarity
- **Method**: BM25-based similarity scoring
- **Parameters**: Configurable similarity threshold
- **Result**: Additional groups for better retrieval

### Document Service Configuration

```python
class DocumentService:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        tokenizer: Optional[str] = None,
        grouping: bool = True,
        file_max_tokens: int = 13000,
        utilization_threshold: float = 0.8
    ):
```

### Supported File Types

Currently supported:
- **PDF** (`.pdf`): Full text extraction with page tracking

Extensible architecture allows easy addition of:
- Word documents (`.docx`)
- Plain text (`.txt`)
- Markdown (`.md`)
- HTML (`.html`)

### Token Counting

The system supports token counting using HuggingFace tokenizers:
- **Dynamic loading**: Loads tokenizers on demand
- **Model-specific**: Supports various model tokenizers
- **Accurate counting**: Provides precise token counts for budget management

## RAG (Retrieval-Augmented Generation) System

### Architecture

The RAG system builds upon the document processing pipeline to provide intelligent document retrieval:

1. **Tokenizer Service** (`services/tokenizer.py`)
   - Chinese word segmentation using jieba
   - Traditional/Simplified Chinese conversion using opencc
   - Optional stopword filtering
   - Mixed language support

2. **RAG Service** (`services/rag_service.py`)
   - BM25-based document retrieval
   - Group-based similarity matching
   - Configurable tokenization options
   - Detailed logging for debugging

### Tokenization System

#### Features

##### 1. Chinese Word Segmentation
- Uses **jieba** for intelligent Chinese word segmentation
- Handles mixed English and Chinese text
- Example: `"這個論文的Abstract說了什麼"` → `['這個', '論文', '的', 'abstract', '說', '了', '什麼']`

##### 2. Traditional/Simplified Conversion
- Uses **opencc** for Traditional/Simplified Chinese conversion
- **Default**: Normalizes all Chinese text to Traditional Chinese (繁體中文)
- Ensures consistent matching between queries and documents

##### 3. Optional Stopword Filtering
- Supports removing common stopwords (的、了、是、the、a、etc.)
- Disabled by default to preserve query intent
- Can be enabled when needed

#### Dependencies

```txt
jieba>=0.42.1
opencc-python-reimplemented>=0.1.7
setuptools>=80.9.0
```

Install with:
```bash
uv pip install setuptools
uv pip install --no-build-isolation jieba opencc-python-reimplemented
```

#### Usage

##### Basic Tokenization

```python
from services.tokenizer import get_tokenizer

# Default tokenizer (Traditional Chinese, no stopword filtering)
tokenizer = get_tokenizer(filter_stopwords=False)
tokens = tokenizer.tokenize("這個論文的Abstract說了什麼")
# Result: ['這個', '論文', '的', 'abstract', '說', '了', '什麼']
```

##### With Stopword Filtering

```python
tokenizer = get_tokenizer(filter_stopwords=True)
tokens = tokenizer.tokenize("這個論文的Abstract說了什麼")
# Result: ['論文', 'abstract']  # Stopwords removed
```

### RAG Service

#### Features

- **BM25 Retrieval**: Uses BM25 algorithm for similarity-based document retrieval
- **Group-based Matching**: Retrieves document groups rather than individual chunks
- **Configurable Tokenization**: Supports different tokenization modes
- **Mixed Language Support**: Handles English and Chinese queries effectively
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

#### Usage

##### Basic RAG Service

```python
from services.rag_service import RAGService

# Without stopword filtering (default)
rag_service = RAGService(filter_stopwords=False)

# With stopword filtering
rag_service = RAGService(filter_stopwords=True)
```

##### Document Retrieval

```python
# Sample document groups
groups = [
    {
        "group_id": "group1",
        "merged_content": "AIBrix: Towards Scalable, Cost-Effective Large Language Model Inference Infrastructure. Abstract. We introduce AIBrix...",
        "chunk_ids": [1, 2, 3],
        "total_tokens": 150
    },
    # ... more groups
]

# Retrieve most similar groups
query = "這個論文的Abstract說了什麼"
results = rag_service.retrieve_most_similar_group(
    query=query,
    groups=groups,
    top_k=3,
    document_name="2504.03648v1.pdf"
)

for result in results:
    print(f"Group ID: {result.group_id}")
    print(f"Similarity Score: {result.similarity_score:.4f}")
    print(f"Content: {result.content[:100]}...")
```

### RAG Logging System

The RAG service provides comprehensive logging for debugging and monitoring:

#### Log Information
- **Document Information**: Current document being searched
- **Query Details**: User query and tokenization results
- **Group Analysis**: Each group's ID, chunk IDs, token count, BM25 score
- **Content Preview**: First 100 characters of each group's content
- **Final Ranking**: Sorted results by BM25 score
- **Retrieval Summary**: Final results and scores

#### Log Format
```
2025-10-20 14:23:40,843 - services.rag_service - INFO - RAG: Starting retrieval for document '2504.03648v1.pdf'
2025-10-20 14:23:40,843 - services.rag_service - INFO - RAG: Query: '這個論文的Abstract說了什麼'
2025-10-20 14:23:40,843 - services.rag_service - INFO - RAG: Available groups: 3
2025-10-20 14:23:40,845 - services.rag_service - INFO - RAG: Query tokens (7): ['這個', '論文', '的', 'abstract', '說', '了', '什麼']
```

## Why This Matters

### Document Processing Benefits

1. **Intelligent Chunking**: Preserves semantic meaning while respecting token limits
2. **Two-Stage Grouping**: Optimizes both token efficiency and semantic similarity
3. **Page Tracking**: Maintains source page information for citations
4. **Token Budget Management**: Ensures groups fit within model context limits

### RAG System Benefits

#### Before (Simple Character Splitting)
- Query: `"這個論文的Abstract說了什麼"`
- Tokens: `['這', '個', '論', '文', '的', 'a', 'b', 's', 't', 'r', 'a', 'c', 't', '說', '了', '什', '麼']`
- Problem: Cannot match "Abstract" because it's split by character

#### After (Intelligent Segmentation)
- Query: `"這個論文的Abstract說了什麼"`
- Tokens: `['這個', '論文', '的', 'abstract', '說', '了', '什麼']`
- Success: "abstract" is preserved as a complete word and can match documents

## Configuration

### Document Service Configuration

The document service is configured to:
1. **Chunk Size**: 1000 characters per chunk (configurable)
2. **Chunk Overlap**: 200 characters overlap (configurable)
3. **Token Budget**: 13,000 tokens per group (configurable)
4. **Grouping**: Two-stage grouping enabled by default

### Tokenizer Configuration

The tokenizer is configured to:
1. **Normalize to Traditional Chinese**: All Chinese text is converted to Traditional Chinese for consistent matching
2. **Preserve English words**: English words are kept intact (lowercased)
3. **Handle mixed content**: Seamlessly processes documents and queries with mixed languages

### RAG Service Configuration

- **BM25 Parameters**: k1=1.5, b=0.75 (standard values)
- **Default Behavior**: No stopword filtering (preserves query intent)
- **Group Retrieval**: Returns document groups with similarity scores
- **Logging**: Comprehensive logging enabled by default

## Performance Impact

### Document Processing
- **Chunking Speed**: ~100-500 chunks per second (depending on document size)
- **Grouping Speed**: ~50-200 groups per second (depending on tokenizer)
- **Memory Usage**: Moderate (chunks stored in memory during processing)

### RAG System
- **BM25 Matching Accuracy**: Significantly improved for mixed-language queries
- **Query Understanding**: Better semantic matching between query intent and document content
- **Initialization Time**: First query takes ~0.4s to load jieba dictionary (cached afterward)
- **Retrieval Speed**: ~10-50ms per query (depending on number of groups)

## API Reference

### DocumentService Class

```python
class DocumentService:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        tokenizer: Optional[str] = None,
        grouping: bool = True,
        file_max_tokens: int = 13000,
        utilization_threshold: float = 0.8
    )
    async def process_document(self, file_path: Path) -> ProcessedDocument
```

### DocumentChunk Class

```python
@dataclass
class DocumentChunk:
    chunk_id: int
    content: str
    page_numbers: List[int]
    char_count: int
    token_count: Optional[int]
    source_file: Optional[str]
    chunk_index: Optional[int]
    group_id: Optional[str]
    start_page: Optional[int]
    end_page: Optional[int]
    page_key: Optional[str]
```

### Tokenizer Class

```python
class Tokenizer:
    def __init__(self, filter_stopwords: bool = False, normalize_to_traditional: bool = True)
    def tokenize(self, text: str) -> List[str]
```

### RAGService Class

```python
class RAGService:
    def __init__(self, filter_stopwords: bool = False)
    def retrieve_most_similar_group(
        self,
        query: str,
        groups: List[Dict],
        top_k: int = 1,
        document_name: str = "Unknown"
    ) -> List[RetrievalResult]
```

### RetrievalResult Class

```python
@dataclass
class RetrievalResult:
    group_id: str
    content: str
    similarity_score: float
    chunk_ids: List[int]
    total_tokens: int
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'jieba'**
   - Solution: Install dependencies with `uv pip install --no-build-isolation jieba opencc-python-reimplemented`

2. **UnicodeEncodeError in Windows terminal**
   - This is a display issue only, the tokenization still works correctly
   - The actual tokens are processed correctly by the system

3. **Poor retrieval results for mixed language queries**
   - Ensure jieba and opencc are properly installed
   - Check that documents are properly tokenized during indexing

4. **Document processing fails**
   - Check file format is supported (currently PDF only)
   - Verify file is not corrupted
   - Check file size limits

5. **Grouping produces too many small groups**
   - Adjust `file_max_tokens` parameter
   - Modify `utilization_threshold` for better grouping
   - Check tokenizer is properly configured

## References

- [jieba - Chinese word segmentation](https://github.com/fxsjy/jieba)
- [OpenCC - Chinese conversion](https://github.com/BYVoid/OpenCC)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [HuggingFace Tokenizers](https://huggingface.co/docs/tokenizers/index)
