import sqlite3
conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT id, status, pipeline_report FROM jobs")
for row in c.fetchall():
    job_id = row[0]
    status = row[1]
    report = row[2]
    if report and ('"FAST_QUALITY"' in report or '"FAST"' in report or '"GLOBAL_FAST"' in report):
        print(f"Job: {job_id}, Status: {status}")
        # print excerpt
        print(report[:200])
        print("----------------")
