import sqlite3
import os

db_path = "data/jobs.db"
if not os.path.exists(db_path):
    print("Database not found")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get legacy project
cur.execute("SELECT id, name FROM projects WHERE id = 'default-legacy-project'")
proj = cur.fetchone()
print(f"Legacy Project: {proj}")

# Get MARS and Colorado
cur.execute("SELECT id, name, project_id FROM jobs WHERE id IN ('mars_hkairport01_quality', '95f51b12-b771-47bf-9201-c3700f9475a7')")
for row in cur.fetchall():
    print(f"Job: {row[0]} | Name: {row[1]} | Project: {row[2]}")

# Flight 38?
cur.execute("SELECT id, name, project_id FROM jobs WHERE name LIKE '%Flight 38%'")
for row in cur.fetchall():
    print(f"Flight 38 Job: {row[0]} | Name: {row[1]} | Project: {row[2]}")

conn.close()
