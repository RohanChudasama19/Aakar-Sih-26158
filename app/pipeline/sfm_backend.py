import logging
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from scipy.spatial.transform import Rotation

from ..camera import CalibrationState, CameraModel
from . import colmap, sfm

logger = logging.getLogger(__name__)


@dataclass
class SfMProfile:
    name: str
    max_frames: int
    matching_overlap: int
    mapper_strategy: str  # INCREMENTAL, GLOBAL, HIERARCHICAL


def determine_profile(
    info: Dict[str, Any], readiness_report: Optional[Dict] = None, options: Optional[Dict] = None
) -> SfMProfile:
    num_frames = len(info.get("frames", []))
    options = options or {}

    if options.get("profile") == "FAST_QUALITY":
        from .profiles import FAST_QUALITY_V1

        return SfMProfile(
            "FAST_QUALITY",
            FAST_QUALITY_V1["sfm_budget"],
            FAST_QUALITY_V1["matching_settings"]["overlap"],
            "GLOBAL_FAST",
        )

    # Simple duration/frame count heuristic
    if num_frames < 200:
        return SfMProfile("SMALL", 200, 8, "INCREMENTAL")
    elif num_frames < 800:
        return SfMProfile("MEDIUM", 800, 15, "INCREMENTAL")
    elif num_frames < 2000:
        return SfMProfile("LARGE", 2000, 25, "GLOBAL")
    else:
        return SfMProfile("VERY_LARGE", 5000, 35, "HIERARCHICAL")


