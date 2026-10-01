import sqlite3
import os

db_path = 'data/jobs.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, name, status, created, project_id FROM jobs ORDER BY created DESC, id DESC")
jobs = c.fetchall()

failed = [j for j in jobs if j[2] == 'failed']
to_remove = []

for i, f in enumerate(failed):
    if i >= 10:
        if f[0] not in ['mars_hkairport01_quality', '95f51b12-b771-47bf-9201-c3700f9475a7']:
            to_remove.append(f[0])

print(f"Removing {len(to_remove)} DB records...")

try:
    c.execute("BEGIN TRANSACTION")
    
    # Use exact allowlist
    placeholders = ','.join('?' for _ in to_remove)
    c.execute(f"DELETE FROM jobs WHERE id IN ({placeholders})", tuple(to_remove))
    deleted_count = c.rowcount
    
    conn.commit()
    print(f"Removed {deleted_count} records successfully.")
except Exception as e:
    conn.rollback()
    print(f"Failed: {e}")
finally:
    conn.close()

