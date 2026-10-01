import json

with open('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/outputs/sparse/images.json', 'r') as f:
    images = json.load(f)

empty_images = 0
total_images = len(images)
for img_id, img_data in images.items():
    points = img_data.get('points3D_ids', [])
    valid_points = [p for p in points if p != -1]
    if len(valid_points) == 0:
        empty_images += 1

print(f"Total images in sparse model: {total_images}")
print(f"Images with 0 valid 3D points: {empty_images}")
print(f"Images with >0 valid 3D points: {total_images - empty_images}")
