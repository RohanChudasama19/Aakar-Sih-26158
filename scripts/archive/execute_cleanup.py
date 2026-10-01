import os
import shutil
import sqlite3
import hashlib
from pathlib import Path

def get_size(start_path):
    total = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total

data_dir = Path("data").resolve()
db_path = data_dir / "jobs.db"

shutil.copy2(db_path, data_dir / "jobs.db.cleanup.bak")
print("Backed up data/jobs.db")

# We only delete the specific approved ones
approved = [
    "206211f0-7407-4639-aab5-3adb49b6df03",
    "3f814df4-bb5b-4e00-ab07-ee6effd78d42",
    "5b85fba8-4e2b-4634-bac3-5a709f94bc1c",
    "95f51b12-b771-47bf-9201-c3700f9475a7",
    "9e6e5fc4-316d-4e92-bc56-0cb7bf72dacb",
    "b5eb3cc0-81b2-44fa-a6e7-f6d0a4b76750",
    "e1403ebf-70df-47ec-8f01-5e1285c66cb9",
    "FAST_VALIDATION",
    "test_benchmark"
]

total_reclaimed = 0
deleted_info = []

conn = sqlite3.connect(db_path)
c = conn.cursor()

for d in approved:
    p = data_dir / d
    if p.exists() and p.is_dir():
        sz = get_size(p)
        try:
            shutil.rmtree(p)
            total_reclaimed += sz
            deleted_info.append((d, sz, "User explicitly approved deletion of historical/benchmark outputs"))
        except Exception as e:
            print(f"Error deleting {p}: {e}")
            
        # Remove from DB if it is a job
        c.execute("DELETE FROM jobs WHERE id = ?", (d,))

# Remove stale DB records for anything not in 'data/' anymore
c.execute("SELECT id FROM jobs")
job_ids = [row[0] for row in c.fetchall()]
removed_stale = 0
for jid in job_ids:
    if jid != "mars_hkairport01_quality": # Explicitly preserve MARS
        if not (data_dir / jid).exists():
            c.execute("DELETE FROM jobs WHERE id = ?", (jid,))
            removed_stale += 1

conn.commit()
conn.close()

with open("cleanup_report.txt", "w") as f:
    f.write(f"RECLAIMED:{total_reclaimed}\n")
    f.write(f"STALE:{removed_stale}\n")
    for info in deleted_info:
        f.write(f"DEL:{info[0]}:{info[1]}:{info[2]}\n")

