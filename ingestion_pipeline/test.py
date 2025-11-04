from client import IngestionClient

# Initialize
client = IngestionClient()
# 
# Upload  file
# result = client.upload_file("C:\\Users\\Hp\\Downloads\\simpleadio.mp3")
# print(result["chunks_processed"])

# Search
results = client.search("up Scholarship", n_results=5)
print(results)
