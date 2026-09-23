"""COLMAP PatchMatch dense reconstruction backend with per-subprocess timing."""

import shutil
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np


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
    def run(self, sfm, k, directory, work_dir, options, geo, progress):
        from .dense import cpu_densify

        p, c, r = cpu_densify(sfm, k, directory, progress, max_pairs=options.get("max_pairs", 12))
        r["raw_points"] = len(p)
        r["backend"] = "CPU_FALLBACK"
        r["dense_support_confidence"] = {
            "formula": "Bidirectional Optical Flow constraint < 0.6px",
            "median_support": "2 views (stereo pairs only in CPU fallback)",
        }
        return p, c, r


def determine_dense_profile(num_frames: int, options: Dict[str, Any]) -> Dict[str, Any]:
    forced = options.get("force_profile")
    if forced == "FAST": num_frames = 250
    elif forced == "BALANCED": num_frames = 100
    elif forced == "QUALITY": num_frames = 10
    """Select PatchMatch profile based on frame count.

    Profiles target the RTX 3050 Laptop (4 GB VRAM, 2048 CUDA cores).
    num_matching_views caps the number of source images per reference to
    reduce VRAM pressure without significant quality loss for UAV sequences.

    QUALITY  (≤50 frames):  max_image_size=2048, window_radius=6, geom=True,  iters=7, src=10
    BALANCED (≤200 frames): max_image_size=1600, window_radius=5, geom=True,  iters=5, src=8
    FAST     (>200 frames): max_image_size=1024, window_radius=4, geom=False, iters=3, src=7
    """
    if num_frames > 200:
        return {
            "name": "FAST",
            "max_image_size": 1024,
            "window_radius": 4,
            "window_step": 2,
            "num_iterations": 3,
            "geom_consistency": False,
            "num_matching_views": 7,
        }
    elif num_frames > 50:
        return {
            "name": "BALANCED",
            "max_image_size": 1600,
            "window_radius": 5,
            "window_step": 1,
            "num_iterations": 5,
            "geom_consistency": True,
            "num_matching_views": 8,
        }
    else:
        return {
            "name": "QUALITY",
            "max_image_size": 2048,
            "window_radius": 6,
            "window_step": 1,
            "num_iterations": 7,
            "geom_consistency": True,
            "num_matching_views": 10,
        }


class ColmapPatchMatchBackend(DenseBackend):
    def run(self, sfm, k, directory, work_dir, options, geo, progress):
        import subprocess

        colmap_exe = shutil.which('colmap')
        import os
        env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}
        if colmap_exe and colmap_exe.lower().endswith('.bat'):
            script_path = os.path.dirname(colmap_exe)
            exe_path = os.path.join(script_path, 'bin', 'colmap.exe')
            if os.path.exists(exe_path):
                colmap_exe = exe_path
                env['PATH'] = os.path.join(script_path, 'bin') + os.pathsep + env.get('PATH', '')
                env['QT_PLUGIN_PATH'] = os.path.join(script_path, 'plugins') + os.pathsep + env.get('QT_PLUGIN_PATH', '')

        if not colmap_exe:
            raise RuntimeError("COLMAP not found in PATH")

        colmap_model_path = Path(sfm.get("model_path", work_dir / "sparse" / "0"))
        if not (colmap_model_path / "cameras.bin").exists() and not (colmap_model_path / "cameras.txt").exists():
            progress(50, "COLMAP sparse workspace not found. Falling back to CPU.")
            return CPUFallbackDenseBackend().run(sfm, k, directory, work_dir, options, geo, progress)

        primary_profile = determine_dense_profile(len(sfm["poses"]), options)
        profiles = [primary_profile]
        if primary_profile["name"] != "FAST":
            profiles.append(
                {
                    "name": "FAST",
                    "max_image_size": 1024,
                    "window_radius": 4,
                    "window_step": 2,
                    "num_iterations": 3,
                    "geom_consistency": False,
                    "num_matching_views": 7,
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
                    "true" if profile["geom_consistency"] else "false",
                    "--PatchMatchStereo.window_radius",
                    str(profile["window_radius"]),
                    "--PatchMatchStereo.window_step",
                    str(profile["window_step"]),
                    "--PatchMatchStereo.num_iterations",
                    str(profile["num_iterations"]),
                ]
                t_pm0 = time.monotonic()
                subprocess.run(cmd_patchmatch, check=True, capture_output=True, text=True, env=env)
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
                ]
                t_f0 = time.monotonic()
                subprocess.run(cmd_fusion, check=True, capture_output=True, text=True, env=env)
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

                    return (
                        points,
                        colors,
                        {
                            "backend": "COLMAP_PATCHMATCH",
                            "profile": profile["name"],
                            "geom_consistency": profile["geom_consistency"],
                            "raw_points": len(points),
                            "depth_maps_generated": len(depth_maps),
                            "normal_maps_generated": len(normal_maps),
                            "dense_support_confidence": {
                                "formula": "Number of consistent stereo views observing a point",
                                "median_support": "Preserved in COLMAP binary workspace (fused.ply header lacks per-point view count)",
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
                    return CPUFallbackDenseBackend().run(sfm, k, directory, work_dir, options, geo, progress)

        return CPUFallbackDenseBackend().run(sfm, k, directory, work_dir, options, geo, progress)


def execute_dense(
    sfm: Dict[str, Any],
    k: Any,
    directory: Path,
    work_dir: Path,
    options: Dict[str, Any],
    geo: Dict[str, Any],
    progress: Any,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    import shutil

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
    colmap_exe = shutil.which('colmap')
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

