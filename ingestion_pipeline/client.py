"""
Direct client for ingestion pipeline functionality
Provides Python functions to interact with the pipeline without API calls
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from ingest import IngestionPipeline
from logger_config import setup_logger

logger = setup_logger(__name__)


class IngestionClient:
    """
    Client for direct access to ingestion pipeline functionality.
    Provides the same functionality as the API endpoints but as direct Python calls.
    """
    
    def __init__(
        self,
        db_path: str = "chroma_local_db",
        text_model: str = "BAAI/bge-base-en",
        image_model: str = "google/siglip-base-patch16-224",
        offline_mode: bool = True
    ):
        """
        Initialize the ingestion client.
        
        Args:
            db_path: Path to ChromaDB storage directory
            text_model: SentenceTransformer model name for text embeddings
            image_model: HuggingFace model name for image embeddings
            offline_mode: If True, only use cached models (no downloads)
        """
        logger.info("Initializing IngestionClient...")
        self.pipeline = IngestionPipeline(
            db_path=db_path,
            text_model=text_model,
            image_model=image_model,
            offline_mode=offline_mode
        )
        logger.info("✓ IngestionClient initialized")
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload and ingest a single file (PDF, DOCX, image, or audio).
        
        Args:
            file_path: Path to file to upload and ingest
            
        Returns:
            Dictionary with:
                - message: Success message
                - chunks_processed: Number of chunks created
                - total_items_in_collection: Total items in collection after ingestion
                - files_processed: List of processed filenames
                
        Raises:
            ValueError: If file type is not supported
            RuntimeError: If processing fails
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = file_path.suffix.lower()
        if file_ext not in self.pipeline.supported_extensions:
            raise ValueError(
                f"Unsupported file type. Supported: {list(self.pipeline.supported_extensions.keys())}"
            )
        
        logger.info(f"Processing file: {file_path.name}")
        
        # Process the file
        ids, embeddings, documents, metadatas = self.pipeline.process_file(str(file_path))
        
        if not ids:
            raise RuntimeError(f"Failed to process file: {file_path.name}. No chunks extracted.")
        
        # Insert into ChromaDB
        self.pipeline.batch_insert(ids, embeddings, documents, metadatas)
        
        return {
            "message": f"Successfully ingested {file_path.name}",
            "chunks_processed": len(ids),
            "total_items_in_collection": self.pipeline.collection.count(),
            "files_processed": [file_path.name]
        }
    
    def ingest_directory(
        self,
        directory_path: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest all supported files from a directory.
        
        Args:
            directory_path: Path to directory containing files to ingest
            batch_size: Number of items to batch before inserting into ChromaDB
            
        Returns:
            Dictionary with:
                - message: Success message
                - chunks_processed: Number of chunks added
                - total_items_in_collection: Total items in collection after ingestion
                - files_processed: List of processed filenames
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Get count before ingestion
        count_before = self.pipeline.collection.count()
        
        # Process directory
        self.pipeline.ingest_directory(
            directory_path=directory_path,
            batch_size=batch_size
        )
        
        # Get count after ingestion
        count_after = self.pipeline.collection.count()
        chunks_added = count_after - count_before
        
        # Get list of processed files
        files_processed = []
        for ext in self.pipeline.supported_extensions.keys():
            files_processed.extend([f.name for f in directory.glob(f"*{ext}")])
            files_processed.extend([f.name for f in directory.glob(f"*{ext.upper()}")])
        
        return {
            "message": f"Successfully ingested directory: {directory_path}",
            "chunks_processed": chunks_added,
            "total_items_in_collection": count_after,
            "files_processed": files_processed
        }
    
    def search(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search the collection using a text query.
        
        Args:
            query_text: Text query to search for
            n_results: Number of results to return (default: 10)
            where: Optional metadata filter (e.g., {"type": "text"})
            
        Returns:
            Dictionary with:
                - ids: List of result IDs
                - distances: List of similarity distances
                - documents: List of document texts
                - metadatas: List of metadata dictionaries
        """
        # Generate query embedding
        query_embedding = self.pipeline.text_embedding_model.encode(query_text).tolist()
        
        # Build query parameters
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results
        }
        
        # Add metadata filter if provided and valid
        if where:
            # Clean and validate where clause - remove empty dicts and invalid entries
            cleaned_where = {}
            for key, value in where.items():
                # Skip empty dictionaries, None values, or empty strings
                if value is None:
                    continue
                if isinstance(value, dict):
                    # Skip empty dictionaries
                    if not value:
                        continue
                    cleaned_where[key] = value
                elif isinstance(value, (str, int, float, bool)):
                    # Direct equality filters
                    if value != "":
                        cleaned_where[key] = value
                else:
                    cleaned_where[key] = value
            
            # Only add where clause if it has valid filters
            if cleaned_where:
                query_kwargs["where"] = cleaned_where
                logger.debug(f"Search with where filter: {cleaned_where}")
        
        # Perform search
        results = self.pipeline.collection.query(**query_kwargs)
        
        return {
            "ids": results.get("ids", [[]]),
            "distances": results.get("distances", [[]]),
            "documents": results.get("documents", [[]]),
            "metadatas": results.get("metadatas", [[{}]])
        }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the ChromaDB collection.
        
        Returns:
            Dictionary with:
                - name: Collection name
                - count: Number of items in collection
                - metadata: Collection metadata (if any)
        """
        collection = self.pipeline.collection
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    
    def get_collection_count(self) -> int:
        """
        Get the total number of items in the collection.
        
        Returns:
            Number of items in collection
        """
        return self.pipeline.collection.count()
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """
        Get a specific item from the collection by ID.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Dictionary with:
                - id: Item ID
                - document: Document text (or "N/A" for images)
                - metadata: Item metadata
                
        Raises:
            ValueError: If item not found
        """
        results = self.pipeline.collection.get(ids=[item_id])
        if not results["ids"]:
            raise ValueError(f"Item {item_id} not found")
        
        return {
            "id": results["ids"][0],
            "document": results["documents"][0] if results["documents"] else None,
            "metadata": results["metadatas"][0] if results["metadatas"] else None
        }
    
    def delete_item(self, item_id: str) -> Dict[str, str]:
        """
        Delete a specific item from the collection by ID.
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            Dictionary with success message
        """
        self.pipeline.collection.delete(ids=[item_id])
        return {"message": f"Item {item_id} deleted successfully"}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the pipeline.
        
        Returns:
            Dictionary with:
                - status: "healthy" or "unhealthy"
                - collection_count: Number of items in collection
                - pipeline_initialized: True if pipeline is ready
        """
        try:
            count = self.pipeline.collection.count()
            return {
                "status": "healthy",
                "collection_count": count,
                "pipeline_initialized": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
                "pipeline_initialized": False
            }


