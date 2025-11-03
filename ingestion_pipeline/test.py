import chromadb
from chromadb.utils import embedding_functions

# Use local persistent storage (offline)
client = chromadb.PersistentClient(path="./chroma_db")

# Optional: define an embedding model
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Create or get a collection
collection = client.get_or_create_collection(
    name="research_papers",
    embedding_function=embedding_function
)

# Add sample data
documents = [
    "Milvus Lite runs embedded without external server.",
    "ChromaDB supports offline persistent vector storage.",
    "Qdrant and Weaviate are great for hybrid vector search."
]
ids = ["1", "2", "3"]
# collection.add(documents=documents, ids=ids)

# Perform a similarity search
results = collection.query(
    query_texts=["offline vector database"],
    n_results=2
)
print(f"Results: {results}")
