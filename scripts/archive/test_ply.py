import trimesh
import numpy as np
from pathlib import Path

fused_ply = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_full_ref2/fused.ply")
pc = trimesh.load(str(fused_ply))

verts = pc.vertices
count = len(verts)
is_finite = np.all(np.isfinite(verts))
bbox_min = verts.min(axis=0)
bbox_max = verts.max(axis=0)
extent = bbox_max - bbox_min
nonzero_extent = np.all(extent > 0)
has_colors = pc.colors is not None and len(pc.colors) > 0

print(f"Point count: {count}")
print(f"Finite: {is_finite}")
print(f"Nonzero extent: {nonzero_extent}")
print(f"Has colors: {has_colors}")
print(f"BBox: min={bbox_min}, max={bbox_max}")
print(f"Extent: {extent}")
