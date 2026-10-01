import sqlite3
import json

conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT id, status, report FROM jobs WHERE status = 'completed'")
for row in c.fetchall():
    job_id = row[0]
    report_raw = row[2]
    if report_raw:
        report = json.loads(report_raw)
        dur = report.get("processing_time_sec")
        if dur and 800 < dur < 1000:
            print(f"Job: {job_id}, duration: {dur}")
