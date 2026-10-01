import os
from pathlib import Path

p = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data\95f51b12-b771-47bf-9201-c3700f9475a7\work")

stereo_dirs = ["dense_full_ref2/stereo", "dense_10_source_full/stereo", "dense_fast_quality/stereo"]

results = {}

def get_ext_size(path):
    sizes = {"depth": 0, "normal": 0, "consistency": 0, "config": 0, "logs": 0, "other": 0}
    if not path.exists(): return sizes
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            sz = os.path.getsize(fp)
            if "depth_maps" in dirpath: sizes["depth"] += sz
            elif "normal_maps" in dirpath: sizes["normal"] += sz
            elif f.endswith(".cfg") or f.endswith(".json"): sizes["config"] += sz
            elif f.endswith(".txt") or f.endswith(".log"): sizes["logs"] += sz
            else: sizes["other"] += sz
    return sizes

for sd in stereo_dirs:
    tgt = p / sd
    res = get_ext_size(tgt)
    results[sd] = res

for sd, res in results.items():
    print(f"\n{sd}:")
    print(f"  depth maps: {res['depth']/1e9:.3f} GB")
    print(f"  normal maps: {res['normal']/1e9:.3f} GB")
    print(f"  configs: {res['config']/1e6:.3f} MB")
    print(f"  logs: {res['logs']/1e6:.3f} MB")
    print(f"  other: {res['other']/1e9:.3f} GB")
