import sqlite3
import os

db_path = 'data/jobs.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("PRAGMA integrity_check")
integrity = c.fetchone()[0]

c.execute("SELECT id FROM jobs WHERE status = 'failed'")
remaining_failed = c.fetchall()

c.execute("SELECT id FROM jobs WHERE status != 'failed'")
non_failed = c.fetchall()

c.execute("SELECT id FROM jobs WHERE id = 'mars_hkairport01_quality'")
mars_exists = c.fetchone() is not None

c.execute("SELECT id FROM jobs WHERE id = '95f51b12-b771-47bf-9201-c3700f9475a7'")
colorado_exists = c.fetchone() is not None

print(f"Integrity check: {integrity}")
print(f"Remaining failed missions: {len(remaining_failed)}")
print(f"Non-failed jobs preserved: {len(non_failed)}")
print(f"MARS exists: {mars_exists}")
print(f"Colorado exists: {colorado_exists}")

conn.close()
