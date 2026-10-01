from app.db import Session, Job
with Session() as s:
    jobs = s.query(Job).all()
    print("Count:", len(jobs))
    for j in jobs:
        print(" -", j.id, j.status)
