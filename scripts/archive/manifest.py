import json
import hashlib
from pathlib import Path

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

dense_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_full_ref2")
fused_ply = dense_dir / "fused.ply"

manifest = {
    "source_job": "95f51b12-b771-47bf-9201-c3700f9475a7",
    "configuration": {
        "num_matching_views": 6,
        "fusion_min_num_pixels": 4,
        "geom_consistency": True,
        "PatchMatch_references": 250,
        "PatchMatch_max_image_size": 1600
    },
    "runtime": {
        "PatchMatch": 1009.0,
        "StereoFusion": 89.0
    },
    "artifacts": [
        {
            "path": str(fused_ply),
            "sha256": sha256_file(fused_ply) if fused_ply.exists() else "MISSING"
        }
    ]
}

Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/full_ref_manifest.json").write_text(json.dumps(manifest, indent=2))
print("Manifest written")
