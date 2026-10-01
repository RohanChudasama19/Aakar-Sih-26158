import sqlite3
import json
import time
import os
import shutil

def main():
    conn = sqlite3.connect('data/jobs.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    job_id = None
    while not job_id:
        c.execute("SELECT id FROM jobs WHERE name = 'Demo Mission' AND status IN ('queued', 'running') ORDER BY created DESC LIMIT 1")
        row = c.fetchone()
        if row:
            job_id = row['id']
            print(f"Found Job ID: {job_id}", flush=True)
            break
        time.sleep(5)
        
    print(f"Monitoring job {job_id}...", flush=True)
    while True:
        c.execute("SELECT status, progress, report, message FROM jobs WHERE id = ?", (job_id,))
        row = c.fetchone()
        status = row['status']
        print(f"Status: {status} ({row['progress']}%): {row['message']}", flush=True)
        if status in ('completed', 'failed'):
            report_raw = row['report']
            break
        time.sleep(15)

    if status == 'failed':
        print(f"Job failed! Message: {row['message']}", flush=True)
        try:
            with open(f"data/{job_id}/error.log", "r") as f:
                print("Error log:")
                print(f.read())
        except:
            print("No error.log found.")
        return

    print("Success! Exiting monitor.")

if __name__ == '__main__':
    main()
