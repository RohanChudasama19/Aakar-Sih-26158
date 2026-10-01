import json
import math
points_map = {}
lines = open("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/sparse_txt/images.txt").read().splitlines()
i = 0
while i < len(lines):
    header = lines[i].strip()
    i += 1
    if not header or header.startswith("#"):
        continue
    parts = header.split()
    if len(parts) >= 10:
        name = parts[9]
        pts_line = lines[i].strip()
        i += 1
        pts_parts = pts_line.split()
        pt_ids = {int(pts_parts[j]) for j in range(2, len(pts_parts), 3) if int(pts_parts[j]) != -1}
        points_map[name] = pt_ids

image_files = sorted(list(points_map.keys()))
target_refs = 105
step = len(image_files) / max(1, target_refs) if len(image_files) > target_refs else 1
ref_indices = {int(i * step) for i in range(min(len(image_files), target_refs))}
ref_images = [img for i, img in enumerate(image_files) if i in ref_indices]

print("References:", len(ref_images))
img1 = ref_images[0]
print("Image1:", img1, "points:", len(points_map[img1]))
overlaps = []
for other in ref_images:
    if other != img1:
        shared = len(points_map[img1].intersection(points_map[other]))
        if shared > 0:
            overlaps.append((shared, other))
overlaps.sort(reverse=True)
print("Top overlaps in ref_images:")
for s, name in overlaps[:10]:
    print(f"  {name}: {s} shared points")
