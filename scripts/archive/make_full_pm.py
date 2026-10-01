import pathlib
stereo_dir = pathlib.Path('test_dense_full/stereo')
stereo_dir.mkdir(exist_ok=True)
images_dir = pathlib.Path('test_dense_full/images')
image_files = sorted([f.name for f in images_dir.iterdir() if f.is_file()])

target_refs = 105
step = len(image_files) / max(1, target_refs)
ref_indices = {int(i * step) for i in range(target_refs)}

cfg_lines = []
for i, img in enumerate(image_files):
    if i in ref_indices:
        cfg_lines.append(f"{img}")
        cfg_lines.append(f"__auto__, 6")

(stereo_dir / 'patch-match.cfg').write_text('\n'.join(cfg_lines))
