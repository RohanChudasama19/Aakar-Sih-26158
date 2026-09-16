import json
import shutil
import sqlite3
import uuid
from pathlib import Path

# Create a RELATIVE job
jid = str(uuid.uuid4())

# Copy the work dir
src = Path("data/db63f615-1043-4f4d-9387-d948fde5f6a1")
dst = Path(f"data/{jid}")
shutil.copytree(src, dst)

# Modify mission report to RELATIVE
rep = dst / "work/outputs/mission_report.json"
data = json.loads(rep.read_text())
data["alignment"]["metric_state"] = "RELATIVE"
data["metric_state"] = "RELATIVE"
rep.write_text(json.dumps(data))

# Insert into jobs.db
conn = sqlite3.connect("data/jobs.db")
c = conn.cursor()
# We can just copy the existing job row and change ID
c.execute("SELECT * FROM jobs WHERE id = 'db63f615-1043-4f4d-9387-d948fde5f6a1'")
row = c.fetchone()
if row:
    row = list(row)
    row[0] = jid
    row[2] = "Relative Test"
    c.execute(f"INSERT INTO jobs VALUES ({','.join(['?' for _ in row])})", row)
    conn.commit()

with open("e2e_rel_jid.txt", "w") as f:
    f.write(jid)
