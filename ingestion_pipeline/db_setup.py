"""
ChromaDB Setup Script
Initializes a persistent ChromaDB client and creates/retrieves the multimodal collection.
"""
import chromadb
from pathlib import Path
import logging

from logger_config import setup_logger

logger = setup_logger(__name__)


def setup_chromadb(db_path: str = "chroma_local_db") -> tuple:
    """
    Initialize ChromaDB persistent client and get/create the collection.
    
    Args:
        db_path: Path to the ChromaDB storage directory
        
    Returns:
        tuple: (client, collection) ChromaDB client and collection objects
    """
    logger.info(f"Initializing ChromaDB at: {Path(db_path).absolute()}")
    
    # Initialize persistent client
    client = chromadb.PersistentClient(path=db_path)
    
    # Get or create the collection
    collection = client.get_or_create_collection(
        name="multimodal_collection"
    )
    
    logger.info("✓ ChromaDB initialized successfully")
    logger.info(f"✓ Collection 'multimodal_collection' ready (current count: {collection.count()})")
    
    return client, collection


if __name__ == "__main__":
    # Test the setup
    client, collection = setup_chromadb()
    print(f"\nCollection info: {collection.count()} items in collection")

