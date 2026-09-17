import threading
import traceback

from .config import DATA, REDIS_URL
from .db import init_db, update
from .pipeline.runner import run_pipeline
from .storage import upload_job


def process_job(job_id):
    from .db import Job, Session

    init_db()
    with Session() as s:
        job = s.get(Job, job_id)
        if job is None:
            raise ValueError("Unknown job")
        options = job.options
    directory = DATA / job_id
    stop = threading.Event()


    def heartbeat():
        import os

        import psutil

        from .db import Job, Session

        while not stop.wait(3):
            try:
                update(job_id)
                # Check for cancellation
                with Session() as s:
                    j = s.get(Job, job_id)
                    if j and j.status == "cancelling":
                        update(job_id, status="cancelled", message="Job cancelled by user")
                        # Kill process tree
                        parent = psutil.Process(os.getpid())
                        for child in parent.children(recursive=True):
                            try:
                                child.kill()
                            except psutil.NoSuchProcess:
                                pass
                        os._exit(1)
            except Exception:
                pass


    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        update(job_id, status="running", message="Worker started")
        report = run_pipeline(
            directory / "inputs",
            directory / "work",
            options,
            lambda stage, p, message: update(job_id, stage=stage, progress=p, message=message),
        )
        upload_job(job_id, directory / "work" / "outputs")
        upload_job(job_id, directory / "inputs")

        import json

        ready_report_path = directory / "work" / "outputs" / "cv_quality_report.json"
        if ready_report_path.exists():
            ready_report = json.loads(ready_report_path.read_text())
            update(
                job_id,
                status="completed",
                progress=100,
                report=report,
                message="Completed · review accuracy and coverage limitations",
                readiness_status=ready_report.get("status", "pending"),
                readiness_score=ready_report.get("scores", {}).get("overall_readiness_score", 0.0),
                readiness_report_path="cv_quality_report.json",
            )
        else:
            update(
                job_id,
                status="completed",
                progress=100,
                report=report,
                message="Completed · review accuracy and coverage limitations",
            )
        return report
    except Exception as exc:
        if type(exc).__name__ == "ReadinessBlockedError":
            report = exc.report
            (directory / "error.log").write_text("Blocked by readiness gate:\n" + "\n".join(report["blocking_reasons"]))
            update(
                job_id,
                status="RECONSTRUCTION_BLOCKED",
                message="Blocked by readiness gate",
                readiness_status=report["status"],
                readiness_score=report["scores"]["overall_readiness_score"],
                readiness_report_path="cv_quality_report.json",
            )
            # Upload artifacts so the report is accessible
            upload_job(job_id, directory / "work" / "outputs")
            return report
        (directory / "error.log").write_text(traceback.format_exc())
        update(job_id, status="failed", message=str(exc)[:1900])
        raise
    finally:
        stop.set()
        thread.join(timeout=1)


if __name__ == "__main__":
    from redis import Redis
    from rq import Queue, Worker

    init_db()
    connection = Redis.from_url(REDIS_URL)
    Worker([Queue("reconstruction", connection=connection)], connection=connection).work()
