from app.db import Session, Job
import json

rep_path = "data/mars_hkairport01_quality/work/outputs/mission_report.json"
rep = json.loads(open(rep_path).read())

with Session() as s:
    j = s.get(Job, "mars_hkairport01_quality")
    if j is not None:
        j.report = rep
        s.commit()
        print("Updated job.report in database!")
    else:
        print("Job not found in database!")
