import sqlite3
import json

conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT id, report FROM jobs WHERE status = 'completed'")
for row in c.fetchall():
    job_id = row[0]
    report_raw = row[1]
    if report_raw:
        try:
            report = json.loads(report_raw)
            dur = report.get('processing_time_sec')
            if dur and 800 < dur < 900:
                print(f"ID: {job_id}")
                print(f"Time: {dur}")
                print(f"Dense points: {report.get('dense', {}).get('filtered_points')}")
                print(f"Mesh largest: {report.get('mesh', {}).get('largest_component_area_fraction')}")
                print(f"Texture coverage: {report.get('mesh', {}).get('textured_face_fraction')}")
        except:
            pass
