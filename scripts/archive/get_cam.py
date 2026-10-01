import sqlite3
import json

conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT report FROM jobs WHERE status = 'completed' AND report IS NOT NULL")
rows = c.fetchall()
for r in rows:
    report = json.loads(r[0])
    if 'camera' in report:
        print(report['camera'])
    elif 'sfm' in report:
        # maybe camera is inside sfm report
        print(report['sfm'])
