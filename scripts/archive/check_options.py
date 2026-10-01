import sys
import sqlite3
import json
conn = sqlite3.connect('data/jobs.db')
c = conn.cursor()
c.execute("SELECT options FROM jobs WHERE id=?", ('6ffe72c9-c309-4f1f-91a6-6385e4ee6b34',))
row = c.fetchone()
if row and row[0]:
    print(json.loads(row[0]))
else:
    print("No options found")
