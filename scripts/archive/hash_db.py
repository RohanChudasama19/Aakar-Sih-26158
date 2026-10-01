import hashlib
h = hashlib.sha256()
with open('data/jobs.db', 'rb') as f:
    h.update(f.read())
print("SHA256:", h.hexdigest())
