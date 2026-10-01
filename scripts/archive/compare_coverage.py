import numpy as np
import open3d as o3d
from pathlib import Path

root = Path("C:/Users/ATHARAV/Documents/sih 26/gpt 6 astra/AAKAR-SIH26158-Surface-Fix/aakar")
exp_dir = root / "data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_experiment"

pcd4 = o3d.io.read_point_cloud(str(exp_dir / "fused_min4.ply"))
pcd2 = o3d.io.read_point_cloud(str(exp_dir / "fused_min2.ply"))

print(f"Points 4: {len(pcd4.points)}")
print(f"Points 2: {len(pcd2.points)}")

pts4 = np.asarray(pcd4.points)
pts2 = np.asarray(pcd2.points)

voxel_size = 1.0  # 1 meter resolution

def get_voxel_set(pts, vs):
    voxels = np.floor(pts / vs).astype(np.int32)
    return set(map(tuple, voxels))

v4 = get_voxel_set(pts4, voxel_size)
v2 = get_voxel_set(pts2, voxel_size)

print(f"Occupied cells (min4): {len(v4)}")
print(f"Occupied cells (min2): {len(v2)}")

new_cells = v2 - v4
print(f"New occupied cells (recovered): {len(new_cells)}")

# Look at bounding box
min_bound = np.min(pts2, axis=0)
max_bound = np.max(pts2, axis=0)
print(f"Bounds 2: Min {min_bound}, Max {max_bound}")
