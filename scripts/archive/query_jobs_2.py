import sqlite3
import json

conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT id, name, status, report FROM jobs")
for row in c.fetchall():
    job_id = row[0]
    name = row[1]
    status = row[2]
    report_raw = row[3]
    if report_raw:
        try:
            report = json.loads(report_raw)
            print(f"Job: {job_id} | Name: {name} | Status: {status}")
            print(f"  Duration: {report.get('duration_sec', 'N/A')}")
            if 'sfm' in report:
                print(f"  Profile: {report['sfm'].get('profile', 'N/A')}")
            print("---")
        except:
            pass
