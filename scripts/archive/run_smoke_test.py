import requests
import time
import sys

jid = 'e1403ebf-70df-47ec-8f01-5e1285c66cb9'
print(f"Submitted Job ID: {jid}")

# Poll for completion
start = time.time()
while time.time() - start < 180:
    st = requests.get(f'http://127.0.0.1:8000/api/jobs/{jid}').json()
    print(f"Status: {st['status']}")
    if st['status'] in ('COMPLETED', 'FAILED'):
        if 'report' in st:
            print(f"Final Report: {st['report']}")
        break
    time.sleep(5)
