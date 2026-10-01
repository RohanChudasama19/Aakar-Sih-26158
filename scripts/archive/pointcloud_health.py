import open3d as o3d
import numpy as np
import scipy.spatial
from pathlib import Path

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_6 = work_dir / "dense_full_ref2/fused.ply"
ply_10 = work_dir / "dense_10_source_full/fused.ply"

def analyze_cloud(ply_path):
    print(f"\nAnalyzing {ply_path.name}...")
    pc = o3d.io.read_point_cloud(str(ply_path))
    xyz = np.asarray(pc.points)
    
    valid = np.isfinite(xyz).all(axis=1)
    xyz = xyz[valid]
    
    bbox_min, bbox_max = xyz.min(axis=0), xyz.max(axis=0)
    extent = float(np.linalg.norm(bbox_max - bbox_min))
    
    _, unique_idx = np.unique(np.round(xyz, 5), axis=0, return_index=True)
    duplicate_frac = 1.0 - (len(unique_idx) / len(xyz))
    print(f"Total points: {len(xyz)}")
    print(f"Duplicate (10um) points: {duplicate_frac:.3%} ({len(xyz) - len(unique_idx)})")
    
    tree = scipy.spatial.cKDTree(xyz)
    nn_distances, _ = tree.query(xyz, k=2)
    p25, p50, p75, p95 = np.percentile(nn_distances[:, 1], [25, 50, 75, 95])
    print(f"NN Percentiles: 25th: {p25:.4f}, Median: {p50:.4f}, 75th: {p75:.4f}, 95th: {p95:.4f}")
    
    print(f"Has normals: {pc.has_normals()}")
    if pc.has_normals():
        normals = np.asarray(pc.normals)
        normals = normals[valid]
        mags = np.linalg.norm(normals, axis=1)
        valid_normals = np.isfinite(normals).all(axis=1) & (mags > 1e-5)
        print(f"Valid normals: {np.mean(valid_normals):.3%}")

analyze_cloud(ply_6)
analyze_cloud(ply_10)
