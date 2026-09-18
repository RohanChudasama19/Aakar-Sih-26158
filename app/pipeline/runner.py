import json
import shutil
import time
from pathlib import Path

import numpy as np

from ..schemas import intrinsics, metadata, telemetry
from . import exports, georef, mesh, preprocess, readiness, semantic


class ReadinessBlockedError(Exception):
    def __init__(self, report):
        self.report = report
        super().__init__("Reconstruction blocked by readiness gate")


STAGES = {
    "A": "Ingest & preprocess",
    "B": "Pose estimation & GPS alignment",
    "C": "Dense reconstruction",
    "D": "Mesh extraction & texturing",
    "E": "Semantic layer",
    "F": "Export packaging & scene report",
}


def clean(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def _build_hardware_info() -> dict:
    """Return actual hardware info including real GPU from nvidia-smi."""
    import platform as _platform

    _g = _detect_gpu_info()
    return {
        "cpu": _platform.processor() or _platform.machine(),
        "gpu": _g.get("name", "unknown"),
        "gpu_driver": _g.get("driver", "unknown"),
        "vram_total_mib": _g.get("vram_total_mib"),
        "benchmark_verified": bool(_g),
    }


def _detect_gpu_info() -> dict:
    """Query nvidia-smi for actual GPU name/driver/VRAM. Returns empty dict if unavailable."""
    import subprocess as _sp

    try:
        r = _sp.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = [p.strip() for p in r.stdout.strip().split(",")]
            return {
                "name": parts[0] if len(parts) > 0 else "unknown",
                "driver": parts[1] if len(parts) > 1 else "unknown",
                "vram_total_mib": int(parts[2]) if len(parts) > 2 else None,
                "vram_used_at_start_mib": int(parts[3]) if len(parts) > 3 else None,
            }
    except Exception:
        pass
    return {}


def run_pipeline(input_dir, work, options=None, callback=None):
    input_dir, work = Path(input_dir), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    out = work / "outputs"
    out.mkdir(exist_ok=True)
    opts = dict(options or {})
    start = time.monotonic()
    stages = {}
    events = []
    current = "A"
    stage_start = start
    sub_stages: dict = {}

    import contextlib as _contextlib

    @_contextlib.contextmanager
    def timed(name: str):
        """Record wall-clock duration of a named sub-stage."""
        t0 = time.monotonic()
        try:
            yield
        finally:
            sub_stages[name] = round(time.monotonic() - t0, 3)

    def progress(p, message):
        e = {
            "stage": current,
            "progress": round(p, 1),
            "message": message,
            "elapsed_sec": round(time.monotonic() - start, 2),
        }
        events.append(e)
        with (work / "events.jsonl").open("a") as f:
            f.write(json.dumps(e) + "\n")
        if callback:
            callback(current, p, message)

    def stage(code, p):
        nonlocal current, stage_start
        if code != current:
            stages[current] = {"elapsed_sec": round(time.monotonic() - stage_start, 3), "status": "completed"}
        current = code
        stage_start = time.monotonic()
        progress(p, STAGES[code])

    meta = metadata(input_dir / "flight.json")
    gps = telemetry(input_dir / "gps.csv")
    video = next((p for p in input_dir.glob("video.*")), None)
    if video is None:
        raise ValueError("Missing video")
    override = (
        json.loads((input_dir / "intrinsics.json").read_text()) if (input_dir / "intrinsics.json").exists() else None
    )

    stage("A", 1)

    # Run Readiness Analysis
    progress(2, "Running input quality and readiness analysis")

    # Attempt to parse intrinsics for readiness if available (meta or override), using dummy width/height as it relies on resolution
    # Readiness scales it anyway
    import app.schemas as schemas

    k_test = None
    try:
        # Default analysis resolution is 960 width
        # The schema might raise an error if K is bad, we just ignore K if so
        k_test = schemas.intrinsics(meta, 960, 540, override)
    except Exception:
        pass

    with timed("readiness_analysis"):
        ready_report = readiness.perform_analysis(video, gps, meta, k_test)
    (out / "cv_quality_report.json").write_text(json.dumps(ready_report, indent=2))

    lines = [
        "RECONSTRUCTION READINESS REPORT",
        f"Status: {ready_report['status']}",
        f"Score: {ready_report['scores']['overall_readiness_score']:.1f}",
        "",
    ]
    if ready_report["blocking_reasons"]:
        lines.extend(["BLOCKING REASONS:", *[f"- {r}" for r in ready_report["blocking_reasons"]], ""])
    if ready_report["warnings"]:
        lines.extend(["WARNINGS:", *[f"- {r}" for r in ready_report["warnings"]], ""])
    if ready_report["recommendations"]:
        lines.extend(["RECOMMENDATIONS:", *[f"- {r}" for r in ready_report["recommendations"]], ""])
    (out / "cv_quality_report.txt").write_text("\n".join(lines))

    if ready_report["status"] == "NOT_READY":
        raise ReadinessBlockedError(ready_report)

    if ready_report["status"] == "WARNING":
        progress(5, "Readiness analysis produced warnings. Proceeding.")
    else:
        progress(5, "Readiness analysis passed.")

    with timed("frame_extraction"):
        info = preprocess.extract(video, work / "frames", opts, progress)

    camera = intrinsics(meta, info["width"], info["height"], override)

    # Save camera artifact
    (out / "camera_model.json").write_text(json.dumps(clean(camera.to_dict()), indent=2))

    if abs(info["fps"] - float(meta["video_fps"])) > max(0.1, info["fps"] * 0.02):
        raise ValueError(
            "Flight metadata FPS differs from the decoded video; telemetry frame alignment would be unreliable"
        )
    if abs(info["duration_sec"] - float(meta["video_duration_sec"])) > max(1.0, info["duration_sec"] * 0.02):
        raise ValueError("Flight metadata duration differs from decoded video")
    from datetime import datetime

    start_utc = datetime.fromisoformat(meta["start_time_utc"].replace("Z", "+00:00")).timestamp()
    info["start_time_utc"] = start_utc

    for sample in gps:
        if abs(sample["time"] - start_utc - sample["frame"] / info["fps"]) > max(0.25, 2 / info["fps"]):
            raise ValueError("GPS UTC/frame values are inconsistent with the video FPS and flight start time")

    # Undistort images if needed
    import cv2

    from ..camera import Undistorter

    undistorter = Undistorter(camera)
    if any(camera.distortion):
        progress(10, "Undistorting extracted frames")
        undistorted_dir = work / "undistorted_frames"
        undistorted_dir.mkdir(exist_ok=True)
        undistorted_originals_dir = work / "undistorted_originals"
        undistorted_originals_dir.mkdir(exist_ok=True)

        for f in info["frames"]:
            # Undistort processed frames
            frame_path = work / "frames" / f["name"]
            img = cv2.imread(str(frame_path))
            if img is not None:
                img_u = undistorter.undistort_image(img)
                cv2.imwrite(str(undistorted_dir / f["name"]), img_u)

            # Undistort original frames
            orig_path = work / "originals" / f["name"]
            img_orig = cv2.imread(str(orig_path))
            if img_orig is not None:
                img_orig_u = undistorter.undistort_image(img_orig)
                cv2.imwrite(str(undistorted_originals_dir / f["name"]), img_orig_u)

        # Replace directory pointers for downstream stages
        frames_dir = undistorted_dir
        originals_dir = undistorted_originals_dir
        active_camera = undistorter.get_undistorted_camera()
    else:
        frames_dir = work / "frames"
        originals_dir = work / "originals"
        active_camera = camera

    k = active_camera.to_matrix()

    stage("B", 20)
    from .sfm_backend import execute_sfm

    force_cpu = not (opts.get("engine", "") or "").lower().startswith("colmap")

    with timed("sfm"):
        reconstruction = execute_sfm(frames_dir, info, active_camera, progress, force_cpu=force_cpu)

    # Write SfM Report
    sfm_report = reconstruction.get("sfm_report", {})
    (out / "sfm_report.json").write_text(json.dumps(clean(sfm_report), indent=2))

    lines = [
        "STRUCTURE FROM MOTION (SFM) REPORT",
        f"Backend: {sfm_report.get('backend')}",
        f"Mapper Strategy: {sfm_report.get('mapper_strategy')}",
        f"Registered Cameras: {sfm_report.get('registered_cameras')}/{sfm_report.get('input_frames')} ({sfm_report.get('registration_ratio', 0) * 100:.1f}%)",
        f"Sparse Points: {sfm_report.get('sparse_point_count')}",
        f"Median Reprojection Error: {sfm_report.get('median_reprojection_error_px', 0.0):.3f} px",
        f"Median Track Length: {sfm_report.get('median_track_length', 0.0)}",
        f"BA Backend: {sfm_report.get('ba_backend')}",
        f"SfM Runtime: {sfm_report.get('sfm_runtime_sec', 0.0):.1f} s",
        "",
    ]
    if "fallback_reason" in sfm_report:
        lines.append(f"Fallback Reason: {sfm_report['fallback_reason']}")

    (out / "sfm_report.txt").write_text("\n".join(lines))

    with timed("georef"):
        geo = georef.align(reconstruction, info, gps, input_dir)
    np.savez_compressed(work / "sparse.npz", points=reconstruction["points"], colors=reconstruction["colors"])
    (work / "poses.json").write_text(json.dumps(clean(reconstruction["poses"])))
    (work / "alignment.json").write_text(json.dumps(clean(geo), indent=2))
    stage("C", 43)
    from .dense_backend import execute_dense

    with timed("dense"):
        points, colors, dense_report = execute_dense(reconstruction, k, frames_dir, work, opts, geo, progress)
    if (input_dir / "depth.onnx").exists():
        from .depth import infer

        dense_report["custom_depth"] = infer(input_dir / "depth.onnx", reconstruction, k, originals_dir, out, progress)

    np.savez_compressed(work / "dense.npz", points=points, colors=colors)

    import trimesh

    if len(points) > 0:
        _pc_path = out / "dense_filtered.ply"
        trimesh.points.PointCloud(points, colors=colors).export(_pc_path)
        shutil.copy2(str(_pc_path), str(out / "dense_relative.ply"))  # avoid re-serializing identical data
        if geo["valid"]:
            from .exports import transform

            local = transform(points, geo)
            absolute = local + geo["origin"]
            trimesh.points.PointCloud(absolute, colors=colors).export(out / "dense_metric.ply")

    stage("D", 62)
    with timed("mesh"):
        surface, mesh_report = mesh.build_mesh(
            points, colors, geo, reconstruction, k, originals_dir, out_dir=out, options=opts
        )
    stage("E", 78)
    with timed("semantics"):
        semantic_report = semantic.classify(
            points, colors, geo, surface, out, sfm=reconstruction, k=k, directory=originals_dir, options=opts
        )

    stage("F", 93)
    # Load semantic labels for export if available
    point_labels = None
    labels_file = out / "semantic_labels.npz"
    if labels_file.exists():
        try:
            with np.load(labels_file) as d:
                point_labels = d["point_labels"]
        except Exception:
            pass

    # Generate compact viewer artifacts (sparse PLY, display cloud, confidence mesh, semantic copy)
    try:
        from .viewer_artifacts import generate_all_viewer_artifacts

        generate_all_viewer_artifacts(
            out_dir=out,
            reconstruction=reconstruction,
            dense_points=points,
            dense_colors=colors,
            mesh=surface,
        )
    except Exception as _va_err:
        import warnings

        warnings.warn(f"Viewer artifact generation failed (non-fatal): {_va_err}")

    with timed("exports"):
        export_report = exports.export_all(surface, points, colors, geo, out, point_labels=point_labels)

    elapsed = time.monotonic() - start
    stages["F"] = {"elapsed_sec": round(time.monotonic() - stage_start, 3), "status": "completed"}
    warnings = [
        "This build uses geometric SfM + stereo, not trained Gaussian Splatting/InstantSplat.",
        "GPS alignment RMSE is a fit residual, not independently verified spatial accuracy.",
        "Unseen surfaces are not reconstructed. Frame registration is not a surface coverage measurement.",
        "Texture selection uses per-face camera projection without multiband seam blending or full occlusion testing.",
        "3D Poisson meshing interpolates surfaces and can smooth detail; it is not proof of observed completeness or watertightness.",
        "Semantic classes are unvalidated color/height heuristics.",
        "No learned deblurring: blurred frames are rejected to avoid invented detail.",
    ]
    if mesh_report["surface_quality"] != "CONNECTED_SURFACE_ESTIMATE":
        warnings.append(
            "Surface quality is insufficient: "
            + mesh_report["surface_quality"]
            + ". Processing completion does not mean a realistic model was recovered."
        )
    if not info["dynamic_masking"]:
        warnings.append("Dynamic segmentation disabled: install/configure trusted YOLO segmentation weights.")
    if info["truncated"]:
        warnings.append(
            "Frame budget reached before end of clip; visible-scene coverage is incomplete. Increase max_frames."
        )
    if not geo["valid"]:
        warnings.append(geo["reason"])
    if (input_dir / "imu.csv").exists():
        warnings.append(
            "IMU was archived but is not fused: this build has no calibrated IMU-to-camera extrinsics/time-offset estimator."
        )
    if any(
        "FAILED" in str(s) or "NOT_AVAILABLE" in str(s) for s in export_report.get("validation_results", {}).values()
    ):
        warnings.append("Some exports are unavailable or failed validation; consult manifest.json.")
    report = {
        "application": "AeroRecon",
        "build_tier": "reduced_fidelity_reference_implementation",
        "mission": meta["mission_name"],
        "synthetic_input": bool(meta.get("synthetic", False)),
        "status": "completed_with_limitations",
        "processing_time_sec": round(elapsed, 3),
        "video_duration_sec": info["duration_sec"],
        "engine": reconstruction["engine"],
        "hardware": _build_hardware_info(),
        "targets": {
            "processing_time": {
                "target": "< 15 min for a 10-min video",
                "measured_sec": round(elapsed, 3),
                "ten_minute_benchmark_passed": None,
                "reason": "Only this input was timed; no extrapolation to 10 minutes",
            },
            "spatial_accuracy": {
                "target": "≤ 1 m",
                "gps_alignment_rmse_m": geo.get("rmse_m"),
                "independent_error_m": geo.get("checkpoint_rmse_3d"),
                "passed": None,
                "reason": "Requires independent checkpoints; GPS fit residual is not ground truth",
            },
            "coverage": {
                "target": "Full visible-scene coverage",
                "registered_frames": len(reconstruction["poses"]),
                "selected_frames": len(info["frames"]),
                "registered_frames_pct": round(100 * len(reconstruction["poses"]) / len(info["frames"]), 2),
                "surface_coverage_pct": None,
                "passed": None,
            },
        },
        "metric_state": geo.get("metric_state", "RELATIVE"),
        "reprojection_rmse_px": reconstruction["reprojection_rmse_px"],
        "alignment": clean(geo),
        "preprocessing": {k: v for k, v in info.items() if k != "frames"},
        "sfm": sfm_report,
        "dense": dense_report,
        "mesh": mesh_report,
        "semantics": semantic_report,
        "exports": export_report,
        "stages": stages,
        "sub_stages": sub_stages,
        "warnings": warnings,
        "confidence": {
            "kind": "evidence indicators, not a calibrated probability",
            "registered_fraction": len(reconstruction["poses"]) / max(1, len(info["frames"])),
            "independent_accuracy_validated": False,
        },
    }
    reports_dir = out / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Move other reports into reports_dir (optional cleanup)
    for rep in ["cv_quality_report.json", "cv_quality_report.txt", "sfm_report.json", "sfm_report.txt"]:
        if (out / rep).exists():
            shutil.move(str(out / rep), str(reports_dir / rep))

    (out / "mission_report.json").write_text(json.dumps(clean(report), indent=2, allow_nan=False))
    lines = [
        "AERORECON SCENE REPORT",
        str(meta["mission_name"]),
        f"Processing: {elapsed:.2f} s",
        f"Metric state: {report['metric_state']}",
        f"Registered cameras: {len(reconstruction['poses'])}/{len(info['frames'])}",
        f"GPS alignment residual: {geo.get('rmse_m', 'N/A')} m (NOT independent accuracy)",
        "",
        *warnings,
    ]
    (out / "mission_report.txt").write_text("\n".join(lines))
    progress(99, "Packaging model, texture dependencies and reports")
    deliverables_dir = work / f"mission_{meta.get('mission_name', 'unknown')}_deliverables"
    deliverables_dir.mkdir(exist_ok=True)
    for folder in ["mesh", "pointcloud", "geospatial", "reports"]:
        if (out / folder).exists():
            shutil.copytree(out / folder, deliverables_dir / folder, dirs_exist_ok=True)
    for file in ["manifest.json", "mission_report.json", "mission_report.txt"]:
        if (out / file).exists():
            shutil.copy2(out / file, deliverables_dir / file)

    with timed("zip_packaging"):
        shutil.make_archive(str(work / "artifacts"), "zip", deliverables_dir)
    progress(100, "Completed with reported limitations")
    return clean(report)
