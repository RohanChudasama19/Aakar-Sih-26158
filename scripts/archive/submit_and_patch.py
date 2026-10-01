import requests
import json
import sqlite3

url = "http://127.0.0.1:8000/api/jobs"
files = {
    'video': ('video.mp4', open('demo/fast_quality_demo/video.mp4', 'rb'), 'video/mp4'),
    'gps': ('gps.csv', open('demo/fast_quality_demo/gps.csv', 'rb'), 'text/csv'),
    'flight': ('flight.json', open('colorado_dataset/flight.json', 'rb'), 'application/json')
}
data = {'name': 'Final Production Run FAST_QUALITY', 'engine': 'colmap'}

print("Submitting to API...")
r = requests.post(url, files=files, data=data)
if r.status_code == 202:
    resp = r.json()
    jid = resp['id']
    print(f"Job created: {jid}")
    
    # Patch SQLite!
    conn = sqlite3.connect('data/jobs.db')
    c = conn.cursor()
    c.execute("SELECT options FROM jobs WHERE id=?", (jid,))
    row = c.fetchone()
    if row:
        opts = json.loads(row[0])
        opts["profile"] = "FAST_QUALITY"
        c.execute("UPDATE jobs SET options=? WHERE id=?", (json.dumps(opts), jid))
        conn.commit()
        print("Patched database to include FAST_QUALITY profile.")
    else:
        print("Error: Job not found in DB!")
    conn.close()
else:
    print(f"Failed to submit: {r.status_code} {r.text}")
