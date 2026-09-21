import os
import shutil
import subprocess
from typing import Any, Dict


def get_colmap_path() -> str:
    path = os.environ.get("COLMAP_BIN")
    if path and os.path.exists(path):
        return path
    path = shutil.which("COLMAP.bat") or shutil.which("colmap")
    if path:
        return path
    fallback = r"C:\Tools\COLMAP\COLMAP.bat"
    if os.path.exists(fallback):
        return fallback
    return "NOT_FOUND"


def get_openmvs_path(binary: str) -> str:
    path = os.environ.get(f"OPENMVS_{binary.upper().replace('POINTCLOUD', '')}")
    if path and os.path.exists(path):
        return path
    path = shutil.which(binary)
    if path:
        return path
    fallback = (
        rf"C:\Users\ATHARAV\Documents\AeroForge-SIH26158\aeroforge\OpenMVS_Windows_x64\vc17\x64\Release\{binary}.exe"
    )
    if os.path.exists(fallback):
        return fallback
    return "NOT_FOUND"


def run_doctor() -> Dict[str, Any]:
    res = {}

    # GPU / nvidia-smi
    try:
        smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=True)
        res["nvidia-smi"] = "Executed successfully"
        for line in smi.stdout.split("\n"):
            if "NVIDIA" in line and "GeForce" in line:
                res["NVIDIA_GPU"] = line.strip()
            if "Driver Version" in line:
                res["NVIDIA_DRIVER"] = line.strip()
    except Exception:
        res["nvidia-smi"] = "Failed or NOT_FOUND"
        res["NVIDIA_GPU"] = "NOT_FOUND"
        res["NVIDIA_DRIVER"] = "NOT_FOUND"

    # COLMAP
    colmap = get_colmap_path()
    res["COLMAP_FOUND"] = colmap
    res["COLMAP_VERSION"] = "NOT_FOUND"
    res["COLMAP_CUDA_BUILD"] = "NOT_FOUND"
    res["COLMAP_GPU_FEATURE_EXTRACTION"] = "NOT_FOUND"
    res["COLMAP_PATCHMATCH"] = "NOT_FOUND"
    res["COLMAP_PATCHMATCH_GPU_RUNTIME"] = "NOT_FOUND"
    if colmap != "NOT_FOUND":
        try:
            v = subprocess.run([colmap, "help"], capture_output=True, text=True)
            v_text = v.stdout + v.stderr
            if "COLMAP 4.2.0" in v_text:
                res["COLMAP_VERSION"] = "4.2.0"
            if "with CUDA" in v_text:
                res["COLMAP_CUDA_BUILD"] = "TRUE"

            fm = subprocess.run([colmap, "feature_extractor", "-h"], capture_output=True, text=True)
            fm_text = fm.stdout + fm.stderr
            if "FeatureExtraction.use_gpu" in fm_text:
                res["COLMAP_GPU_FEATURE_EXTRACTION"] = "VERIFIED"

            pm = subprocess.run([colmap, "patch_match_stereo", "-h"], capture_output=True, text=True)
            pm_text = pm.stdout + pm.stderr
            if "PatchMatchStereo" in pm_text:
                res["COLMAP_PATCHMATCH"] = "VERIFIED"
            if "PatchMatchStereo.gpu_index" in pm_text:
                res["COLMAP_PATCHMATCH_GPU_RUNTIME"] = "VERIFIED"
        except Exception:
            pass

    # OpenMVS
    res["OPENMVS"] = {
        "InterfaceCOLMAP": get_openmvs_path("InterfaceCOLMAP"),
        "DensifyPointCloud": get_openmvs_path("DensifyPointCloud"),
        "ReconstructMesh": get_openmvs_path("ReconstructMesh"),
        "RefineMesh": get_openmvs_path("RefineMesh"),
        "TextureMesh": get_openmvs_path("TextureMesh"),
    }

    # Python packages
    try:
        import open3d as o3d

        res["OPEN3D"] = o3d.__version__
    except Exception:
        res["OPEN3D"] = "NOT_FOUND"

    try:
        import torch

        res["PYTORCH"] = torch.__version__
        res["PYTORCH_CUDA"] = str(torch.cuda.is_available())
    except Exception:
        res["PYTORCH"] = "NOT_FOUND"
        res["PYTORCH_CUDA"] = "NOT_FOUND"

    return res


if __name__ == "__main__":
    import json

    print(json.dumps(run_doctor(), indent=2))
