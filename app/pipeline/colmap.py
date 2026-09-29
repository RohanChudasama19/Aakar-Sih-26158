import os
import shutil
from typing import Optional


def resolve_colmap_executable() -> Optional[str]:
    r"""
    Resolve the COLMAP executable path.
    1. configured explicit COLMAP path (C:\Tools\COLMAP\COLMAP.bat or bin\colmap.exe)
    2. PATH / shutil.which
    3. known validated Windows install path
    4. None if not found
    """
    candidates = [r"C:\Tools\COLMAP\bin\colmap.exe", r"C:\Tools\COLMAP\COLMAP.bat"]

    which_colmap = shutil.which("colmap")
    if which_colmap:
        candidates.insert(1, which_colmap)

    for p in candidates:
        if os.path.exists(p):
            if p.lower().endswith(".bat"):
                exe_path = os.path.join(os.path.dirname(p), "bin", "colmap.exe")
                if os.path.exists(exe_path):
                    return exe_path
            return p

    return None


def get_colmap_env() -> dict:
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    colmap_exe = resolve_colmap_executable()
    if colmap_exe:
        bin_dir = os.path.dirname(colmap_exe)
        plugins_dir = os.path.join(os.path.dirname(bin_dir), "plugins")
        if os.path.exists(plugins_dir):
            env["QT_PLUGIN_PATH"] = plugins_dir + os.pathsep + env.get("QT_PLUGIN_PATH", "")
    return env


"""External COLMAP 3.9 CLI integration; every command is checked and logged."""

import subprocess

import numpy as np
from scipy.spatial.transform import Rotation


def run(args, work):
    cmd_list = list(map(str, args))
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}

    colmap_path = cmd_list[0]
    if colmap_path == "colmap":
        colmap_path = shutil.which("colmap") or "colmap"

    if colmap_path and colmap_path.lower().endswith(".bat"):
        # Workaround for COLMAP.bat argument quoting bug on Windows
        script_path = os.path.dirname(colmap_path)
        exe_path = os.path.join(script_path, "bin", "colmap.exe")
        if os.path.exists(exe_path):
            cmd_list[0] = exe_path
            env["PATH"] = os.path.join(script_path, "bin") + os.pathsep + env.get("PATH", "")
            env["QT_PLUGIN_PATH"] = os.path.join(script_path, "plugins") + os.pathsep + env.get("QT_PLUGIN_PATH", "")

    with (work / "colmap.log").open("a") as log:
        log.write("\nCOMMAND: " + " ".join(cmd_list) + "\n")
        log.flush()
        subprocess.run(
            cmd_list,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=None,
            env=env,
        )


def sparse(directory, info, camera, notify):
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
            camera.model_type.value,
            "--ImageReader.camera_params",
            camera.to_colmap(),
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

