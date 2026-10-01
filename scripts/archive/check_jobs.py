import requests, json
r = requests.get('http://127.0.0.1:8000/api/jobs')
data = r.json()
print("Job IDs found:", [d['id'] for d in data])
