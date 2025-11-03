ChromaDB Data Structure Agreement
The Ingestion (Person 1) and Retrieval (Person 2) teams must agree on the exact data structure for the ChromaDB collection. Chroma's structure is defined by the data you add (ids, embeddings, documents, and metadatas).

Proposed Structure:

Collection Name: multimodal_collection (Agreed-upon name)

ids: Primary Key (String, must be unique, user-provided, e.g., "report.pdf_chunk_1")

embeddings: Float Vector (Dimension: 512 for clip-ViT-B-32)

documents: String (The text chunk or transcript. For images, "N/A" or the source filename can be used.)

metadatas: JSON (This will store all queryable attributes other than the vector.)

source_file: String (e.g., "report.pdf")

type: String (e.g., "text", "image", "audio")

...any other custom fields (e.g., {"page": 3} or {"timestamp": "00:32:15"})

Person 1: Ingestion Pipeline Specialist
Goal: Process all incoming files (PDF, DOCX, images, audio) and load them into a persistent ChromaDB vector database.

Setup ChromaDB
Write a script db_setup.py.

Import chromadb.

Initialize a persistent client: client = chromadb.PersistentClient(path="chroma_local_db") (This creates a local DB directory).

Get or create the collection: collection = client.get_or_create_collection(name="multimodal_collection").

(Note: No manual schema definition or index creation is required. Chroma manages indexing automatically using HNSW.)

Load Models
Load the SentenceTransformer('clip-ViT-B-32') model for text/image encoding.

Load the whisper.load_model('base.en') model for audio transcription.

Build File Parsers (parsers.py)
PDF/DOCX Parser:

Use PyMuPDF (for PDF) and python-docx (for DOCX) to extract raw text.

Implement a text chunker (e.g., RecursiveCharacterTextSplitter from LangChain or a simple paragraph-based splitter).

Audio Parser:

Use whisper.transcribe() to get the full transcript with timestamps.

Chunk the transcript into smaller segments (e.g., 10-second intervals or by sentence) and store the timestamps.

Image Parser:

Use Pillow (PIL) to open and pre-process images.

Build Ingestion Logic (ingest.py)
Create a "main" script that can be pointed at a directory.

Prepare lists for batch insertion: ids_batch, embeddings_batch, documents_batch, metadatas_batch.

For each file:

If PDF/DOCX:

Parse & chunk text.

For each chunk:

vector = clip_model.encode(text_chunk)

Prepare data:

id: Generate a unique string (e.g., f"{filename}_chunk_{i}")

embedding: vector

document: text_chunk

metadata: {"source_file": ..., "type": "text", "page": ...}

If Audio:

Transcribe & chunk transcript.

For each chunk:

vector = clip_model.encode(transcript_chunk)

Prepare data:

id: Generate a unique string (e.g., f"{filename}_segment_{i}")

embedding: vector

document: transcript_chunk

metadata: {"source_file": ..., "type": "audio", "start": ..., "end": ...}

If Image:

Load image with Pillow.

vector = clip_model.encode(image)

Prepare data:

id: Generate a unique string (e.g., f"{filename}_image")

embedding: vector

document: "N/A" (or filename)

metadata: {"source_file": ..., "type": "image", "timestamp": ...}

Add each item's data to the corresponding batch lists.

Batch insert the prepared data into Chroma: collection.upsert(ids=ids_batch, embeddings=embeddings_batch, documents=documents_batch, metadatas=metadatas_batch).

Deliverable
A script (ingest.py) that populates a chroma_local_db directory.

---

## Offline Operation

This pipeline is designed to work **completely offline** after initial setup. All models are cached locally and ChromaDB uses persistent local storage.

### Initial Setup (One-time, requires internet)

Before running the pipeline offline, download all required models:

```bash
# Download all models to local cache
python ingestion_pipeline/setup_offline.py
```

This script downloads:
- SentenceTransformer model (`clip-ViT-B-32`) → cached in `~/.cache/huggingface/`
- Whisper model (`base.en`) → cached in `~/.cache/whisper/`

### Offline Mode

