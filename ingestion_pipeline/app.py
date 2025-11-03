"""
FastAPI Application for Ingestion Pipeline
Provides REST API endpoints for file ingestion and ChromaDB operations.
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import uvicorn
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ingest import IngestionPipeline
from db_setup import setup_chromadb
from logger_config import setup_logger

logger = setup_logger(__name__, log_file="ingestion_api.log")

# Initialize FastAPI app
app = FastAPI(
    title="RAG Ingestion Pipeline API",
    description="API for ingesting PDF, DOCX, images, and audio files into ChromaDB",
    version="1.0.0"
)

# Global pipeline instance (initialized on startup)
pipeline: Optional[IngestionPipeline] = None


# Pydantic models for request/response
class DirectoryIngestRequest(BaseModel):
    directory_path: str = Field(..., description="Path to directory containing files to ingest")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch size for insertion")


class SearchRequest(BaseModel):
    query_text: str = Field(..., description="Text query to search for")
    n_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    where: Optional[dict] = Field(default=None, description="Metadata filter (e.g., {'type': 'text'})")


class SearchResponse(BaseModel):
    ids: List[List[str]]
    distances: List[List[float]]
    documents: List[List[str]]
    metadatas: List[List[dict]]


class CollectionInfo(BaseModel):
    name: str
    count: int
    metadata: Optional[dict] = None


class IngestResponse(BaseModel):
    message: str
    chunks_processed: int
    total_items_in_collection: int
    files_processed: List[str]


@app.on_event("startup")
async def startup_event():
    """Initialize the ingestion pipeline on startup"""
    global pipeline
    db_path = os.getenv("CHROMA_DB_PATH", "chroma_local_db")
    text_model = os.getenv("TEXT_MODEL", "BAAI/bge-base-en")
    image_model = os.getenv("IMAGE_MODEL", "google/siglip-base-patch16-224")
    
    logger.info("Initializing ingestion pipeline...")
    logger.info(f"DB Path: {db_path}")
    logger.info(f"Text Model: {text_model}")
    logger.info(f"Image Model: {image_model}")
    
    # Use offline mode by default (set OFFLINE_MODE=0 to allow downloads)
    offline_mode = os.getenv("OFFLINE_MODE", "1").lower() in ("1", "true", "yes")
    logger.info(f"Offline mode: {offline_mode}")
    
    pipeline = IngestionPipeline(
        db_path=db_path,
        text_model=text_model,
        image_model=image_model,
        offline_mode=offline_mode
    )
    logger.info("✓ Pipeline initialized successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Ingestion Pipeline API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload - Upload and ingest a file",
            "ingest_directory": "POST /ingest-directory - Ingest files from a directory",
            "search": "POST /search - Search the collection",
            "collection_info": "GET /collection/info - Get collection information",
            "collection_count": "GET /collection/count - Get item count",
            "delete_item": "DELETE /collection/items/{item_id} - Delete an item",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if pipeline is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Pipeline not initialized"}
        )
    
    try:
        count = pipeline.collection.count()
        return {
            "status": "healthy",
            "collection_count": count,
            "pipeline_initialized": True
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
        )


@app.post("/upload", response_model=IngestResponse)
async def upload_file(
    file: UploadFile = File(..., description="File to upload and ingest")
):
    """
    Upload and ingest a single file (PDF, DOCX, image, or audio).
    
    Supported formats:
    - Documents: PDF, DOCX
    - Images: JPG, PNG, GIF, BMP, WEBP
    - Audio: MP3, WAV, M4A, FLAC
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in pipeline.supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {list(pipeline.supported_extensions.keys())}"
        )
    
    # Save uploaded file to temporary location
    tmp_file_path = None
    try:
        # Create temporary file and write content
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            # Copy file content
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        
        # File is now closed, safe to process
        # Process the file
        ids, embeddings, documents, metadatas = pipeline.process_file(tmp_file_path)
        
        if not ids:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process file: {file.filename}. No chunks extracted."
            )
        
        # Insert into ChromaDB
        pipeline.batch_insert(ids, embeddings, documents, metadatas)
        
        return IngestResponse(
            message=f"Successfully ingested {file.filename}",
            chunks_processed=len(ids),
            total_items_in_collection=pipeline.collection.count(),
            files_processed=[file.filename]
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file (ensure it's closed first)
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                # On Windows, sometimes need to wait a moment for file handles to release
                import time
                time.sleep(0.1)  # Small delay for Windows file handle release
                os.unlink(tmp_file_path)
                logger.debug(f"Temporary file deleted: {tmp_file_path}")
            except (PermissionError, OSError) as e:
                # If deletion fails, log but don't fail the request
                # On Windows, temporary files in %TEMP% are auto-cleaned by OS eventually
                logger.warning(f"Could not delete temporary file {tmp_file_path}: {e}")


@app.post("/ingest-directory", response_model=IngestResponse)
async def ingest_directory(request: DirectoryIngestRequest):
    """
    Ingest all supported files from a directory.
    
    The directory path should be accessible from the server.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    directory = Path(request.directory_path)
    if not directory.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory_path}")
    
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.directory_path}")
    
    try:
        # Get count before ingestion
        count_before = pipeline.collection.count()
        
        # Process directory
        pipeline.ingest_directory(
            directory_path=request.directory_path,
            batch_size=request.batch_size
        )
        
        # Get count after ingestion
        count_after = pipeline.collection.count()
        chunks_added = count_after - count_before
        
        # Get list of processed files
        files_processed = []
        for ext in pipeline.supported_extensions.keys():
            files_processed.extend([f.name for f in directory.glob(f"*{ext}")])
            files_processed.extend([f.name for f in directory.glob(f"*{ext.upper()}")])
        
        return IngestResponse(
            message=f"Successfully ingested directory: {request.directory_path}",
            chunks_processed=chunks_added,
            total_items_in_collection=count_after,
            files_processed=files_processed
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting directory: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_collection(request: SearchRequest):
    """
    Search the collection using a text query.
    
    Returns similar items based on semantic similarity.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # Generate query embedding using text model
        query_embedding = pipeline.text_embedding_model.encode(request.query_text).tolist()
        
        # Build query parameters
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": request.n_results
        }
        
        # Add metadata filter if provided and valid
        if request.where:
            # Clean and validate where clause - remove empty dicts and invalid entries
            cleaned_where = {}
            for key, value in request.where.items():
                # Skip empty dictionaries, None values, or empty strings
                if value is None:
                    continue
                if isinstance(value, dict):
                    # Skip empty dictionaries
                    if not value:
                        continue
                    # Validate nested structure for ChromaDB operators
                    cleaned_where[key] = value
                elif isinstance(value, (str, int, float, bool)):
                    # Direct equality filters (e.g., {"type": "text"})
                    if value != "":
                        cleaned_where[key] = value
                else:
                    # Include other valid types
                    cleaned_where[key] = value
            
            # Only add where clause if it has valid filters
            if cleaned_where:
                query_kwargs["where"] = cleaned_where
                logger.debug(f"Search with where filter: {cleaned_where}")
            else:
                logger.warning(f"Empty or invalid where clause provided, ignoring: {request.where}")
        
        # Perform search
        results = pipeline.collection.query(**query_kwargs)
        
        return SearchResponse(
            ids=results.get("ids", [[]]),
            distances=results.get("distances", [[]]),
            documents=results.get("documents", [[]]),
            metadatas=results.get("metadatas", [[{}]])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching collection: {str(e)}")


@app.get("/search", response_model=SearchResponse)
async def search_collection_get(
    query: str = Query(..., description="Text query to search for"),
    n_results: int = Query(default=10, ge=1, le=100, description="Number of results to return"),
    file_type: Optional[str] = Query(default=None, description="Filter by type (text, image, audio)"),
    source_file: Optional[str] = Query(default=None, description="Filter by source file name")
):
    """
    Search the collection using GET request (convenience endpoint).
    """
    # Build where clause if filters provided
    where_clause = None
    if file_type or source_file:
        where_clause = {}
        if file_type:
            where_clause["type"] = file_type
        if source_file:
            where_clause["source_file"] = source_file
    
    request = SearchRequest(query_text=query, n_results=n_results, where=where_clause)
    return await search_collection(request)


@app.get("/collection/info", response_model=CollectionInfo)
async def get_collection_info():
    """Get information about the ChromaDB collection"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        collection = pipeline.collection
        return CollectionInfo(
            name=collection.name,
            count=collection.count(),
            metadata=collection.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection info: {str(e)}")


@app.get("/collection/count")
async def get_collection_count():
    """Get the total number of items in the collection"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        count = pipeline.collection.count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection count: {str(e)}")


@app.delete("/collection/items/{item_id}")
async def delete_item(item_id: str):
    """Delete a specific item from the collection by ID"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        pipeline.collection.delete(ids=[item_id])
        return {"message": f"Item {item_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


@app.get("/collection/items/{item_id}")
async def get_item(item_id: str):
    """Get a specific item from the collection by ID"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        results = pipeline.collection.get(ids=[item_id])
        if not results["ids"]:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        return {
            "id": results["ids"][0],
            "document": results["documents"][0] if results["documents"] else None,
            "metadata": results["metadatas"][0] if results["metadatas"] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting item: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)

