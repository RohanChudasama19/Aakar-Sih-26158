import asyncio
import json
import os
import shutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import structlog
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import API_TOKEN, DATA, MAX_UPLOAD_BYTES, REDIS_URL, ROOT
from .db import Job, Session, init_db, serialize, update
from .schemas import metadata, telemetry

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

local_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="reconstruction")


@asynccontextmanager
async def lifespan(app):
    init_db()
    # Local threads do not survive restart: surface the interrupted state.
    if not REDIS_URL:
        with Session.begin() as s:
            for j in s.scalars(select(Job).where(Job.status.in_(["running", "queued"]))):
                j.status = "failed"
                j.message = "Local server restarted before job finished. Submit again."
    logger.info("application_started", mode="local" if not REDIS_URL else "rq")
    yield
    logger.info("application_shutdown")


app = FastAPI(title="AeroRecon", version="0.1.0", lifespan=lifespan)


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("api_error", code=exc.code, status=exc.status_code, error=exc.message, request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "request_id": request_id, "details": exc.details}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("internal_error", error=str(exc), request_id=request_id, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred",
                "request_id": request_id,
                "details": {},
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("http_error", status=exc.status_code, error=exc.detail, request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": exc.detail, "request_id": request_id, "details": {}}},
    )


@app.middleware("http")
async def protect(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    if API_TOKEN and request.url.path.startswith("/api/"):
        import secrets

        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        if not secrets.compare_digest(token, API_TOKEN):
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Authentication required"}, status_code=401)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def queue_health():
    if not REDIS_URL:
        return {"mode": "local", "available": True, "workers": 1, "message": "Local CPU worker Â· one job at a time"}
    try:
        from redis import Redis
        from rq import Queue, Worker

        connection = Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        connection.ping()
        queue = Queue("reconstruction", connection=connection)
        workers = Worker.all(queue=queue)
        return {
            "mode": "rq",
            "available": len(workers) > 0,
            "workers": len(workers),
            "queued": len(queue),
            "message": f"{len(workers)} reconstruction worker(s) online"
            if workers
            else "No worker online. Start docker compose worker before uploading.",
        }
    except Exception:
        return {
            "mode": "rq",
            "available": False,
            "workers": 0,
            "message": "Queue is unreachable. Check Redis and worker containers.",
        }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response

    return Response(content=b"", media_type="image/x-icon", status_code=204)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "queue": queue_health(),
        "capabilities": {
            "colmap": shutil.which("colmap") is not None,
            "fbx": shutil.which("blender") is not None,
            "segmentation": bool(os.getenv("SEGMENTATION_MODEL", "")),
            "custom_pt_allowed": os.getenv("ALLOW_TRUSTED_PT", "0") == "1",
        },
        "limits": {"max_upload_bytes": MAX_UPLOAD_BYTES},
    }


async def save(upload, target, budget):
    total = 0
    print(f"Inside save: {target.name}, passed budget={budget}")
    with target.open("wb") as f:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > budget:
                raise HTTPException(413, f"Upload exceeds configured byte limit: {total} > {budget} ({target.name})")
            f.write(chunk)
    if total == 0:
        raise HTTPException(422, "An uploaded file is empty")
    await upload.close()
    return total


@app.post("/api/jobs", status_code=202)
async def submit(
    video: UploadFile = File(...),
    gps: UploadFile = File(...),
    flight: UploadFile = File(...),
    name: str = Form("Drone mission"),
    engine: str = Form("cpu"),
    max_frames: int = Form(180),
    imu: UploadFile | None = File(None),
    barometer: UploadFile | None = File(None),
    intrinsics: UploadFile | None = File(None),
        rtk: UploadFile | None = File(None),
    segmentation: UploadFile | None = File(None),
    depth: UploadFile | None = File(None),
    project_id: str = Form("default-legacy-project"),
):
    if engine not in ("cpu", "colmap"):
        raise HTTPException(422, "Engine must be cpu or colmap")
    if not 3 <= max_frames <= 1500:
        raise HTTPException(422, "Frame budget must be 3â€“1500")
    if not 1 <= len(name.strip()) <= 160:
        raise HTTPException(422, "Mission name must be 1â€“160 characters")
    health = queue_health()
    if not health["available"]:
        raise HTTPException(503, health["message"])
    if engine == "colmap" and os.getenv("ENABLE_COLMAP", "1") != "1":
        raise HTTPException(422, "COLMAP worker is not enabled. Follow GPU setup instructions first.")
    if segmentation and os.getenv("ALLOW_TRUSTED_PT", "0") != "1":
        raise HTTPException(
            422,
            "Custom PT loading is disabled. Only an administrator may enable trusted checkpoint loading; PT files can execute code.",
        )
    
    with Session.begin() as s:
        from .db import Project
        if not s.get(Project, project_id):
            raise HTTPException(422, "Project does not exist")

    ext = Path(video.filename or "").suffix.lower()
    if ext not in (".mp4", ".mov", ".avi", ".mkv"):
        raise HTTPException(422, "Video must be MP4, MOV, AVI or MKV")
    if depth and not (depth.filename or "").lower().endswith(".onnx"):
        raise HTTPException(422, "Custom depth checkpoint must follow the documented ONNX contract")
    jid = str(uuid.uuid4())
    directory = DATA / jid
    inputs = directory / "inputs"
    inputs.mkdir(parents=True)
    opts = {"engine": engine, "max_frames": max_frames, "max_width": 960 if engine == "cpu" else 1600}
    remaining = MAX_UPLOAD_BYTES
    try:
        files = [
            (video, "video" + ext),
            (gps, "gps.csv"),
            (flight, "flight.json"),
            (imu, "imu.csv"),
            (barometer, "barometer.csv"),
            (intrinsics, "intrinsics.json"),
            (rtk, "rtk.csv"),
            (segmentation, "segmentation.pt"),
            (depth, "depth.onnx"),
        ]
        for upload, filename in files:
            if upload:
                print(f"Remaining before {filename}: {remaining}")
                remaining -= await save(
                    upload,
                    inputs / filename,
                    min(remaining, 10 * 1024**2) if filename.endswith((".csv", ".json")) else remaining,
                )
        telemetry(inputs / "gps.csv")
        metadata(inputs / "flight.json")
        if (inputs / "intrinsics.json").exists():
            json.loads((inputs / "intrinsics.json").read_text())
        if segmentation:
            opts["segmentation_model"] = str(inputs / "segmentation.pt")
        elif os.getenv("SEGMENTATION_MODEL"):
            opts["segmentation_model"] = os.environ["SEGMENTATION_MODEL"]
        with Session.begin() as s:
            s.add(Job(id=jid, name=name.strip(), options=opts))
        if REDIS_URL:
            from redis import Redis
            from rq import Queue

            Queue("reconstruction", connection=Redis.from_url(REDIS_URL)).enqueue(
                "app.worker.process_job", jid, job_id=jid, job_timeout=86400, result_ttl=86400, failure_ttl=604800
            )
        else:
            from .worker import process_job

            local_pool.submit(process_job, jid)
    except HTTPException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    except (ValueError, KeyError, TypeError) as exc:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(422, str(exc))
    except Exception as exc:
        with Session() as s:
            exists = s.get(Job, jid) is not None
        if exists:
            update(jid, status="failed", message="Job could not be queued; check service logs")
        else:
            shutil.rmtree(directory, ignore_errors=True)
        import traceback

        traceback.print_exc()
        raise HTTPException(503, f"Job could not be queued. {exc}") from exc
    return {"id": jid, "status": "queued"}


@app.post("/api/jobs/{jid}/cancel")
def cancel_job(jid: str):
    from app.db import Job, Session

    with Session() as s:
        job = s.get(Job, jid)
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status in ("completed", "failed", "cancelled", "RECONSTRUCTION_BLOCKED"):
            return {"status": job.status, "message": "Job already inactive"}

        job.status = "cancelling"
        job.message = "Cancellation requested..."
        s.commit()

        # Also attempt rq cancel if it's queued but not running yet
        try:
            from redis import Redis
            from rq.job import Job as RQJob

            from app.config import REDIS_URL

            rq_job = RQJob.fetch(jid, connection=Redis.from_url(REDIS_URL))
            if rq_job.get_status() in ("queued", "deferred"):
                rq_job.cancel()
                job.status = "cancelled"
                job.message = "Job cancelled by user"
                s.commit()
        except Exception:
            pass

    return {"status": "cancelling"}


@app.post("/api/jobs/{jid}/retry")
def retry_job(jid: str):
    import shutil

    from app.config import DATA
    from app.db import Job, Session

    with Session() as s:
        job = s.get(Job, jid)
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status not in ("completed", "failed", "cancelled", "RECONSTRUCTION_BLOCKED"):
            raise HTTPException(400, "Can only retry inactive jobs")

        # Clean workspace to ensure safe retry (Option A: conservative)
        work_dir = DATA / jid / "work"
        if work_dir.exists():
            shutil.rmtree(str(work_dir), ignore_errors=True)

        job.status = "queued"
        job.message = "Queued for retry"
        job.progress = 0.0
        job.stage = ""
        s.commit()

        try:
            from redis import Redis
            from rq import Queue

            from app.config import REDIS_URL

            if REDIS_URL:
                q = Queue("reconstruction", connection=Redis.from_url(REDIS_URL))
                q.enqueue("app.worker.process_job", jid, job_id=jid, job_timeout=86400)
        except (ImportError, Exception):
            pass

    return {"status": "queued"}


from .db import Project, serialize_project
from pydantic import BaseModel, constr

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    location: str = ""

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None

@app.get("/api/projects")
def list_projects():
    with Session() as s:
        projects = s.query(Project).filter(Project.archived_at == None).all()
        # count missions
        res = []
        for p in projects:
            count = s.query(Job).filter(Job.project_id == p.id).count()
            data = serialize_project(p)
            data["mission_count"] = count
            res.append(data)
        return res

@app.post("/api/projects", status_code=201)
def create_project(data: ProjectCreate):
    if not 1 <= len(data.name.strip()) <= 160:
        raise HTTPException(422, "Project name must be 1-160 characters")
    p = Project(name=data.name.strip(), description=data.description, location=data.location)
    with Session.begin() as s:
        s.add(p)
    return serialize_project(p)

@app.get("/api/projects/{pid}")
def get_project(pid: str):
    with Session() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        data = serialize_project(p)
        data["mission_count"] = s.query(Job).filter(Job.project_id == pid).count()
        return data

@app.patch("/api/projects/{pid}")
def update_project(pid: str, data: ProjectUpdate):
    with Session.begin() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        if data.name is not None:
            if not 1 <= len(data.name.strip()) <= 160:
                raise HTTPException(422, "Project name must be 1-160 characters")
            p.name = data.name.strip()
        if data.description is not None:
            p.description = data.description
        if data.location is not None:
            p.location = data.location
        p.updated_at = time.time()
        return serialize_project(p)

@app.delete("/api/projects/{pid}")
def archive_project(pid: str):
    with Session.begin() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        p.archived_at = time.time()
        p.updated_at = time.time()
        return serialize_project(p)

@app.post("/api/projects/{pid}/restore")
def restore_project(pid: str):
    with Session.begin() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        p.archived_at = None
        p.updated_at = time.time()
        return serialize_project(p)

@app.get("/api/projects/{pid}/missions")
def get_project_missions(pid: str):
    with Session() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        jobs = s.query(Job).filter(Job.project_id == pid).order_by(Job.created.desc()).all()
        return [serialize(j) for j in jobs]



@app.delete("/api/jobs/{jid}")
def delete_job(jid: str):
    with Session.begin() as s:
        j = s.get(Job, jid)
        if not j:
            raise HTTPException(404, "Job not found")
        s.delete(j)
        # Rename directory instead of hard delete
        work_dir = DATA / jid / "work"
        if work_dir.exists():
            deleted_dir = DATA / f"deleted_{jid}"
            try:
                work_dir.rename(deleted_dir)
            except Exception:
                pass
        return {"status": "deleted"}


@app.get("/api/jobs")
def jobs():
    with Session() as s:
        res = []
        for j in s.scalars(select(Job).order_by(Job.created.desc()).limit(100)):
            d = serialize(j)
            if d["status"] == "completed":
                try:
                    d["representations"] = get_job_representations(j.id, d)
                except Exception:
                    d["representations"] = []
            res.append(d)
        return res

import re as _re
_JID_RE = _re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

def get_job(jid, include_reps=True):
    if not jid or not _JID_RE.match(jid):
        raise HTTPException(404, "Unknown job")
    with Session() as s:
        j = s.get(Job, jid)
        if j is None:
            raise HTTPException(404, "Unknown job")
        data = serialize(j)
    if REDIS_URL and data["status"] in ("queued", "running"):
        try:
            from redis import Redis
            from rq.job import Job as RQJob

            status = RQJob.fetch(jid, connection=Redis.from_url(REDIS_URL)).get_status(refresh=True)
            if str(getattr(status, "value", status)) in ("failed", "stopped", "canceled"):
                update(
                    jid,
                    status="failed",
                    message="Queue reports a failed or interrupted worker. Check job and worker logs.",
                )
                data["status"] = "failed"
                data["message"] = "Worker failed or was interrupted. Check worker logs."
        except Exception:
            pass
    if data["status"] == "running" and time.time() - data["updated"] > 90:
        data["message"] = "Worker heartbeat is stale. Check worker container; the job may have been interrupted."
    if include_reps and data["status"] == "completed":
        try:
            data["representations"] = get_job_representations(jid, data)
        except Exception:
            data["representations"] = []
    return data


@app.get("/api/jobs/{jid}")
def job(jid: str):
    return get_job(jid)


@app.get("/api/jobs/{jid}/events")
async def events(jid: str, request: Request):
    get_job(jid)

    async def stream():
        last = None
        offset = 0
        log = DATA / jid / "work" / "events.jsonl"
        while not await request.is_disconnected():
            data = get_job(jid)
            if log.exists():
                with log.open() as f:
                    f.seek(offset)
                    while True:
                        line = f.readline()
                        if not line or not line.endswith("\n"):
                            break
                        offset = f.tell()
                        event = json.loads(line)
                        snapshot = {
                            **data,
                            **{k: event[k] for k in ("stage", "progress", "message")},
                            "status": "running",
                        }
                        yield "data: " + json.dumps(snapshot) + "\n\n"
            text = json.dumps(data)
            if text != last:
                yield "data: " + text + "\n\n"
                last = text
            else:
                yield ": heartbeat\n\n"
            if data["status"] in ("completed", "failed", "cancelled", "RECONSTRUCTION_BLOCKED"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/api/jobs/{jid}/files")
def files(jid: str):
    data = get_job(jid, include_reps=False)
    if data["status"] != "completed":
        return []
    out = DATA / jid / "work" / "outputs"
    return [
        {
            "name": p.relative_to(out).as_posix(),
            "bytes": p.stat().st_size,
            "url": f"/api/jobs/{jid}/files/{p.relative_to(out).as_posix()}",
        }
        for p in sorted(out.rglob("*"))
        if p.is_file()
    ]


@app.get("/api/jobs/{jid}/files/{filename:path}")
def artifact(jid: str, filename: str):
    if not jid or not _JID_RE.match(jid):
        raise HTTPException(404, "Unknown job")
    data = get_job(jid, include_reps=False)
    if data["status"] != "completed":
        raise HTTPException(409, "Artifacts are available after the job finishes")
    out = (DATA / jid / "work" / "outputs").resolve()
    p = (out / filename).resolve()
    if not p.is_relative_to(out) or not p.is_file():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(p, filename=p.name)


@app.get("/api/jobs/{jid}/representations")
def representations(jid: str):
    return get_job_representations(jid, get_job(jid, include_reps=False))

def get_job_representations(jid: str, data: dict):
    """
    Return a canonical descriptor of all 6 viewer representations.
    Availability is derived from:
      1. viewer_artifacts.json (generated by viewer_artifacts.py)
      2. manifest.json validation state
      3. Direct file existence checks
    No reconstruction is triggered.
    """
    if data["status"] != "completed":
        raise HTTPException(409, "Representations are available after the job finishes")

    out = (DATA / jid / "work" / "outputs").resolve()
    base_url = f"/api/jobs/{jid}/files"

    def file_info(rel: str) -> dict:
        p = (out / rel).resolve()
        if not p.is_relative_to(out) or not p.is_file():
            return {"available": False}
        return {"available": True, "url": f"{base_url}/{rel}", "bytes": p.stat().st_size}

    # Load pre-generated viewer artifact report if available
    va_report: dict = {}
    va_path = out / "viewer_artifacts.json"
    if va_path.is_file():
        try:
            va_report = json.loads(va_path.read_text())
        except Exception:
            pass

    # Load manifest for validation status
    manifest: dict = {}
    manifest_path = out / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            pass

    validation = manifest.get("validation_results", {})

    def _va(key: str) -> dict:
        return va_report.get(key, {})

    # --- Sparse ---
    sparse_va = _va("sparse")
    sparse_fi = file_info("sparse/sparse.ply")
    cameras_fi = file_info("sparse/cameras.json")
    sparse_rep = {
        "available": sparse_fi["available"],
        "url": sparse_fi.get("url"),
        "format": "PLY",
        "bytes": sparse_fi.get("bytes"),
        "point_count": sparse_va.get("point_count"),
        "cameras_url": cameras_fi.get("url"),
        "camera_count": _va("cameras").get("camera_count"),
        "verification": "VERIFIED" if sparse_fi["available"] else "NOT_AVAILABLE",
    }

    # --- Dense ---
    display_va = _va("dense_display")
    dense_display_fi = file_info("pointcloud/dense_display.ply")
    # Fall back to dense_filtered if display cloud not generated
    dense_fallback_fi = file_info("dense_filtered.ply")
    dense_available = dense_display_fi["available"] or dense_fallback_fi["available"]
    dense_rep = {
        "available": dense_available,
        "url": dense_display_fi.get("url") or dense_fallback_fi.get("url"),
        "format": "PLY",
        "bytes": dense_display_fi.get("bytes") or dense_fallback_fi.get("bytes"),
        "display_point_count": display_va.get("display_point_count"),
        "analysis_point_count": display_va.get("original_point_count"),
        "downsampling_method": display_va.get("downsampling_method"),
        "analysis_url": base_url + "/dense_filtered.ply" if dense_fallback_fi["available"] else None,
        "verification": "VERIFIED" if dense_available else "NOT_AVAILABLE",
    }

    # --- Mesh (geometry only) ---
    glb_validation = validation.get("GLB", "")
    glb_fi = file_info("mesh/model.glb")
    if not glb_fi["available"]:
        glb_fi = file_info("model.glb")
    mesh_rep = {
        "available": glb_fi["available"] and "FAILED" not in glb_validation,
        "url": glb_fi.get("url"),
        "format": "GLB",
        "bytes": glb_fi.get("bytes"),
        "verification": glb_validation if glb_validation else ("VERIFIED" if glb_fi["available"] else "NOT_AVAILABLE"),
        "note": "Geometry-only view; textured materials replaced with neutral shading",
    }

    # --- Textured Mesh ---
    textured_rep = {
        "available": glb_fi["available"] and "FAILED" not in glb_validation,
        "url": glb_fi.get("url"),
        "format": "GLB",
        "bytes": glb_fi.get("bytes"),
        "verification": glb_validation if glb_validation else ("VERIFIED" if glb_fi["available"] else "NOT_AVAILABLE"),
    }

    # --- Semantic ---
    sem_fi = file_info("semantic/semantic_mesh.ply")
    # Also check legacy path
    sem_legacy_fi = file_info("semantic_mesh.ply")
    sem_available = sem_fi["available"] or sem_legacy_fi["available"]
    semantic_rep = {
        "available": sem_available,
        "url": sem_fi.get("url") or sem_legacy_fi.get("url"),
        "format": "PLY",
        "bytes": sem_fi.get("bytes") or sem_legacy_fi.get("bytes"),
        "classes": {
            0: "UNKNOWN",
            1: "GROUND",
            2: "ROAD",
            3: "BUILDING",
            4: "VEGETATION",
            5: "WATER",
            6: "INFRASTRUCTURE",
            7: "OBSTACLE",
        },
        "palette": {
            "UNKNOWN": "#808080",
            "GROUND": "#8B4513",
            "ROAD": "#323232",
            "BUILDING": "#C83232",
            "VEGETATION": "#228B22",
            "WATER": "#0000FF",
            "INFRASTRUCTURE": "#FFA500",
            "OBSTACLE": "#FFFF00",
        },
        "verification": "VERIFIED" if sem_available else "NOT_AVAILABLE",
    }

    # --- Confidence/Coverage ---
    conf_va = _va("confidence")
    conf_fi = file_info("mesh/confidence_mesh.ply")
    conf_summary_fi = file_info("mesh/surface_support_summary.json")
    conf_rep = {
        "available": conf_fi["available"],
        "url": conf_fi.get("url"),
        "format": "PLY",
        "bytes": conf_fi.get("bytes"),
        "summary_url": conf_summary_fi.get("url"),
        "supported_face_ratio": conf_va.get("supported_face_ratio"),
        "weak_face_ratio": conf_va.get("weak_face_ratio"),
        "unobserved_face_ratio": conf_va.get("unobserved_face_ratio"),
        "palette": {
            "SUPPORTED": "#22C55E",
            "WEAK": "#EAB308",
            "UNOBSERVED": "#EF4444",
        },
        "note": "Colors represent reconstruction support evidence, not positional accuracy",
        "verification": "VERIFIED" if conf_fi["available"] else "NOT_AVAILABLE",
    }

    return {
        "sparse": sparse_rep,
        "dense": dense_rep,
        "mesh": mesh_rep,
        "textured": textured_rep,
        "semantic": semantic_rep,
        "confidence": conf_rep,
    }


@app.get("/api/jobs/{jid}/download")
def download(jid: str):
    data = get_job(jid)
    p = DATA / jid / "work" / "artifacts.zip"
    if data["status"] != "completed" or not p.exists():
        raise HTTPException(409, "Result bundle not ready")
    return FileResponse(p, filename=f"aerorecon-{jid[:8]}.zip")


@app.get("/api/samples/{filename}")
def sample(filename: str):
    if filename not in ["sample.mp4", "gps.csv", "flight.json", "rtk-example.csv", "barometer-example.csv"]:
        raise HTTPException(404)
    return FileResponse(ROOT / "samples" / filename, filename=filename)


@app.get("/api/jobs/{jid}/map-data")
async def get_map_data(jid: str):
    job_dir = DATA / jid
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    report_path = job_dir / "work/outputs/mission_report.json"
    if not report_path.exists():
        raise HTTPException(404, "Mission report not available")

    report = json.loads(report_path.read_text())
    align = report.get("alignment", {})
    metric_state = align.get("metric_state", "RELATIVE")

    if metric_state == "RELATIVE":
        return {"metric_state": metric_state}

    gps_traj = []
    gps_path = job_dir / "inputs/gps.csv"
    if gps_path.exists():
        lines = gps_path.read_text().strip().split("\n")
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) >= 5:
                    gps_traj.append(
                        {
                            "timestamp": parts[0],
                            "frame": parts[1],
                            "lat": float(parts[2]),
                            "lon": float(parts[3]),
                            "alt": float(parts[4]),
                        }
                    )

    if metric_state != "GEOREFERENCED_METRIC":
        return {"metric_state": metric_state, "gps_trajectory": gps_traj}

    epsg = align.get("epsg")
    if not epsg:
        return {"metric_state": "RELATIVE", "error": "Missing EPSG"}

    s = align.get("scale", 1.0)
    import numpy as np

    R = np.array(align.get("rotation", np.eye(3)))
    t = np.array(align.get("translation", np.zeros(3)))
    origin = np.array(align.get("origin", np.zeros(3)))

    import pyproj

    transformer = pyproj.Transformer.from_crs(epsg, "EPSG:4326", always_xy=True)

    recon_traj = []
    poses_path = job_dir / "work/poses.json"
    if poses_path.exists():
        poses = json.loads(poses_path.read_text())
        for cid, pose_mat in poses.items():
            mat = np.array(pose_mat)
            if mat.shape != (3, 4):
                continue
            R_cam = mat[:, :3]
            t_cam = mat[:, 3]
            center_rel = -R_cam.T @ t_cam
            center_metric = s * (R @ center_rel) + t
            center_utm = center_metric + origin
            lon, lat = transformer.transform(center_utm[0], center_utm[1])
            recon_traj.append({"camera_id": cid, "lat": float(lat), "lon": float(lon), "alt": float(center_utm[2])})

    bounds = None
    if recon_traj:
        lats = [pt["lat"] for pt in recon_traj]
        lons = [pt["lon"] for pt in recon_traj]
        bounds = {"min_lat": min(lats), "max_lat": max(lats), "min_lon": min(lons), "max_lon": max(lons)}

    return {
        "metric_state": metric_state,
        "crs": f"EPSG:{epsg}",
        "epsg": epsg,
        "gps_trajectory": gps_traj,
        "reconstructed_trajectory": recon_traj,
        "mission_bounds": bounds,
        "alignment_quality": {
            "rmse_m": align.get("rmse_m"),
            "inliers": align.get("alignment_inliers"),
            "samples": align.get("alignment_samples"),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 — Independent Spatial Accuracy Validation
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/api/jobs/{jid}/validation")
async def get_validation(jid: str):
    """Return the independent spatial accuracy validation report.

    This report is generated from survey-grade checkpoint CSV files that are
    NOT used in the Phase-4 GPS/camera Sim(3) alignment fit.
    GPS alignment RMSE (mission_report.json) and this result are completely
    separate. The two must never be conflated.

    If no validation report exists, returns NOT_AVAILABLE.
    No reconstruction is triggered.
    """
    job_dir = DATA / jid
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    report_path = job_dir / "work/outputs/validation/validation_report.json"
    if report_path.exists():
        return json.loads(report_path.read_text())

    # No report: check if a checkpoint CSV even exists
    cp_path = job_dir / "inputs/checkpoints.csv"
    if cp_path.exists():
        reason = (
            "Checkpoint CSV found but validation report not yet generated. "
            "Re-run the mission or trigger validation manually."
        )
    else:
        reason = (
            "No independent checkpoints were provided. Upload a checkpoints.csv to enable spatial accuracy validation."
        )
    return {
        "status": "NOT_AVAILABLE",
        "reason": reason,
    }


@app.get("/api/jobs/{jid}/surface-validation")
async def get_surface_validation(jid: str):
    job_dir = DATA / jid
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    report_path = job_dir / "work/outputs/validation/surface_validation_report.json"
    if report_path.exists():
        import json

        return json.loads(report_path.read_text())

    return {"status": "NOT_AVAILABLE", "reason": "No independent surface reference geometry provided."}


@app.post("/api/jobs/{jid}/checkpoints", status_code=202)
async def upload_checkpoints(jid: str, checkpoints: UploadFile = File(...)):
    """Upload an independent checkpoint CSV for post-mission spatial accuracy validation.

    IMPORTANT: These checkpoints are used ONLY for validation.
    They are NOT used to fit the georeferencing transform.
    This distinction is by design and is enforced in app/pipeline/accuracy_validation.py.

    After upload, call POST /api/jobs/{jid}/run-validation to compute the report,
    or re-submit the job.
    """
    from app.pipeline.accuracy_validation import CheckpointValidationError, parse_checkpoint_csv

    job_dir = DATA / jid
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    if not checkpoints.filename:
        raise HTTPException(422, "No file provided")
    if not checkpoints.filename.endswith(".csv"):
        raise HTTPException(422, "File must be a .csv")

    # Save with size guard (10 MB)
    cp_path = job_dir / "inputs/checkpoints.csv"
    cp_path.parent.mkdir(parents=True, exist_ok=True)
    content = await checkpoints.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Checkpoint file exceeds 10 MB limit")

    # Validate schema before saving
    text = content.decode("utf-8-sig", errors="replace")
    try:
        # Write to temp path for parse_checkpoint_csv which needs a file
        import pathlib
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as tf:
            tf.write(text)
            tmp = pathlib.Path(tf.name)
        try:
            parsed = parse_checkpoint_csv(tmp)
        finally:
            tmp.unlink(missing_ok=True)
    except CheckpointValidationError as e:
        raise HTTPException(422, f"Invalid checkpoint CSV: {e}")

    cp_path.write_bytes(content)
    n_total = len(parsed)
    n_check = sum(1 for p in parsed if p["role"].value == "CHECKPOINT")
    n_ctrl = n_total - n_check
    return {
        "status": "accepted",
        "checkpoint_count": n_check,
        "control_count": n_ctrl,
        "message": (
            f"Checkpoint file accepted ({n_check} CHECKPOINT, {n_ctrl} CONTROL rows). "
            "These are used ONLY for validation, not for georeferencing."
        ),
    }


@app.post("/api/jobs/{jid}/run-validation", status_code=202)
async def run_validation(jid: str):
    """Trigger (re-)computation of the independent spatial accuracy validation report.

    Reads the existing checkpoint CSV and mission report, runs accuracy_validation.validate(),
    and writes the result to outputs/validation/validation_report.json.
    """
    from app.pipeline.accuracy_validation import VerticalDatum
    from app.pipeline.accuracy_validation import validate as av_validate

    job_dir = DATA / jid
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    report_path = job_dir / "work/outputs/mission_report.json"
    if not report_path.exists():
        raise HTTPException(409, "Mission report not available; job may not be completed")

    cp_path = job_dir / "inputs/checkpoints.csv"
    if not cp_path.exists():
        raise HTTPException(409, "No checkpoint CSV uploaded. Use POST /api/jobs/{jid}/checkpoints first")

    report = json.loads(report_path.read_text())
    geo = report.get("alignment", {})
    if not geo.get("epsg") or not geo.get("origin"):
        raise HTTPException(409, "Mission alignment data incomplete; cannot run validation")

    _mpp = job_dir / "work/outputs/mesh/model_filtered.ply"
    mesh_ply = _mpp if _mpp.exists() else None  # type: ignore[assignment]

    result = av_validate(
        geo=geo,
        ply_path=mesh_ply,
        checkpoint_csv_path=cp_path,
        recon_vertical_datum=VerticalDatum.UNKNOWN,
    )

    out_dir = job_dir / "work/outputs/validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation_report.json").write_text(json.dumps(result, indent=2))

    # Generate human-readable report
    _write_validation_txt(out_dir / "validation_report.txt", result)

    return result


def _write_validation_txt(path, report: dict):
    """Write a human-readable plain-text validation summary."""
    lines = [
        "AeroRecon Independent Spatial Accuracy Validation Report",
        "=" * 60,
        f"Status          : {report.get('status')}",
        f"CRS             : {report.get('crs')}",
        f"Method          : {report.get('method')}",
        f"Data source     : {report.get('data_source', 'UNKNOWN')}",
        f"Pass rule       : {report.get('pass_rule')}",
        f"Checkpoints used: {report.get('checkpoint_count_used')} / {report.get('checkpoint_count_checkpoint')}",
        "",
        "RMSE Summary",
        "-" * 40,
        f"  Horizontal RMSE : {_fmt(report.get('rmse_horizontal_m'))} m",
        f"  Vertical RMSE   : {_fmt(report.get('rmse_z_m'))} m",
        f"  3D RMSE         : {_fmt(report.get('rmse_3d_m'))} m",
        f"  Mean 3D error   : {_fmt(report.get('mean_3d_error_m'))} m",
        f"  Median 3D error : {_fmt(report.get('median_3d_error_m'))} m",
        f"  Max 3D error    : {_fmt(report.get('max_3d_error_m'))} m",
        f"  Threshold       : {report.get('threshold_m')} m",
        "",
    ]
    if report.get("warnings"):
        lines.append("Warnings")
        lines.append("-" * 40)
        for w in report["warnings"]:
            lines.append(f"  ! {w}")
        lines.append("")

    cps = report.get("checkpoints", [])
    if cps:
        lines.append("Per-Checkpoint Residuals")
        lines.append("-" * 80)
        lines.append(
            f"{'ID':<12} {'Role':<12} {'dX(m)':<9} {'dY(m)':<9} {'dZ(m)':<9} {'Horiz(m)':<10} {'3D(m)':<9} {'Status'}"
        )
        for cp in cps:
            lines.append(
                f"{cp['checkpoint_id']:<12} "
                f"{cp.get('role', ''):<12} "
                f"{_fmt(cp.get('dx')):<9} "
                f"{_fmt(cp.get('dy')):<9} "
                f"{_fmt(cp.get('dz')):<9} "
                f"{_fmt(cp.get('horizontal_error_m')):<10} "
                f"{_fmt(cp.get('error_3d_m')):<9} "
                f"{cp.get('checkpoint_status', '')}"
            )

    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(v) -> str:
    if v is None:
        return "N/A"
    return f"{v:.4f}"


from starlette.exceptions import HTTPException as StarletteHTTPException

VALID_SPA_ROUTES = {"", "projects", "new", "workspace", "analytics", "quality", "models", "exports", "settings"}

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    path = request.url.path
    if path.startswith("/api/") or path.startswith("/assets/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    
    segments = path.strip("/").split("/")
    root_segment = segments[0] if segments else ""
    
    if root_segment in VALID_SPA_ROUTES:
        index = ROOT / "web" / "index.html"
        if index.exists():
            return FileResponse(index)
            
    return JSONResponse({"detail": "Not found"}, status_code=404)

    return JSONResponse({"detail": "Frontend not built"}, status_code=404)


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
