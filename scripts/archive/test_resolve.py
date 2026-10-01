from pathlib import Path
out = (Path("data") / "mars_hkairport01_quality" / "work" / "outputs").resolve()
p = (out / "model.glb").resolve()
print("out:", out)
print("p:", p)
print("exists?", p.is_file())
print("relative to out?", p.is_relative_to(out))
