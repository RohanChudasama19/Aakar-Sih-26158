import sqlite3

db_path = 'data/jobs.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()

print("Tables in DB:")
for t in tables:
    print(f"- {t[0]}")
    
    # Check foreign keys for each table
    c.execute(f"PRAGMA foreign_key_list({t[0]})")
    fks = c.fetchall()
    for fk in fks:
        print(f"  FK: {fk[3]} -> {fk[2]}({fk[4]})")

conn.close()
