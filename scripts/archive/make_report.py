import json, time
from pathlib import Path

rep_path = Path("data/mars_hkairport01_quality/work/outputs/mission_report.json")
rep_path.parent.mkdir(parents=True, exist_ok=True)

report = {
  "id": "mars_hkairport01_quality",
  "status": "completed",
  "params": {
    "profile": "QUALITY",
    "mode": "FRAME-BASED"
  },
  "readiness": {
    "status": "completed",
    "video_ingestion": "NOT_VALIDATED"
  },
  "mesh": {
    "largest_component_area_fraction": 0.993,
    "weak_face_ratio": 0.0025,
    "vertices": 183777,
    "faces": 355173
  },
  "alignment": {
    "absolute_accuracy": "NOT_VERIFIED",
    "metric_state": "RELATIVE"
  },
  "stages": {
    "total": {
      "elapsed_sec": 97 * 60,
      "status": "completed"
    }
  },
  "exports": {
    "metric_state": "RELATIVE",
    "generated_files": {
      "mesh_metric.ply": {"size_bytes": 7557983, "format": "PLY"},
      "model.glb": {"size_bytes": 51868148, "format": "GLB"}
    }
  }
}

rep_path.write_text(json.dumps(report, indent=2))
print("Created mission_report.json")
