from app.db import Session, Job
import time

with Session() as s:
    j = s.get(Job, "mars_hkairport01_quality")
    if j is None:
        j = Job(
            id="mars_hkairport01_quality",
            name="MARS HKairport01",
            status="completed",
            stage="",
            progress=1.0,
            message="Completed manually",
            created=time.time(),
            updated=time.time()
        )
        s.add(j)
    else:
        j.status = "completed"
    s.commit()
    print("Added/updated MARS job in database.")
