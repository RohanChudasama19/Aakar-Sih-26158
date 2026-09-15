"""External COLMAP 3.9 CLI integration; every command is checked and logged."""

import os
import subprocess

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation


def run(args, work):
    with (work / "colmap.log").open("a") as log:
        log.write("\nCOMMAND: " + " ".join(map(str, args)) + "\n")
        log.flush()
        subprocess.run(
            list(map(str, args)),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=7200,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        )


def sparse(directory, info, k, notify):
    work = directory.parent
    db = work / "colmap.db"
    models = work / "sparse"
    models.mkdir(exist_ok=True)
    run(
        [
            "colmap",
            "feature_extractor",
            "--database_path",
            db,
            "--image_path",
            directory,
            "--ImageReader.mask_path",
            work / "masks",
            "--ImageReader.single_camera",
            "1",
            "--ImageReader.camera_model",
            "PINHOLE",
            "--ImageReader.camera_params",
            ",".join(str(v) for v in [k[0, 0], k[1, 1], k[0, 2], k[1, 2]]),
            "--SiftExtraction.use_gpu",
            "1",
        ],
        work,
    )
    notify(26, "COLMAP sequential feature matching")
    run(
        [
            "colmap",
            "sequential_matcher",
            "--database_path",
            db,
            "--SequentialMatching.overlap",
            "10",
            "--SiftMatching.use_gpu",
            "1",
        ],
        work,
    )
    run(
        [
            "colmap",
            "mapper",
            "--database_path",
            db,
            "--image_path",
            directory,
            "--output_path",
            models,
            "--Mapper.ba_refine_focal_length",
            "0",
            "--Mapper.ba_refine_principal_point",
            "0",
            "--Mapper.ba_refine_extra_params",
            "0",
        ],
        work,
    )
    choices = list(models.glob("*/images.bin"))
    if not choices:
        raise ValueError("COLMAP could not register cameras; see colmap.log")
    model = max(choices, key=lambda p: p.stat().st_size).parent
    textdir = work / "sparse_txt"
    textdir.mkdir(exist_ok=True)
    run(["colmap", "model_converter", "--input_path", model, "--output_path", textdir, "--output_type", "TXT"], work)
    poses = {}
    lines = (textdir / "images.txt").read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        values = line.split()
        qw, qx, qy, qz = map(float, values[1:5])
        rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
        name = values[9]
        idx = next((n for n, f in enumerate(info["frames"]) if f["name"] == name), None)
        if idx is not None:
            poses[idx] = np.c_[rot, np.array(values[5:8], float)]
        i += 1  # points2D line may be empty, but still consumes a line
    points = []
    colors = []
    errors = []
    for line in (textdir / "points3D.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            v = line.split()
            points.append(list(map(float, v[1:4])))
            colors.append(list(map(int, v[4:7])))
            errors.append(float(v[7]))
    if len(poses) < 3 or len(points) < 25:
        raise ValueError("COLMAP model has insufficient registered geometry")
    return {
        "points": np.array(points),
        "colors": np.array(colors, np.uint8),
        "poses": poses,
        "model_path": str(model),
        "reprojection_rmse_px": float(np.sqrt(np.mean(np.square(errors)))),
        "engine": "colmap_cuda",
    }


def dense(sfm, directory, notify):
    work = directory.parent
    target = work / "dense"
    run(
        [
            "colmap",
            "image_undistorter",
            "--image_path",
            directory,
            "--input_path",
            sfm["model_path"],
            "--output_path",
            target,
            "--output_type",
            "COLMAP",
            "--max_image_size",
            "1600",
        ],
        work,
    )
    notify(46, "CUDA PatchMatch stereo; see colmap.log for detailed iteration output")
    run(
        ["colmap", "patch_match_stereo", "--workspace_path", target, "--PatchMatchStereo.geom_consistency", "true"],
        work,
    )
    run(
        [
            "colmap",
            "stereo_fusion",
            "--workspace_path",
            target,
            "--input_type",
            "geometric",
            "--output_path",
            target / "fused.ply",
        ],
        work,
    )
    cloud = trimesh.load(target / "fused.ply", process=False)
    if len(cloud.vertices) < 100:
        raise ValueError("COLMAP dense fusion produced too few supported points")
    return (
        np.array(cloud.vertices),
        np.array(cloud.colors[:, :3]),
        {"method": "COLMAP_PatchMatch_MVS", "stereo_points": len(cloud.vertices), "neural_completion": False},
    )
