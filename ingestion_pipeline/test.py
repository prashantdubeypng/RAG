from pymilvus import connections, Collection

# connect to a local Lite instance (stored as a file)
connections.connect("default", uri="milvus_lite.db")

# define schema and collection
fields = [
    {"name": "id", "type": "INT64", "is_primary": True},
    {"name": "embedding", "type": "FLOAT_VECTOR", "params": {"dim": 384}}
]
collection = Collection("example_collection", fields)

# insert and query
data = [
    [1, 2, 3],
    [[0.1]*384, [0.2]*384, [0.3]*384]
]
collection.insert(data)
collection.load()
results = collection.search([[0.1]*384], "embedding", limit=2, output_fields=["id"])
print(results)
