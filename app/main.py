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
        return {"mode": "local", "available": True, "workers": 1, "message": "Local CPU worker · one job at a time"}
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
    with target.open("wb") as f:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > budget:
                raise HTTPException(413, "Upload exceeds configured byte limit")
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
):
    if engine not in ("cpu", "colmap"):
        raise HTTPException(422, "Engine must be cpu or colmap")
    if not 3 <= max_frames <= 1500:
        raise HTTPException(422, "Frame budget must be 3–1500")
    if not 1 <= len(name.strip()) <= 160:
        raise HTTPException(422, "Mission name must be 1–160 characters")
    health = queue_health()
    if not health["available"]:
        raise HTTPException(503, health["message"])
    if engine == "colmap" and os.getenv("ENABLE_COLMAP", "0") != "1":
        raise HTTPException(422, "COLMAP worker is not enabled. Follow GPU setup instructions first.")
    if segmentation and os.getenv("ALLOW_TRUSTED_PT", "0") != "1":
        raise HTTPException(
            422,
            "Custom PT loading is disabled. Only an administrator may enable trusted checkpoint loading; PT files can execute code.",
        )
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
                remaining -= await save(
                    upload,
                    inputs / filename,
                    min(remaining, 2 * 1024**2) if filename.endswith((".csv", ".json")) else remaining,
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
                "app.worker.process_job", jid, job_id=jid, job_timeout=10800, result_ttl=86400, failure_ttl=604800
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
        raise HTTPException(503, "Job could not be queued. Check API/Redis logs.") from exc
    return {"id": jid, "status": "queued"}


@app.get("/api/jobs")
def jobs():
    with Session() as s:
        return [serialize(j) for j in s.scalars(select(Job).order_by(Job.created.desc()).limit(100))]


def get_job(jid):
    try:
        uuid.UUID(jid)
    except ValueError:
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
    data = get_job(jid)
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
    data = get_job(jid)
    if data["status"] != "completed":
        raise HTTPException(409, "Artifacts are available after the job finishes")
    out = (DATA / jid / "work" / "outputs").resolve()
    p = (out / filename).resolve()
    if not p.is_relative_to(out) or not p.is_file():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(p, filename=p.name)


@app.get("/api/jobs/{jid}/representations")
def representations(jid: str):
    """
    Return a canonical descriptor of all 6 viewer representations.
    Availability is derived from:
      1. viewer_artifacts.json (generated by viewer_artifacts.py)
      2. manifest.json validation state
      3. Direct file existence checks
    No reconstruction is triggered.
    """
    data = get_job(jid)
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


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
