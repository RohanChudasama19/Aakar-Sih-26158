import sqlite3
c = sqlite3.connect('data/jobs.db')
print(c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
