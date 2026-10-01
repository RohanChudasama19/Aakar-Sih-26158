from pathlib import Path
mars_dir = Path("data/mars_hkairport01_quality")
orig = sorted(list((mars_dir / "work/originals").glob("*.jpg")))
frames = sorted(list((mars_dir / "work/frames").glob("*.jpg")))
dense = sorted(list((mars_dir / "work/dense_mars/images").glob("*.jpg")))
print(f"Originals: {len(orig)}, first: {orig[0].name if orig else 'none'}, last: {orig[-1].name if orig else 'none'}")
print(f"Frames: {len(frames)}, first: {frames[0].name if frames else 'none'}, last: {frames[-1].name if frames else 'none'}")
print(f"Dense: {len(dense)}, first: {dense[0].name if dense else 'none'}, last: {dense[-1].name if dense else 'none'}")
