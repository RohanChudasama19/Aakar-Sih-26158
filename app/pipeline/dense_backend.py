"""COLMAP PatchMatch dense reconstruction backend with per-subprocess timing."""

import shutil
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from .profiles import FAST_QUALITY_V1


class DenseBackend(ABC):
    @abstractmethod
    def run(
        self,
        sfm: Dict[str, Any],
        k: Any,
        directory: Path,
        work_dir: Path,
        options: Dict[str, Any],
        geo: Dict[str, Any],
        progress: Any,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        pass


class CPUFallbackDenseBackend(DenseBackend):
    def __init__(self, fallback_reason: str | None = None):
        self.fallback_reason = fallback_reason

    def run(self, sfm, k, directory, work_dir, options, geo, progress):
        from .dense import cpu_densify

        p, c, r = cpu_densify(sfm, k, directory, progress, max_pairs=options.get("max_pairs", 12))
        r["raw_points"] = len(p)
        r["backend"] = "CPU_FALLBACK"
        if self.fallback_reason:
            r["status"] = "DENSE_DEGRADED"
            r["fallback_reason"] = self.fallback_reason
        r["dense_support_confidence"] = {
            "formula": "Bidirectional Optical Flow constraint < 0.6px",
            "median_support": "2 views (stereo pairs only in CPU fallback)",
        }
        return p, c, r


def determine_dense_profile(num_frames: int, options: Dict[str, Any]) -> Dict[str, Any]:
    if options.get("profile") == "FAST_QUALITY":
        profile = FAST_QUALITY_V1["dense_settings"].copy()
        profile["name"] = "FAST_QUALITY"
        profile["min_num_pixels"] = FAST_QUALITY_V1["fusion_settings"]["min_num_pixels"]
        return profile

    if num_frames < 50:
        return {
            "name": "QUALITY",
            "max_image_size": 2048,
            "window_radius": 6,
            "window_step": 1,
            "num_iterations": 7,
            "geom_consistency": True,
            "num_matching_views": 10,
            "min_num_pixels": 4,
        }
    elif num_frames <= 200:
        return {
            "name": "BALANCED",
            "max_image_size": 1600,
            "window_radius": 5,
            "window_step": 1,
            "num_iterations": 5,
            "geom_consistency": True,
            "num_matching_views": 8,
            "min_num_pixels": 4,
        }
    else:
        return {
            "name": "FAST",
            "max_image_size": 1024,
            "window_radius": 4,
            "window_step": 2,
            "num_iterations": 3,
            "geom_consistency": False,
            "num_matching_views": 7,
            "min_num_pixels": 4,
        }


class ColmapPatchMatchBackend(DenseBackend):
    def run(self, sfm, k, directory, work_dir, options, geo, progress):
        import subprocess

        from .colmap import get_colmap_env, resolve_colmap_executable

        colmap_exe = resolve_colmap_executable()
        env = get_colmap_env()

        if not colmap_exe:
            raise RuntimeError("COLMAP not found in PATH")

        colmap_model_path = Path(sfm.get("model_path", work_dir / "sparse" / "0"))
        if not (colmap_model_path / "cameras.bin").exists() and not (colmap_model_path / "cameras.txt").exists():
            progress(50, "COLMAP sparse workspace not found. Falling back to CPU.")
            return CPUFallbackDenseBackend(
                fallback_reason="COLMAP sparse workspace not found or all profiles failed"
            ).run(sfm, k, directory, work_dir, options, geo, progress)

        primary_profile = determine_dense_profile(len(sfm["poses"]), options)
        profiles = [primary_profile]
        if primary_profile["name"] != "FAST":
            profiles.append(
                {
                    "name": "FAST",
                    "max_image_size": 1600,
                    "window_radius": 4,
                    "window_step": 2,
                    "num_iterations": 3,
                    "geom_consistency": True,
                    "num_matching_views": 6,
                }
            )

        for attempt, profile in enumerate(profiles):
            dense_dir = work_dir / f"dense_{profile['name'].lower()}"
            dense_dir.mkdir(parents=True, exist_ok=True)

            try:
                # 1. Undistort
                progress(45, f"Running COLMAP image_undistorter ({profile['name']} profile)")
                cmd_undistort = [
                    colmap_exe,
                    "image_undistorter",
                    "--image_path",
                    str(directory),
                    "--input_path",
                    str(colmap_model_path),
                    "--output_path",
                    str(dense_dir),
                    "--output_type",
                    "COLMAP",
                    "--max_image_size",
                    str(profile["max_image_size"]),
                ]
                t_u0 = time.monotonic()
                subprocess.run(cmd_undistort, check=True, capture_output=True, text=True, env=env)
                t_undistort = round(time.monotonic() - t_u0, 1)

                # 4. ADAPTIVE DENSE REFERENCE SELECTION
                try:
                    target_refs = (
                        FAST_QUALITY_V1["dense_settings"]["reference_target"] if profile["name"] == "FAST_QUALITY" else 140
                    )
                    stereo_dir = dense_dir / "stereo"
                    stereo_dir.mkdir(exist_ok=True, parents=True)

                    images_dir = dense_dir / "images"
                    image_files = sorted([f.name for f in images_dir.iterdir() if f.is_file()])

                    if len(image_files) > target_refs:
                        step = len(image_files) / max(1, target_refs)
                        ref_indices = {int(i * step) for i in range(target_refs)}

                        cfg_lines = []
                        for i, img in enumerate(image_files):
                            if i in ref_indices:
                                cfg_lines.append(f"{img}")
                                cfg_lines.append(f"__auto__, {profile.get('num_matching_views', 10)}")

                        (stereo_dir / "patch-match.cfg").write_text("\n".join(cfg_lines))
                        print(f"Generated patch-match.cfg with {target_refs} reference views (source views available: {len(image_files)})")
                except Exception as e:
                    print("Error generating patch-match.cfg:", e)

                # 2. PatchMatch Stereo
                progress(60, f"Running COLMAP patch_match_stereo ({profile['name']} profile)")
                cmd_patchmatch = [
                    colmap_exe,
                    "patch_match_stereo",
                    "--workspace_path",
                    str(dense_dir),
                    "--workspace_format",
                    "COLMAP",
                    "--PatchMatchStereo.max_image_size",
                    str(profile["max_image_size"]),
                    "--PatchMatchStereo.geom_consistency",
                    "1" if profile["geom_consistency"] else "0",
                    "--PatchMatchStereo.window_radius",
                    str(profile["window_radius"]),
                    "--PatchMatchStereo.window_step",
                    str(profile["window_step"]),
                    "--PatchMatchStereo.num_iterations",
                    str(profile["num_iterations"]),
                ]
                cmd_patchmatch.extend(["--PatchMatchStereo.allow_missing_files", "1"])
                t_pm0 = time.monotonic()
                r_pm = subprocess.run(cmd_patchmatch, check=True, capture_output=True, text=True, env=env)
                with open(dense_dir / "pm_log.txt", "w") as f:
                    f.write(r_pm.stdout + "\n" + r_pm.stderr)
                t_patchmatch = round(time.monotonic() - t_pm0, 1)

                # 3. Stereo Fusion
                progress(85, f"Running COLMAP stereo_fusion ({profile['name']} profile)")
                cmd_fusion = [
                    colmap_exe,
                    "stereo_fusion",
                    "--workspace_path",
                    str(dense_dir),
                    "--workspace_format",
                    "COLMAP",
                    "--input_type",
                    "geometric" if profile["geom_consistency"] else "photometric",
                    "--output_path",
                    str(dense_dir / "fused.ply"),
                    "--StereoFusion.min_num_pixels",
                    str(profile.get("min_num_pixels", 5)),
                ]
                t_f0 = time.monotonic()
                r_fusion = subprocess.run(cmd_fusion, check=True, capture_output=True, text=True, env=env)
                with open(dense_dir / "fusion_log.txt", "w") as f:
                    f.write(r_fusion.stdout + "\n" + r_fusion.stderr)
                t_fusion = round(time.monotonic() - t_f0, 1)

                if (dense_dir / "fused.ply").exists():
                    import trimesh

                    pc = trimesh.load(str(dense_dir / "fused.ply"))
                    points = np.array(pc.vertices)
                    colors = np.array(pc.visual.vertex_colors[:, :3])
                    depth_maps = (
                        list((dense_dir / "stereo" / "depth_maps").glob("*.bin"))
                        if (dense_dir / "stereo" / "depth_maps").exists()
                        else []
                    )
                    normal_maps = (
                        list((dense_dir / "stereo" / "normal_maps").glob("*.bin"))
                        if (dense_dir / "stereo" / "normal_maps").exists()
                        else []
                    )

                    support_status = "INSUFFICIENT"
                    if len(points) > 100000:
                        support_status = "GOOD"
                    elif len(points) > len(sfm["poses"]) * 50:
                        support_status = "MARGINAL"

                    return (
                        points,
                        colors,
                        {
                            "backend": "COLMAP_PATCHMATCH",
                            "colmap_exe": colmap_exe,
                            "profile": profile["name"],
                            "geom_consistency": profile["geom_consistency"],
                            "raw_points": len(points),
                            "depth_maps_generated": len(depth_maps),
                            "normal_maps_generated": len(normal_maps),
                            "dense_support_confidence": {
                                "formula": "Number of consistent stereo views observing a point",
                                "median_support": "Preserved in COLMAP binary workspace (fused.ply header lacks per-point view count)",
                                "support_status": support_status,
                            },
                            "subprocess_timings": {
                                "undistort_s": t_undistort,
                                "patchmatch_s": t_patchmatch,
                                "fusion_s": t_fusion,
                            },
                        },
                    )

            except subprocess.CalledProcessError:
                progress(86, f"COLMAP {profile['name']} profile failed (possibly OOM).")
                if attempt == len(profiles) - 1:
                    progress(87, "All COLMAP profiles exhausted. Falling back to CPU.")
                    return CPUFallbackDenseBackend(
                        fallback_reason="COLMAP sparse workspace not found or all profiles failed"
                    ).run(sfm, k, directory, work_dir, options, geo, progress)

        return CPUFallbackDenseBackend(fallback_reason="COLMAP sparse workspace not found or all profiles failed").run(
            sfm, k, directory, work_dir, options, geo, progress
        )


def execute_dense(
    sfm: Dict[str, Any],
    k: Any,
    directory: Path,
    work_dir: Path,
    options: Dict[str, Any],
    geo: Dict[str, Any],
    progress: Any,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:

    # Disk Space Precheck
    try:
        total, used, free = shutil.disk_usage(str(work_dir))
        # Estimate: 50MB per frame for workspace
        required = len(sfm["poses"]) * 50 * 1024 * 1024
        if free < required:
            raise RuntimeError(
                f"Insufficient disk space for dense reconstruction. Required: {required / 1024**2:.1f} MB, Free: {free / 1024**2:.1f} MB"
            )
    except RuntimeError as e:
        raise e
    except Exception:
        pass

    # Simple check for CUDA/COLMAP
    from .colmap import resolve_colmap_executable

    colmap_exe = resolve_colmap_executable()
    import os

    has_colmap = bool(colmap_exe) and os.path.exists(colmap_exe)

    backend: DenseBackend
    if options.get("use_gpu", True):
        if not has_colmap:
            raise RuntimeError(
                "CRITICAL ERROR: colmap.exe is missing from your computer! The GPU engine cannot run without it."
            )
        backend = ColmapPatchMatchBackend()
    else:
        backend = CPUFallbackDenseBackend()
    points, colors, report = backend.run(sfm, k, directory, work_dir, options, geo, progress)
    if len(points) > 0:
        import open3d as o3d
        import trimesh

        trimesh.points.PointCloud(points, colors=colors).export(work_dir / "outputs" / "dense_raw.ply")

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors.astype(float) / 255.0)

        # Statistical outlier removal
        cl, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        filtered_points = np.asarray(cl.points)
        filtered_colors = (np.asarray(cl.colors) * 255.0).astype(np.uint8)

        report["filtered_points"] = len(filtered_points)
        report["removed_points"] = len(points) - len(filtered_points)
        return filtered_points, filtered_colors, report

    return points, colors, report