# Convenience function for quick usage
def create_client(
    db_path: str = None,
    text_model: str = None,
    image_model: str = None,
    offline_mode: bool = True
) -> IngestionClient:
    """
    Create an IngestionClient with default or custom settings.
    
    Args:
        db_path: Path to ChromaDB (default: "chroma_local_db" or CHROMA_DB_PATH env var)
        text_model: Text embedding model (default: "BAAI/bge-base-en" or TEXT_MODEL env var)
        image_model: Image embedding model (default: "google/siglip-base-patch16-224" or IMAGE_MODEL env var)
        offline_mode: Offline mode flag (default: True or OFFLINE_MODE env var)
        
    Returns:
        Initialized IngestionClient instance
    """
    # Use environment variables if not provided
    if db_path is None:
        db_path = os.getenv("CHROMA_DB_PATH", "chroma_local_db")
    if text_model is None:
        text_model = os.getenv("TEXT_MODEL", "BAAI/bge-base-en")
    if image_model is None:
        image_model = os.getenv("IMAGE_MODEL", "google/siglip-base-patch16-224")
    if offline_mode:
        offline_mode = os.getenv("OFFLINE_MODE", "1").lower() in ("1", "true", "yes")
    
    return IngestionClient(
        db_path=db_path,
        text_model=text_model,
        image_model=image_model,
        offline_mode=offline_mode
    )


if __name__ == "__main__":
    """
    Example usage of the IngestionClient
    """
    # Initialize client
    client = create_client()
    
    # Health check
    health = client.health_check()
    print(f"Health: {health}")
    
    # Get collection info
    info = client.get_collection_info()
    print(f"Collection: {info['name']}, Count: {info['count']}")
    
    # Example: Upload a file
    # client.upload_file("path/to/document.pdf")
    
    # Example: Search
    # results = client.search("your query", n_results=10)
    # print(f"Found {len(results['ids'][0])} results")
    
    # Example: Ingest directory
    # result = client.ingest_directory("path/to/documents")
    # print(f"Processed {result['chunks_processed']} chunks")

