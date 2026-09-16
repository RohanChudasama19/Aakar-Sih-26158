import httpx
try:
    print(httpx.get("http://localhost:8000/api/jobs").json())
except Exception as e:
    print(e)
