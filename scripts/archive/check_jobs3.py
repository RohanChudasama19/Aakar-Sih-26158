import sys
sys.path.insert(0, '.')
from app.main import DATA
jobs = []
for d in DATA.iterdir():
    if not d.is_dir(): continue
    rep = d / "work" / "outputs" / "mission_report.json"
    if rep.exists():
        jobs.append(d.name)
print("mars in DATA dirs with report?", "mars_hkairport01_quality" in jobs)