class SfMBackend(ABC):
    @abstractmethod
    def run(
        self, frames_dir: Path, info: Dict[str, Any], camera: CameraModel, progress_callback, options: Dict = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def check_capabilities(self) -> Dict[str, Any]:
        pass


class COLMAPBackend(SfMBackend):
    def __init__(self):
        self.capabilities = self.check_capabilities()

    def check_capabilities(self) -> Dict[str, Any]:
        caps = {
            "available": False,
            "version": None,
            "cuda_available": False,
            "caspar_available": False,
        }
        from .colmap import get_colmap_env, resolve_colmap_executable

        colmap_exe = resolve_colmap_executable()
        if not colmap_exe:
            return caps
        try:
            env = get_colmap_env()
            result = subprocess.run([colmap_exe, "help"], capture_output=True, text=True, timeout=30, env=env)
            if colmap_exe and result.returncode == 0:
                caps["available"] = True
                if "CUDA" in result.stdout:
                    caps["cuda_available"] = True

                # Check for Caspar BA
                ba_help = subprocess.run(
                    [colmap_exe, "bundle_adjuster", "--help"], capture_output=True, text=True, timeout=30, env=env
                )
                if "--BundleAdjustment.backend" in ba_help.stdout and "CASPAR" in ba_help.stdout:
                    caps["caspar_available"] = True

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return caps

    def run(
        self, frames_dir: Path, info: Dict[str, Any], camera: CameraModel, progress_callback, options: Dict = None
    ) -> Dict[str, Any]:
        if not self.capabilities["available"]:
            raise RuntimeError("COLMAP is not available.")

        work = frames_dir.parent
        db = work / "colmap.db"
        models = work / "sparse"
        models.mkdir(exist_ok=True)

        start_time = time.monotonic()

        profile = determine_profile(info)

        options = options or {}
        profile = determine_profile(info, None, options)

        # 1. Feature Extraction
        progress_callback(22, f"COLMAP feature extraction ({profile.name})")

        from .colmap import resolve_colmap_executable

        colmap_exe = resolve_colmap_executable() or r"C:\Tools\COLMAP\COLMAP.bat"

        extractor_cmd = [
            colmap_exe,
            "feature_extractor",
            "--database_path",
            db,
            "--image_path",
            frames_dir,
            "--ImageReader.single_camera",
            "1",
            "--ImageReader.camera_model",
            camera.model_type.value,
            "--ImageReader.camera_params",
            camera.to_colmap(),
            "--FeatureExtraction.use_gpu",
            "1" if self.capabilities["cuda_available"] else "0",
        ]

        if profile.name == "GLOBAL_FAST" or options.get("profile") == "FAST_QUALITY":
            extractor_cmd.extend(["--SiftExtraction.max_num_features", "4096"])

        mask_dir = work / "masks"
        if mask_dir.exists() and any(mask_dir.iterdir()):
            extractor_cmd.extend(["--ImageReader.mask_path", mask_dir])

        if profile.name == "FAST_QUALITY":
            pass

        colmap.run(extractor_cmd, work)

        # 2. Matching
        progress_callback(26, f"COLMAP {profile.name} sequential matching")

        # UAV-aware hybrid matching (sequential + spatial) can be emulated via sequential overlap for now,
        # but in production we might run spatial_matcher or vocab_tree_matcher for very large datasets
        colmap.run(
            [
                colmap_exe,
                "sequential_matcher",
                "--database_path",
                db,
                "--SequentialMatching.overlap",
                str(profile.matching_overlap),
                "--SequentialMatching.quadratic_overlap",
                "1",
                "--SequentialMatching.loop_detection",
                "0" if profile.name == "FAST_QUALITY" else "1",
                "--FeatureMatching.use_gpu",
                "1" if self.capabilities["cuda_available"] else "0",
            ],
            work,
        )

        # 3. Mapping
        progress_callback(32, f"COLMAP {profile.mapper_strategy} mapping")

        refine_focal = "0"
        refine_extra = "0"
        if camera.state == CalibrationState.ESTIMATED:
            refine_focal = "1"
            refine_extra = "1"

        if profile.mapper_strategy == "GLOBAL_FAST":
            progress_callback(32, "COLMAP GLOBAL_FAST view_graph_calibrator")
            colmap.run([colmap_exe, "view_graph_calibrator", "--database_path", db], work)

            mapper_cmd = [
                colmap_exe,
                "global_mapper",
                "--database_path",
                db,
                "--image_path",
                frames_dir,
                "--output_path",
                models,
                "--GlobalMapper.ba_num_iterations",
                "3",
                "--GlobalMapper.ba_refine_focal_length",
                refine_focal,
                "--GlobalMapper.ba_refine_principal_point",
                "0",
                "--GlobalMapper.ba_refine_extra_params",
                refine_extra,
                "--GlobalMapper.ba_ceres_max_num_iterations",
                "30",
                "--GlobalMapper.skip_retriangulation",
                "1",
            ]
        elif profile.mapper_strategy == "HIERARCHICAL":
            mapper_cmd = [
                colmap_exe,
                "hierarchical_mapper",
                "--database_path",
                db,
                "--image_path",
                frames_dir,
                "--output_path",
                models,
            ]
        else:
            mapper_cmd = [
                colmap_exe,
                "mapper",
                "--database_path",
                db,
                "--image_path",
                frames_dir,
                "--output_path",
                models,
                "--Mapper.ba_refine_focal_length",
                refine_focal,
                "--Mapper.ba_refine_principal_point",
                "0",
                "--Mapper.ba_refine_extra_params",
                refine_extra,
            ]
            if profile.name == "FAST":
                mapper_cmd.extend(
                    [
                        "--Mapper.ba_global_max_num_iterations",
                        "30",
                        "--Mapper.ba_local_max_num_iterations",
                        "20",
                        "--Mapper.ba_global_max_refinements",
                        "2",
                    ]
                )

        if self.capabilities["caspar_available"]:
            if profile.mapper_strategy != "GLOBAL_FAST":
                mapper_cmd.extend(["--Mapper.ba_backend", "CASPAR"])

        # Execute Mapping
        colmap.run(mapper_cmd, work)

        # 4. Model Selection and Conversion
        progress_callback(40, "COLMAP model conversion and metric parsing")
        choices = list(models.glob("*/images.bin"))
        if not choices:
            raise ValueError("COLMAP could not register cameras; see colmap.log")

        # Choose model with most registered images
        best_model_path = max(choices, key=lambda p: p.stat().st_size).parent

        textdir = work / "sparse_txt"
        textdir.mkdir(exist_ok=True)
        colmap.run(
            [
                r"C:\Tools\COLMAP\COLMAP.bat",
                "model_converter",
                "--input_path",
                best_model_path,
                "--output_path",
                textdir,
                "--output_type",
                "TXT",
            ],
            work,
        )

        # Parse Poses
        poses = {}
        lines = (textdir / "images.txt").read_text().splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line or line.startswith("#"):
                continue
            values = line.split()
            qw, qx, qy, qz = map(float, values[1:5])
            rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
            name = values[9]
            idx = next((n for n, f in enumerate(info["frames"]) if f["name"] == name), None)
            if idx is not None:
                poses[idx] = np.c_[rot, np.array(values[5:8], float)]
            i += 1

        # Parse Points
        points = []
        colors = []
        errors = []
        track_lengths = []
        for line in (textdir / "points3D.txt").read_text().splitlines():
            if line and not line.startswith("#"):
                v = line.split()
                points.append(list(map(float, v[1:4])))
                colors.append(list(map(int, v[4:7])))
                errors.append(float(v[7]))
                # Track length is number of observing cameras (elements after error are pairs of [image_id, point2D_idx])
                track_lengths.append(len(v[8:]) // 2)

        if len(poses) < 3 or len(points) < 25:
            raise ValueError("COLMAP model has insufficient registered geometry")

        errors_np = np.array(errors)
        track_np = np.array(track_lengths)

        report = {
            "backend": "COLMAP_CUDA" if self.capabilities["cuda_available"] else "COLMAP_CPU",
            "mapper_strategy": profile.mapper_strategy,
            "camera_model": camera.model_type.value,
            "input_frames": len(info["frames"]),
            "registered_cameras": len(poses),
            "registration_ratio": len(poses) / max(1, len(info["frames"])),
            "sparse_point_count": len(points),
            "mean_reprojection_error_px": float(np.mean(errors_np)),
            "median_reprojection_error_px": float(np.median(errors_np)),
            "p95_reprojection_error_px": float(np.percentile(errors_np, 95)),
            "mean_track_length": float(np.mean(track_np)),
            "median_track_length": float(np.median(track_np)),
            "ba_backend": "CASPAR" if self.capabilities["caspar_available"] else "CERES",
            "sfm_runtime_sec": time.monotonic() - start_time,
        }

        return {
            "points": np.array(points),
            "colors": np.array(colors, np.uint8),
            "poses": poses,
            "model_path": str(best_model_path),
            "reprojection_rmse_px": float(np.sqrt(np.mean(np.square(errors_np)))),
            "engine": report["backend"],
            "sfm_report": report,
        }


class CPUFallbackBackend(SfMBackend):
    def check_capabilities(self) -> Dict[str, Any]:
        return {"available": True, "cuda_available": False, "caspar_available": False}

    def run(
        self, frames_dir: Path, info: Dict[str, Any], camera: CameraModel, progress_callback, options: Dict = None
    ) -> Dict[str, Any]:
        start_time = time.monotonic()
        determine_profile(info)

        try:
            # Re-use existing sfm.py logic, but adapt to new report structure
            res = sfm.reconstruct(frames_dir, info, camera, progress_callback)

            report = {
                "backend": "OPENCV_INCREMENTAL",
                "mapper_strategy": "INCREMENTAL",
                "camera_model": camera.model_type.value,
                "input_frames": len(info["frames"]),
                "registered_cameras": len(res["poses"]),
                "registration_ratio": len(res["poses"]) / max(1, len(info["frames"])),
                "sparse_point_count": len(res["points"]),
                "mean_reprojection_error_px": res["reprojection_rmse_px"],
                "median_reprojection_error_px": res["reprojection_rmse_px"],
                "p95_reprojection_error_px": res["reprojection_rmse_px"],
                "mean_track_length": 2.0,  # Approximate for fallback
                "median_track_length": 2.0,
                "ba_backend": "NONE",
                "sfm_runtime_sec": time.monotonic() - start_time,
                "fallback_reason": "COLMAP unavailable or overridden",
            }
            res["sfm_report"] = report
            return res

        except Exception as e:
            raise RuntimeError(f"CPU Fallback SfM failed: {e}")


def execute_sfm(
    frames_dir: Path,
    info: Dict[str, Any],
    camera: CameraModel,
    progress_callback,
    force_cpu: bool = False,
    options: Dict = None,
) -> Dict[str, Any]:
    options = options or {}
    colmap_backend = COLMAPBackend()

    if not force_cpu:
        if not colmap_backend.capabilities["available"]:
            raise RuntimeError(
                "CRITICAL ERROR: colmap.exe is missing from your computer! Your external D: drive might be unplugged. The system cannot run the GPU engine."
            )
        try:
            return colmap_backend.run(frames_dir, info, camera, progress_callback, options)
        except Exception as e:
            raise RuntimeError(f"COLMAP backend failed: {e}")

    cpu_backend = CPUFallbackBackend()
    return cpu_backend.run(frames_dir, info, camera, progress_callback, options)
