import sqlite3
import os

db_path = 'data/jobs.db'
if not os.path.exists(db_path):
    print('DB not found')
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name, status, created, project_id FROM jobs ORDER BY created DESC, id DESC")
    jobs = c.fetchall()
    
    print(f"Total jobs: {len(jobs)}")
    failed = [j for j in jobs if j[2] == 'failed']
    print(f"Failed jobs: {len(failed)}")
    
    for i, f in enumerate(failed):
        mark = "KEEP" if i < 10 else "REMOVE_DB_ONLY"
        if f[0] in ['mars_hkairport01_quality', '95f51b12-b771-47bf-9201-c3700f9475a7']:
            mark = "KEEP (PROTECTED)"
        print(f"  {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[4]} | {mark}")
    
    conn.close()
