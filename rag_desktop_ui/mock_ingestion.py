"""
Mock ingestion client for testing UI without heavy dependencies
"""
import os
import json
import time

class MockIngestionClient:
    """Mock client that simulates ingestion without actual ML processing"""
    
    def __init__(self, **kwargs):
        self.collection_count = 0
        
    def upload_file(self, file_path):
        """Mock file upload that just simulates processing"""
        filename = os.path.basename(file_path)
        # Simulate processing time
        time.sleep(0.5)
        
        # Mock response
        chunks = 5  # Pretend we created 5 chunks
        self.collection_count += chunks
        
        return {
            "message": f"Successfully ingested {filename}",
            "chunks_processed": chunks,
            "total_items_in_collection": self.collection_count,
            "files_processed": [filename]
        }
    
    def search(self, query_text, n_results=10, where=None):
        """Mock search that returns fake results"""
        # Simulate search time
        time.sleep(0.2)
        
        # Mock search results
        mock_results = [
            f"This is a mock search result for '{query_text}'. In a real implementation, this would be relevant content from your uploaded documents.",
            f"Another mock result showing how the system would find information related to '{query_text}' in your knowledge base.",
        ]
        
        return {
            "ids": [["result_1", "result_2"]],
            "distances": [[0.1, 0.2]],
            "documents": [mock_results],
            "metadatas": [[{"type": "text", "source": "mock_doc.txt"}, {"type": "text", "source": "mock_doc2.txt"}]]
        }
    
    def get_collection_info(self):
        """Mock collection info"""
        return {
            "name": "mock_collection",
            "count": self.collection_count,
            "metadata": {"mock": True}
        }
    
    def get_collection_count(self):
        """Mock collection count"""
        return self.collection_count

def create_mock_client(**kwargs):
    """Create a mock ingestion client"""
    return MockIngestionClient(**kwargs)