By default, the pipeline runs in **offline mode** and will:
- ✅ Use local model cache only (no downloads)
- ✅ Use local ChromaDB storage (`chroma_local_db/`)
- ✅ Work without internet connection
- ❌ Fail if models are not in cache (use `setup_offline.py` first)

### Configuration

- **Offline Mode** (default): Set `OFFLINE_MODE=1` or leave unset
  - Only uses cached models
  - Fails gracefully if models not found
  
- **Online Mode**: Set `OFFLINE_MODE=0`
  - Will download models if not in cache
  - Requires internet connection

```bash
# Force offline mode (default)
export OFFLINE_MODE=1
python ingestion_pipeline/ingest.py /path/to/files

# Allow online downloads
export OFFLINE_MODE=0
python ingestion_pipeline/ingest.py /path/to/files
```

### Model Cache Locations

- **SentenceTransformer models**: `~/.cache/huggingface/hub/`
- **Whisper models**: `~/.cache/whisper/`
- **ChromaDB data**: `chroma_local_db/` (configurable via `CHROMA_DB_PATH`)

### Verification

To verify all models are cached and ready for offline use:

```bash
# Check SentenceTransformer cache
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32')"
# Should load without errors

# Check Whisper cache
python -c "import whisper; whisper.load_model('base.en')"
# Should load without errors
```

---

## FastAPI Web API

A REST API is available to interact with the ingestion pipeline programmatically.

### Starting the API Server

```bash
# Option 1: Using the run script
python ingestion_pipeline/run_api.py

# Option 2: Using uvicorn directly
uvicorn ingestion_pipeline.app:app --reload --port 8000

# Option 3: Using the app directly
python ingestion_pipeline/app.py
```

The API will be available at `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Environment Variables

- `CHROMA_DB_PATH`: Path to ChromaDB storage (default: `chroma_local_db`)
- `EMBEDDING_MODEL`: SentenceTransformer model name (default: `clip-ViT-B-32`)
- `PORT`: Server port (default: `8000`)
- `HOST`: Server host (default: `0.0.0.0`)

### API Endpoints

#### 1. **POST /upload** - Upload and ingest a single file
Upload a PDF, DOCX, image, or audio file for ingestion.

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "message": "Successfully ingested document.pdf",
  "chunks_processed": 15,
  "total_items_in_collection": 125,
  "files_processed": ["document.pdf"]
}
```

#### 2. **POST /ingest-directory** - Ingest all files from a directory
Process all supported files in a directory.

```bash
curl -X POST "http://localhost:8000/ingest-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/documents",
    "batch_size": 100
  }'
```

#### 3. **POST /search** - Search the collection
Search for similar content using semantic similarity.

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "machine learning",
    "n_results": 10,
    "where": {"type": "text"}
  }'
```

#### 4. **GET /search** - Search with query parameters (convenience endpoint)
```bash
curl "http://localhost:8000/search?query=machine%20learning&n_results=10&file_type=text"
```

#### 5. **GET /collection/info** - Get collection information
```bash
curl "http://localhost:8000/collection/info"
```

**Response:**
```json
{
  "name": "multimodal_collection",
  "count": 150,
  "metadata": null
}
```

#### 6. **GET /collection/count** - Get item count
```bash
curl "http://localhost:8000/collection/count"
```

#### 7. **GET /collection/items/{item_id}** - Get a specific item
```bash
curl "http://localhost:8000/collection/items/document.pdf_chunk_1"
```

#### 8. **DELETE /collection/items/{item_id}** - Delete an item
```bash
curl -X DELETE "http://localhost:8000/collection/items/document.pdf_chunk_1"
```

#### 9. **GET /health** - Health check
```bash
curl "http://localhost:8000/health"
```

#### 10. **GET /** - API information
```bash
curl "http://localhost:8000/"
```

### Python Client Example

```python
import requests

# Upload a file
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    print(response.json())

# Search the collection
response = requests.post(
    "http://localhost:8000/search",
    json={
        "query_text": "artificial intelligence",
        "n_results": 5,
        "where": {"type": "text"}
    }
)
results = response.json()
print(f"Found {len(results['ids'][0])} results")
```

### Using with JavaScript/Fetch

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Search
fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query_text: 'machine learning',
    n_results: 10
  })
})
.then(response => response.json())
.then(results => console.log(results));
```