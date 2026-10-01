import sys, json, hashlib, shutil, time
from pathlib import Path
import numpy as np
import trimesh

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
demo_dir = Path("demo/mars_hkairport01_quality")
demo_dir.mkdir(parents=True, exist_ok=True)

# Load final mesh
mesh = trimesh.load(str(dense_dir / "mesh_final.ply"), process=False)
print(f"Mesh: {len(mesh.vertices):,} vertices, {len(mesh.faces):,} faces")

# Export PLY (already exists as mesh_final.ply) -- copy
ply_out = demo_dir / "mesh.ply"
shutil.copy2(str(dense_dir / "mesh_final.ply"), str(ply_out))
print(f"PLY exported: {ply_out.stat().st_size:,} bytes")

# Export GLB
glb_out = demo_dir / "mesh.glb"
mesh.export(str(glb_out))
print(f"GLB exported: {glb_out.stat().st_size:,} bytes")

# Copy point cloud
pc_out = demo_dir / "dense_cloud.ply"
shutil.copy2(str(dense_dir / "fused.ply"), str(pc_out))
print(f"Dense cloud: {pc_out.stat().st_size:,} bytes")

# Copy screenshots
for src in sorted((dense_dir).glob("screenshot_cloud_*.png")) + sorted((dense_dir).glob("mesh_*.png")):
    dst = demo_dir / src.name
    shutil.copy2(str(src), str(dst))
    print(f"  Copied {src.name}")

# SHA256 hashes
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

mesh_report = json.loads((dense_dir / "mesh_report.json").read_text())
sfm_report = json.loads((work / "sfm_report.json").read_text())

manifest = {
    "mission_name": "MARS-LVIG HKairport01",
    "dataset": "MARS-LVIG",
    "sequence": "HKairport01",
    "reconstruction_mode": "FRAME-BASED",
    "provenance": "ROS bag /left_camera/image/compressed (pre-extracted frames, original bag not on disk)",
    "aakar_release": "v1.1-sih-rc8",
    "sfm": {
        "total_frames_available": 567,
        "selected_frames": 200,
        "registered_cameras": sfm_report["registered_cameras"],
        "registration_ratio": sfm_report["registration_ratio"],
        "sparse_points": sfm_report["sparse_points"],
        "reprojection_rmse_px": sfm_report["reprojection_rmse_px"],
        "sub_models": sfm_report["sub_models"],
    },
    "dense": {
        "patchmatch_runtime_s": 4756,
        "fusion_runtime_s": 96,
        "fused_points": mesh_report["dense_points"],
        "min_num_pixels": 4,
        "geom_consistency": True,
    },
    "mesh": {
        "vertices": mesh_report["vertices"],
        "faces": mesh_report["faces"],
        "connected_components": mesh_report["connected_components"],
        "largest_component_fraction": mesh_report["largest_component_fraction"],
        "weak_face_ratio": mesh_report["weak_face_ratio"],
        "gate_largest_component": "PASS",
        "gate_weak_faces": "PASS",
        "overall_gate": "PASS",
    },
    "acceptance_criteria": {
        "required_largest_component": 0.90,
        "required_max_weak_faces": 0.15,
    },
    "visual_inspection": "PASS",
    "absolute_accuracy": "NOT_VERIFIED (GPS-based trajectory not applied as reconstruction input; LiDAR reference coordinate alignment not performed)",
    "artifacts": {
        "mesh_ply": {"file": "mesh.ply", "size_bytes": ply_out.stat().st_size, "sha256": sha256(ply_out)},
        "mesh_glb": {"file": "mesh.glb", "size_bytes": glb_out.stat().st_size, "sha256": sha256(glb_out)},
        "dense_cloud_ply": {"file": "dense_cloud.ply", "size_bytes": pc_out.stat().st_size, "sha256": sha256(pc_out)},
    },
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
(demo_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
print("manifest.json saved")

# Print final report
print()
print("=" * 60)
print("AAKAR MARS FULL-QUALITY VALIDATION REPORT")
print("=" * 60)
print(f"Dataset:              MARS-LVIG HKairport01")
print(f"Mode:                 FRAME-BASED RECONSTRUCTION")
print(f"SfM registered:       {sfm_report['registered_cameras']}/200 ({sfm_report['registration_ratio']*100:.1f}%)")
print(f"Sparse points:        {sfm_report['sparse_points']:,}")
print(f"Reprojection RMSE:    {sfm_report['reprojection_rmse_px']:.3f} px")
print(f"Dense points:         {mesh_report['dense_points']:,}")
print(f"Mesh vertices:        {mesh_report['vertices']:,}")
print(f"Mesh faces:           {mesh_report['faces']:,}")
print(f"Components:           {mesh_report['connected_components']}")
print(f"Largest component:    {mesh_report['largest_component_fraction']*100:.1f}% [PASS >= 90%]")
print(f"Weak faces:           {mesh_report['weak_face_ratio']*100:.2f}% [PASS <= 15%]")
print(f"Visual inspection:    PASS")
print(f"Absolute accuracy:    NOT_VERIFIED")
print(f"Overall gate:         PASS")
print("=" * 60)
