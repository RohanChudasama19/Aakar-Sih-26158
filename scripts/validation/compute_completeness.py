import argparse
import numpy as np
import trimesh
import laspy
from scipy.spatial import cKDTree
from scipy.ndimage import binary_dilation
from app.pipeline.surface_validation import voxel_downsample

def main():
    parser = argparse.ArgumentParser(description="Compute LiDAR to AeroRecon footprint completeness.")
    parser.add_argument("--dense", required=True, type=str, help="Path to reconstructed dense PLY.")
    parser.add_argument("--ref", required=True, type=str, help="Path to reference LAS/LAZ.")
    parser.add_argument("--res", default=2.0, type=float, help="Grid resolution for footprint (m).")
    parser.add_argument("--buffer", default=10.0, type=float, help="Dilation buffer for footprint (m).")
    args = parser.parse_args()

    recon_pts = np.array(trimesh.load(args.dense).vertices)
    las = laspy.read(args.ref)
    ref_pts = np.vstack((las.x, las.y, las.z)).transpose()

    res = args.res
    buffer_m = args.buffer
    buffer_cells = int(buffer_m / res)

    min_x, min_y = recon_pts[:,0].min(), recon_pts[:,1].min()
    max_x, max_y = recon_pts[:,0].max(), recon_pts[:,1].max()

    grid_w = int(np.ceil((max_x - min_x) / res)) + 2*buffer_cells + 2
    grid_h = int(np.ceil((max_y - min_y) / res)) + 2*buffer_cells + 2

    occupancy = np.zeros((grid_w, grid_h), dtype=bool)
    rx = ((recon_pts[:,0] - min_x) / res).astype(int) + buffer_cells
    ry = ((recon_pts[:,1] - min_y) / res).astype(int) + buffer_cells
    occupancy[rx, ry] = True

    occupancy_dilated = binary_dilation(occupancy, iterations=buffer_cells)
    
    in_bbox = (ref_pts[:,0] >= min_x - buffer_m) & (ref_pts[:,0] <= max_x + buffer_m) & \
              (ref_pts[:,1] >= min_y - buffer_m) & (ref_pts[:,1] <= max_y + buffer_m)

    ref_pts_bbox = ref_pts[in_bbox]
    lx = ((ref_pts_bbox[:,0] - min_x) / res).astype(int) + buffer_cells
    ly = ((ref_pts_bbox[:,1] - min_y) / res).astype(int) + buffer_cells

    valid_idx = (lx >= 0) & (lx < grid_w) & (ly >= 0) & (ly < grid_h)
    lx = lx[valid_idx]
    ly = ly[valid_idx]
    ref_pts_bbox = ref_pts_bbox[valid_idx]

    in_footprint = occupancy_dilated[lx, ly]
    ref_pts_footprint = ref_pts_bbox[in_footprint]

    recon_sampled = voxel_downsample(recon_pts, 0.05, 42)
    _, unique_indices = np.unique(np.floor(ref_pts_footprint / 0.05).astype(np.int32), axis=0, return_index=True)
    ref_sampled = ref_pts_footprint[unique_indices]

    tree = cKDTree(recon_sampled)
    dists, _ = tree.query(ref_sampled, k=1, workers=-1)

    print("--- METRICS ---")
    print(f"mean: {np.mean(dists)}")
    print(f"median: {np.median(dists)}")
    print(f"P95: {np.percentile(dists, 95)}")
    for th in [0.10, 0.25, 0.50, 1.00, 2.00]:
        print(f"within {th}m: {(dists <= th).mean() * 100:.2f}%")

if __name__ == "__main__":
    main()
