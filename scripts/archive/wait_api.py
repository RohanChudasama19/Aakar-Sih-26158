import time
import requests
import json

for i in range(10):
    try:
        r = requests.get('http://127.0.0.1:8000/api/v1/missions')
        if r.status_code == 200:
            print("API ready.")
            print(json.dumps(r.json(), indent=2))
            break
    except Exception as e:
        pass
    time.sleep(2)
else:
    print("API not responding.")
