import pathlib
dense_imgs = set(p.name for p in pathlib.Path('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/dense_fast_quality/images').glob('*.png'))

with open('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/dense_fast_quality/stereo/patch-match.cfg', 'r') as f:
    lines = f.readlines()

pm_imgs = set()
for line in lines:
    line = line.strip()
    if line.endswith('.png'):
        pm_imgs.add(line)

print(f"Images in dir: {len(dense_imgs)}")
print(f"Images in pm: {len(pm_imgs)}")
print(f"In pm but not in dir: {pm_imgs - dense_imgs}")
print(f"In dir but not in pm: {dense_imgs - pm_imgs}")
