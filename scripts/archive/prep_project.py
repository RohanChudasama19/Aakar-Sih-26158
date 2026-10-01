import requests
import sys

# Create project
r = requests.post('http://127.0.0.1:8000/api/projects', json={
    'name': 'MARS Rehearsal',
    'description': 'Rehearsal project for demo',
    'location': 'Local'
})
if r.status_code == 200:
    pid = r.json()['id']
    print(pid)
else:
    print(f"Failed to create project: {r.text}")
    sys.exit(1)
