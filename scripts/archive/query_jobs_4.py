import sqlite3
import json

conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT report FROM jobs WHERE id = '46795c3a-a0e6-4944-b14a-3a9361ad2fc1'")
report_raw = c.fetchone()[0]
report = json.loads(report_raw)
print(f"ID: 46795c3a-a0e6-4944-b14a-3a9361ad2fc1")
print(f"Time: {report.get('processing_time_sec')}")
print(f"Profile: {report.get('sfm', {}).get('profile', 'Unknown')} / {report.get('sfm', {}).get('ba_backend')} / {report.get('dense', {}).get('profile')}")
print(f"Dense points: {report.get('dense', {}).get('filtered_points')}")
print(f"Mesh largest: {report.get('mesh', {}).get('largest_component_area_fraction')}")
print(f"Texture coverage: {report.get('mesh', {}).get('textured_face_fraction')}")
