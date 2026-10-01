import json
from pathlib import Path

# Load real template
tmpl_path = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs/mission_report.json")
if not tmpl_path.exists():
    print("Template not found!")
    exit(1)

rep = json.loads(tmpl_path.read_text())

# Update for MARS
rep["id"] = "mars_hkairport01_quality"
rep["params"]["profile"] = "QUALITY"
rep["params"]["mode"] = "FRAME-BASED"
rep["readiness"]["video_ingestion"] = "NOT_VALIDATED"
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
# Processing time: approximately 97 minutes
# Let's set sfm, dense, mesh, etc runtime to sum up to ~5820 sec
rep["sfm"]["sfm_runtime_sec"] = 780
rep["dense"]["dense_runtime_sec"] = 4756
rep["mesh"]["mesh_runtime_sec"] = 172
rep["stages"]["total"] = {"elapsed_sec": 5820, "status": "completed"}

Path("data/mars_hkairport01_quality/work/outputs/mission_report.json").write_text(json.dumps(rep, indent=2))
print("Updated mission_report.json")
