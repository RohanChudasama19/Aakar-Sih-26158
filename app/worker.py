import os
import threading
import traceback
from .config import DATA,REDIS_URL
from .db import init_db,update
from .pipeline.runner import run_pipeline
from .storage import upload_job


def process_job(job_id):
    from .db import Session,Job
    init_db()
    with Session() as s:
        job=s.get(Job,job_id)
        if job is None: raise ValueError('Unknown job')
        options=job.options
    directory=DATA/job_id
    stop=threading.Event()
    def heartbeat():
        while not stop.wait(10):
            try: update(job_id)
            except Exception: pass
    thread=threading.Thread(target=heartbeat,daemon=True); thread.start()
    try:
        update(job_id,status='running',message='Worker started')
        report=run_pipeline(directory/'inputs',directory/'work',options,lambda stage,p,message:update(job_id,stage=stage,progress=p,message=message))
        upload_job(job_id,directory/'work'/'outputs')
        upload_job(job_id,directory/'inputs')
        update(job_id,status='completed',progress=100,report=report,message='Completed · review accuracy and coverage limitations')
        return report
    except BaseException as exc:
        (directory/'error.log').write_text(traceback.format_exc())
        update(job_id,status='failed',message=str(exc)[:1900])
        raise
    finally:
        stop.set(); thread.join(timeout=1)

if __name__=='__main__':
    from redis import Redis
    from rq import Worker,Queue
    init_db()
    connection=Redis.from_url(REDIS_URL)
    Worker([Queue('reconstruction',connection=connection)],connection=connection).work()
