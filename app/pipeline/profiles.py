import json
from pathlib import Path

FAST_QUALITY_V1 = {
    "profile_name": "FAST_QUALITY",
    "profile_version": "1.0",
    "candidate_budget": 400,
    "sfm_budget": 250,
    "sift_settings": {"max_num_features": 4096},
    "matching_settings": {"overlap": 10, "quadratic_overlap": True, "spatial_matching": False},
    "sfm_backend": "view_graph_calibrator + global_mapper",
    "dense_settings": {
        "reference_target": 105,
        "max_image_size": 1600,
        "window_radius": 4,
        "window_step": 2,
        "num_iterations": 3,
        "num_matching_views": 6,
        "geom_consistency": True,
    },
    "fusion_settings": {"min_num_pixels": 4},
    "mesh_settings": {"depth": 9, "scale": 1.05},
    "texture_settings": {"atlas_size": 4096},
}


def write_profile_report(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fast_quality_profile.json").write_text(json.dumps(FAST_QUALITY_V1, indent=2))
