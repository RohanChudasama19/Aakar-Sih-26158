images_txt_path = 'data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/dense_fast_quality/sparse_txt/images.txt'

import collections

with open(images_txt_path, 'r') as f:
    lines = f.readlines()

point_counts = []
img_names = []

for i, line in enumerate(lines):
    if line.startswith('#') or len(line.strip()) == 0:
        continue
    parts = line.strip().split()
    if len(parts) > 9 and parts[-1].endswith(('.png', '.jpg')):
        img_name = parts[-1]
        points_line = lines[i+1].strip().split()
        valid_points = 0
        for j in range(2, len(points_line), 3):
            if points_line[j] != '-1':
                valid_points += 1
        point_counts.append(valid_points)
        img_names.append(img_name)

import pathlib
dense_imgs = set(p.name for p in pathlib.Path('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/dense_fast_quality/images').glob('*'))

missing = []
present = []
for name, c in zip(img_names, point_counts):
    if name in dense_imgs:
        present.append(c)
    else:
        missing.append(c)

print(f"Present (avg/min/max): {sum(present)/len(present):.1f} / {min(present)} / {max(present)} (count={len(present)})")
if missing:
    print(f"Missing (avg/min/max): {sum(missing)/len(missing):.1f} / {min(missing)} / {max(missing)} (count={len(missing)})")
else:
    print("No missing images")
