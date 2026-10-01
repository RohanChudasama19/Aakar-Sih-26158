from app.db import Session, Job
import json
with Session() as s:
    j = s.get(Job, 'mars_hkairport01_quality')
    if j and j.report:
        print(json.dumps(j.report, indent=2))
