import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import trimesh
from scipy.spatial import cKDTree


class ValidationStatus(str, Enum):
    VERIFIED_REAL_DATA = "VERIFIED_REAL_DATA"
    IMPLEMENTED_SYNTHETICALLY_VERIFIED = "IMPLEMENTED_SYNTHETICALLY_VERIFIED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    INSUFFICIENT_OVERLAP = "INSUFFICIENT_OVERLAP"
    TEMPORAL_MISMATCH = "TEMPORAL_MISMATCH"
    INVALID_REFERENCE_FRAME = "INVALID_REFERENCE_FRAME"


@dataclass
class ReferenceMetadata:
    sensor: str = "UNKNOWN"
    reference_type: str = "UNKNOWN"
    nominal_density_pts_m2: float = 0.0
    stated_accuracy_m: float = 0.0
    crs: str = "UNKNOWN"
    vertical_datum: str = "UNKNOWN"
    acquisition_date: str = "UNKNOWN"
    temporal_scene_change_risk: bool = False


def voxel_downsample(points: np.ndarray, voxel_size: float, seed: int = 42) -> np.ndarray:
    if len(points) == 0:
        return points

    # Deterministic voxel downsampling
    rng = np.random.default_rng(seed)
    voxels = np.floor(points / voxel_size).astype(np.int32)

    # We want one random point per voxel to preserve some original locations
    # For speed and determinism, we can sort by voxel and pick first, but a random permutation first is better
    perm = rng.permutation(len(points))
    points_shuffled = points[perm]
    voxels_shuffled = voxels[perm]

    # Find unique voxels
    _, unique_indices = np.unique(voxels_shuffled, axis=0, return_index=True)
    return points_shuffled[unique_indices]


