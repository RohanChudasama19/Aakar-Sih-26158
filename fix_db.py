import sqlite3

conn = sqlite3.connect("data/jobs.db")
c = conn.cursor()
c.execute("UPDATE jobs SET status = 'completed', name = 'Relative Test' WHERE status = 'Relative Test'")
conn.commit()
