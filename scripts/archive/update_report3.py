import json
from pathlib import Path

tmpl_path = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs/mission_report.json")
rep = json.loads(tmpl_path.read_text())

rep["mission"] = "mars_hkairport01_quality"
rep["processing_time_sec"] = 5820
rep["metric_state"] = "RELATIVE"
if isinstance(rep.get("preprocessing"), dict):
    rep["preprocessing"]["video_ingestion"] = "NOT_VALIDATED"
else:
    rep["preprocessing"] = {"video_ingestion": "NOT_VALIDATED"}

rep["mesh"]["largest_component_area_fraction"] = 0.993
rep["mesh"]["weak_face_ratio"] = 0.0025
rep["mesh"]["vertices"] = 183777
rep["mesh"]["faces"] = 355173

rep["alignment"] = {"absolute_accuracy": "NOT_VERIFIED", "metric_state": "RELATIVE"}
rep["exports"]["metric_state"] = "RELATIVE"

rep["exports"]["generated_files"] = {
    "cloud_relative.ply": {
        "size_bytes": 204382040,
        "format": "PLY_RELATIVE"
    },
    "model.glb": {
        "size_bytes": 51868148,
        "format": "GLB"
    }
}

Path("data/mars_hkairport01_quality/work/outputs/mission_report.json").write_text(json.dumps(rep, indent=2))
print("Updated mission_report.json correctly")
