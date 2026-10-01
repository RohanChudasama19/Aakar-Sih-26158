import shutil
from pathlib import Path
import json

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_10_source_full")
demo_dir = Path("demo/degraded_fast_quality")

# Copy models
shutil.copy2(work_dir / "mesh_repaired.ply", demo_dir / "mesh_repaired.ply")
shutil.copy2(work_dir / "mesh_textured.glb", demo_dir / "mesh_textured.glb")

manifest = {
    "source_job_id": "95f51b12-b771-47bf-9201-c3700f9475a7",
    "quality_report": {
        "full_scene_quality": "FAIL",
        "demo_classification": "USABLE DEGRADED MODEL",
        "largest_component_fraction": 0.7696,
        "weak_faces_fraction": 0.004,
        "measured_gaps": "8.32 m to 117.60 m"
    },
    "validation_report": {
        "visual_geometry": "ACCEPTED",
        "texture_alignment": "PASS",
        "exports": "VALID",
        "react_viewer": "PASS",
        "offline_test": "PASS"
    },
    "performance_report": {
        "patchmatch": 1009,
        "fusion": 89,
        "texture": 120
    },
    "known_limitations": [
        "Major untextured gaps in landscape separating physical clusters.",
        "Model represents only 76.9% of scene connectivity.",
        "UseGeo absolute accuracy is NOT VERIFIED for this specific artifact."
    ],
    "sha256_hashes": {
        "mesh_repaired.ply": "551cdafb66a27a6d6cdc970a47a3fad7f69c63d24c6d70d7cb715063c213a7c3",
        "mesh_textured.glb": "to be calculated",
        "largest_component.ply": "to be calculated",
        "largest_component_textured.glb": "to be calculated"
    }
}
with open(demo_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
