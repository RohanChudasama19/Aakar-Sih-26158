import requests

try:
    resp = requests.get('http://localhost:8000/api/v1/health')
    print(resp.status_code, resp.text)
except Exception as e:
    print(f"Error: {e}")
