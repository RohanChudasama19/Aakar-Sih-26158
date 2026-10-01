import os
import sys
import time
import subprocess
from pathlib import Path
import sqlite3

# Get JID
conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT id FROM jobs ORDER BY created DESC LIMIT 1")
jid = c.fetchone()[0]
conn.close()

print(f"Found latest job: {jid}")

# Start worker
print("Starting worker...")
worker_proc = subprocess.Popen([sys.executable, "-m", "app.worker"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

events_file = Path(f"data/{jid}/work/events.jsonl")
report_file = Path(f"data/{jid}/work/outputs/mission_report.json")

print(f"Waiting for job {jid} to complete...")
while True:
    if events_file.exists():
        try:
            with open(events_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if "Packaging output" in last_line or "Zip packaging" in last_line or "Artifact generation" in last_line or "Exporting artifacts" in last_line:
                        print("Pipeline reached packaging!")
                        time.sleep(20)
                        break
        except Exception:
            pass
            
    if report_file.exists():
        print("Pipeline mission_report.json created!")
        time.sleep(10)
        break
        
    if worker_proc.poll() is not None:
        print("Worker died!")
        break
        
    time.sleep(30)

worker_proc.terminate()
print("Done!")
