images_txt_path = 'data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/dense_fast_quality/sparse_txt/images.txt'

total_images = 0
empty_images = 0

with open(images_txt_path, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('#') or len(line.strip()) == 0:
        continue
    # Even lines are Image properties, odd lines are Points2D
    # But wait, images.txt has 2 lines per image. 
    # Let's just check if it ends in '.png' or '.jpg'
    parts = line.strip().split()
    if len(parts) > 9 and parts[-1].endswith(('.png', '.jpg')):
        total_images += 1
        points_line = lines[i+1].strip().split()
        # Points line: X Y POINT3D_ID ...
        valid_points = 0
        for j in range(2, len(points_line), 3):
            if points_line[j] != '-1':
                valid_points += 1
        if valid_points == 0:
            empty_images += 1

print(f"Total images in dense_fast_quality/sparse_txt: {total_images}")
print(f"Images with 0 valid 3D points: {empty_images}")
print(f"Images with >0 valid 3D points: {total_images - empty_images}")
