import httpx

client = httpx.Client(base_url="http://localhost:8000")
res = client.get("/api/health")
print(res.json())
