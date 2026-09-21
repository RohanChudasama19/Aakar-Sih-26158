import argparse
import json
import numpy as np
import trimesh
import laspy
from pathlib import Path
from app.pipeline.surface_validation import evaluate_surface_accuracy, ReferenceMetadata, save_report

def main():
    parser = argparse.ArgumentParser(description="Evaluate dense point cloud against LiDAR LAS reference.")
    parser.add_argument("--dense", required=True, type=str, help="Path to reconstructed dense PLY.")
    parser.add_argument("--ref", required=True, type=str, help="Path to reference LAS/LAZ.")
    parser.add_argument("--out", required=True, type=str, help="Output JSON report path.")
    parser.add_argument("--crs", default="UNKNOWN", type=str)
    parser.add_argument("--vdatum", default="UNKNOWN", type=str)
    args = parser.parse_args()

    print("Loading Dense PLY...")
    dense_mesh = trimesh.load(args.dense)
    recon_pts = np.array(dense_mesh.vertices)

    print("Loading LiDAR LAS...")
    las = laspy.read(args.ref)
    ref_pts = np.vstack((las.x, las.y, las.z)).transpose()

    bounds_min = recon_pts.min(axis=0)
    bounds_max = recon_pts.max(axis=0)

    meta = ReferenceMetadata(sensor="LiDAR", reference_type="PointCloud", crs=args.crs, vertical_datum=args.vdatum)
    res = evaluate_surface_accuracy(recon_pts, ref_pts, None, meta, bounds_min, bounds_max)

    print("Saving report...")
    save_report(res, Path(args.out))

if __name__ == "__main__":
    main()
