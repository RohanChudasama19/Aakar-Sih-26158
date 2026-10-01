import requests
resp = requests.get("http://127.0.0.1:8000/api/samples/gps.csv")
print(resp.status_code)
