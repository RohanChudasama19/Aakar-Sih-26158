import sqlite3
import os
from pathlib import Path

db_path = 'data/jobs.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, status FROM jobs")
jobs = c.fetchall()

broken = []
for jid, status in jobs:
    job_dir = Path("data") / jid
    if not job_dir.exists():
        broken.append(jid)
        continue
    
    if status == "completed":
        model_exists = (job_dir / "work" / "outputs" / "model.glb").exists()
        ply_exists = (job_dir / "work" / "outputs" / "dense_cloud.ply").exists()
        if not model_exists and not ply_exists:
            broken.append(jid)

for jid in broken:
    print(f"Deleting broken record: {jid}")
    c.execute("DELETE FROM jobs WHERE id = ?", (jid,))

conn.commit()
conn.close()
print(f"Deleted {len(broken)} broken records.")
