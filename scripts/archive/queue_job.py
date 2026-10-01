import os
import sys
import uuid
from pathlib import Path
from redis import Redis
from rq import Queue

job_id = "final_fast_quality_demo"
DATA = Path("data")
job_dir = DATA / job_id
input_dir = job_dir / "inputs"
input_dir.mkdir(parents=True, exist_ok=True)

import shutil
src = Path("demo/fast_quality_demo")
shutil.copy2(src / "video.mp4", input_dir / "video.mp4")
shutil.copy2(src / "gps.csv", input_dir / "gps.csv")
shutil.copy2("colorado_dataset/flight.json", input_dir / "flight_metadata.json")

r = Redis.from_url("redis://localhost:6379/0")
q = Queue("reconstruction", connection=r)

job = q.enqueue(
    "app.worker.process_job",
    args=(job_id,),
    job_id=job_id,
    kwargs={"options": {"profile": "FAST_QUALITY"}},
    job_timeout="1h"
)
print(f"Enqueued {job_id}")