def compute_distances_c2c(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    if len(src) == 0 or len(dst) == 0:
        return np.array([])
    tree = cKDTree(dst)
    dists, _ = tree.query(src, k=1)
    return dists


def compute_c2m(src: np.ndarray, mesh: trimesh.Trimesh) -> np.ndarray:
    if len(src) == 0 or len(mesh.faces) == 0:
        return np.array([])
    closest, dists, _ = trimesh.proximity.closest_point(mesh, src)
    return dists


def filter_by_bounds(
    points: np.ndarray, bounds_min: np.ndarray, bounds_max: np.ndarray, margin: float = 0.0
) -> np.ndarray:
    if len(points) == 0:
        return points

    b_min = bounds_min + margin
    b_max = bounds_max - margin

    mask = np.all((points >= b_min) & (points <= b_max), axis=1)
    return points[mask]


def compute_statistics(dists: np.ndarray) -> Dict[str, float]:
    if len(dists) == 0:
        return {}

    return {
        "count": len(dists),
        "mean_distance_3d": float(np.mean(dists)),
        "median_distance_3d": float(np.median(dists)),
        "RMSE_3D": float(np.sqrt(np.mean(dists**2))),
        "P68": float(np.percentile(dists, 68)),
        "P90": float(np.percentile(dists, 90)),
        "P95": float(np.percentile(dists, 95)),
        "P99": float(np.percentile(dists, 99)),
        "max": float(np.max(dists)),
    }


def compute_coverage(dists: np.ndarray, thresholds: List[float]) -> Dict[str, float]:
    if len(dists) == 0:
        return {f"coverage_{t}m": 0.0 for t in thresholds}
    return {f"coverage_{t}m": float(np.sum(dists <= t) / len(dists)) for t in thresholds}


def evaluate_surface_accuracy(
    recon_pts: np.ndarray,
    ref_pts: Optional[np.ndarray],
    ref_mesh: Optional[trimesh.Trimesh],
    metadata: ReferenceMetadata,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
    margin: float = 0.0,
    voxel_size: float = 0.05,
    seed: int = 42,
    thresholds: List[float] = [0.10, 0.25, 0.50, 1.00],
    is_same_vertical_datum: bool = True,
) -> Dict[str, Any]:

    warnings_list = []

    if metadata.crs == "UNKNOWN" or metadata.vertical_datum == "UNKNOWN":
        warnings_list.append("INVALID_REFERENCE_FRAME: Frame or datum is unknown.")
        return {"status": ValidationStatus.INVALID_REFERENCE_FRAME.value, "warnings": warnings_list}

    if metadata.temporal_scene_change_risk:
        warnings_list.append("TEMPORAL_SCENE_CHANGE_RISK")

    # Crop to mission bounds
    recon_cropped = filter_by_bounds(recon_pts, bounds_min, bounds_max, margin)

    ref_cropped = None
    if ref_pts is not None:
        ref_cropped = filter_by_bounds(ref_pts, bounds_min, bounds_max, margin)

    # Sampling
    recon_sampled = voxel_downsample(recon_cropped, voxel_size, seed)

    ref_sampled = None
    if ref_cropped is not None:
        ref_sampled = voxel_downsample(ref_cropped, voxel_size, seed)

    if len(recon_sampled) == 0:
        warnings_list.append("INSUFFICIENT_OVERLAP: No reconstruction points in bounding box.")
        return {"status": ValidationStatus.INSUFFICIENT_OVERLAP.value, "warnings": warnings_list}

    res: Dict[str, Any] = {
        "status": ValidationStatus.IMPLEMENTED_SYNTHETICALLY_VERIFIED.value,
        "metadata": asdict(metadata),
        "sampling": {
            "voxel_size": voxel_size,
            "seed": seed,
            "recon_sample_count": len(recon_sampled),
            "ref_sample_count": len(ref_sampled) if ref_sampled is not None else 0,
        },
        "accuracy_reconstruction_to_reference": {},
        "completeness_reference_to_reconstruction": {},
        "warnings": warnings_list,
        "mode": [],
    }

    if ref_mesh is not None:
        # C2M
        res["mode"].append("C2M")
        acc_dists = compute_c2m(recon_sampled, ref_mesh)
        res["accuracy_reconstruction_to_reference"].update(compute_statistics(acc_dists))
        res["accuracy_reconstruction_to_reference"]["RAW_metrics"] = True

        # Note: Completeness (M2C) is harder without sampling the mesh.
        # We can sample the mesh to points for completeness.
        ref_mesh_pts = ref_mesh.sample(len(recon_sampled))
        ref_mesh_pts_cropped = filter_by_bounds(ref_mesh_pts, bounds_min, bounds_max, margin)
        if len(ref_mesh_pts_cropped) > 0:
            comp_dists = compute_distances_c2c(ref_mesh_pts_cropped, recon_sampled)
            res["completeness_reference_to_reconstruction"].update(compute_coverage(comp_dists, thresholds))

    elif ref_sampled is not None and len(ref_sampled) > 0:
        # C2C
        res["mode"].append("C2C")

        # Accuracy: Recon -> Ref
        acc_dists = compute_distances_c2c(recon_sampled, ref_sampled)
        res["accuracy_reconstruction_to_reference"].update(compute_statistics(acc_dists))
        res["accuracy_reconstruction_to_reference"]["RAW_metrics"] = True

        # Vertical / Horizontal separate error if same vertical datum
        if is_same_vertical_datum:
            # Re-query to get nearest indices
            tree = cKDTree(ref_sampled)
            dists, indices = tree.query(recon_sampled, k=1)
            ref_nearest = ref_sampled[indices]

            z_err = recon_sampled[:, 2] - ref_nearest[:, 2]
            xy_err = np.linalg.norm(recon_sampled[:, :2] - ref_nearest[:, :2], axis=1)

            res["accuracy_reconstruction_to_reference"]["RMSE_Z"] = float(np.sqrt(np.mean(z_err**2)))
            res["accuracy_reconstruction_to_reference"]["MAE_Z"] = float(np.mean(np.abs(z_err)))
            res["accuracy_reconstruction_to_reference"]["RMSE_XY"] = float(np.sqrt(np.mean(xy_err**2)))

        # Completeness: Ref -> Recon
        comp_dists = compute_distances_c2c(ref_sampled, recon_sampled)
        res["completeness_reference_to_reconstruction"].update(compute_coverage(comp_dists, thresholds))

    else:
        warnings_list.append("INSUFFICIENT_OVERLAP: No reference points in bounding box.")
        res["status"] = ValidationStatus.INSUFFICIENT_OVERLAP.value

    return res


def save_report(report: Dict[str, Any], output_path: Path):
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
