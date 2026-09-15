import json
import platform
import shutil
import time
from pathlib import Path

import numpy as np

from ..schemas import intrinsics, metadata, telemetry
from . import dense, exports, georef, mesh, preprocess, readiness, semantic, sfm


class ReadinessBlockedError(Exception):
    def __init__(self, report):
        self.report = report
        super().__init__("Reconstruction blocked by readiness gate")


STAGES = {
    "A": "Ingest & preprocess",
    "B": "Pose estimation & GPS alignment",
    "C": "Dense reconstruction",
    "D": "Mesh extraction & texturing",
    "E": "Georeferencing & export",
    "F": "Semantic layer & scene report",
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

    info = preprocess.extract(video, work / "frames", opts, progress)

    k = intrinsics(meta, info["width"], info["height"], override)
    if abs(info["fps"] - float(meta["video_fps"])) > max(0.1, info["fps"] * 0.02):
        raise ValueError(
            "Flight metadata FPS differs from the decoded video; telemetry frame alignment would be unreliable"
        )
    if abs(info["duration_sec"] - float(meta["video_duration_sec"])) > max(1.0, info["duration_sec"] * 0.02):
        raise ValueError("Flight metadata duration differs from decoded video")
    from datetime import datetime

    start_utc = datetime.fromisoformat(meta["start_time_utc"].replace("Z", "+00:00")).timestamp()
    for sample in gps:
        if abs(sample["time"] - start_utc - sample["frame"] / info["fps"]) > max(0.25, 2 / info["fps"]):
            raise ValueError("GPS UTC/frame values are inconsistent with the video FPS and flight start time")
    stage("B", 20)
    if opts.get("engine") == "colmap":
        from . import colmap

        reconstruction = colmap.sparse(work / "frames", info, k, progress)
    else:
        reconstruction = sfm.reconstruct(work / "frames", info, k, progress)
    geo = georef.align(reconstruction, info, gps, input_dir)
    np.savez_compressed(work / "sparse.npz", points=reconstruction["points"], colors=reconstruction["colors"])
    (work / "poses.json").write_text(json.dumps(clean(reconstruction["poses"])))
    (work / "alignment.json").write_text(json.dumps(clean(geo), indent=2))
    stage("C", 43)
    if opts.get("engine") == "colmap":
        points, colors, dense_report = colmap.dense(reconstruction, work / "frames", progress)
    else:
        points, colors, dense_report = dense.densify(reconstruction, k, work / "originals", progress)
    if (input_dir / "depth.onnx").exists():
        from .depth import infer

        dense_report["custom_depth"] = infer(
            input_dir / "depth.onnx", reconstruction, k, work / "originals", out, progress
        )
    np.savez_compressed(work / "dense.npz", points=points, colors=colors)
    stage("D", 62)
    surface, mesh_report = mesh.build_mesh(points, colors, geo, reconstruction, k, work / "originals")
    stage("E", 78)
    export_report = exports.export_all(surface, points, colors, geo, out)
    stage("F", 93)
    semantic_report = semantic.classify(points, colors, geo, surface, out)
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
    if any("unavailable" in s for s in export_report.values()):
        warnings.append("Some exports are unavailable; consult exports.json.")
    report = {
        "application": "AeroRecon",
        "build_tier": "reduced_fidelity_reference_implementation",
        "mission": meta["mission_name"],
        "synthetic_input": bool(meta.get("synthetic", False)),
        "status": "completed_with_limitations",
        "processing_time_sec": round(elapsed, 3),
        "video_duration_sec": info["duration_sec"],
        "engine": reconstruction["engine"],
        "hardware": {
            "cpu": platform.processor() or platform.machine(),
            "gpu_assumption_for_target": "RTX 4090-class, 24 GB VRAM",
            "benchmark_verified": False,
        },
        "targets": {
            "processing_time": {
                "target": "< 15 min for a 10-min video",
                "measured_sec": round(elapsed, 3),
                "ten_minute_benchmark_passed": None,
                "reason": "Only this input was timed; no extrapolation to 10 minutes",
            },
            "spatial_accuracy": {
                "target": "≤ 1 m",
                "gps_alignment_rmse_m": geo["rmse_m"],
                "independent_error_m": None,
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
        "metric_state": "GPS_ALIGNED_UNVERIFIED" if geo["valid"] else "RELATIVE_ONLY",
        "reprojection_rmse_px": reconstruction["reprojection_rmse_px"],
        "alignment": clean(geo),
        "preprocessing": {k: v for k, v in info.items() if k != "frames"},
        "dense": dense_report,
        "mesh": mesh_report,
        "semantics": semantic_report,
        "exports": export_report,
        "stages": stages,
        "warnings": warnings,
        "confidence": {
            "kind": "evidence indicators, not a calibrated probability",
            "registered_fraction": len(reconstruction["poses"]) / len(info["frames"]),
            "independent_accuracy_validated": False,
        },
    }
    (out / "report.json").write_text(json.dumps(clean(report), indent=2, allow_nan=False))
    lines = [
        "AERORECON SCENE REPORT",
        str(meta["mission_name"]),
        f"Processing: {elapsed:.2f} s",
        f"Metric state: {report['metric_state']}",
        f"Registered cameras: {len(reconstruction['poses'])}/{len(info['frames'])}",
        f"GPS fit residual: {geo['rmse_m']} m (NOT independent accuracy)",
        "",
        *warnings,
    ]
    (out / "report.txt").write_text("\n".join(lines))
    progress(99, "Packaging model, texture dependencies and reports")
    shutil.make_archive(str(work / "artifacts"), "zip", out)
    progress(100, "Completed with reported limitations")
    return clean(report)
