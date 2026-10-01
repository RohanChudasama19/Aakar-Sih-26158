import requests
import json
try:
    r = requests.get('http://127.0.0.1:8000/api/missions')
    print("Missions:", r.status_code)
    print(r.text[:500])
except Exception as e:
    print(e)
