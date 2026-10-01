import httpx
print(httpx.get('http://127.0.0.1:8002/api/health').json())
