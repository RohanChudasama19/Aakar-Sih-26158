import sqlite3
import hashlib
import os

source_db = 'data/jobs.db'
backup_db = 'data/jobs.db.bak_failed_cleanup'

if os.path.exists(backup_db):
    os.remove(backup_db)

# Create backup safely
def backup_database(src, dst):
    src_conn = sqlite3.connect(src)
    dst_conn = sqlite3.connect(dst)
    
    # Use SQLite's online backup API
    with dst_conn:
        src_conn.backup(dst_conn)
        
    src_conn.close()
    dst_conn.close()

backup_database(source_db, backup_db)

# Verify integrity
conn = sqlite3.connect(backup_db)
c = conn.cursor()
c.execute("PRAGMA integrity_check")
result = c.fetchone()[0]
conn.close()

# Get SHA256
with open(backup_db, 'rb') as f:
    hash_sha256 = hashlib.sha256(f.read()).hexdigest()

print(f"Backup path: {backup_db}")
print(f"File size: {os.path.getsize(backup_db)} bytes")
print(f"SHA256: {hash_sha256}")
print(f"Integrity check: {result}")
