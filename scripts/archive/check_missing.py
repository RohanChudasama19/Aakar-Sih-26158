from pathlib import Path
frames_dir = Path('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/frames')
extracted = set(f.name for f in frames_dir.iterdir() if f.is_file() and f.name.endswith('.png'))

sparse_txt = Path('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/sparse_txt')
with open(sparse_txt / 'images.txt') as f:
    lines = f.readlines()
registered = set()
for line in lines:
    if line.startswith('#'): continue
    parts = line.split()
    if len(parts) >= 10 and parts[-1].endswith('.png'):
        registered.add(parts[-1])

missing = sorted(list(extracted - registered))
print("Missing images:", missing)
