import os
import shutil
import subprocess
from typing import Any, Dict


def get_colmap_path() -> str:
    path = os.environ.get("COLMAP_BIN")
    if path and os.path.exists(path):
        return path
    path = shutil.which("colmap")
    if path:
        return path
    return "NOT_FOUND"


def get_openmvs_path(binary: str) -> str:
    path = os.environ.get(f"OPENMVS_{binary.upper().replace('POINTCLOUD', '')}")
    if path and os.path.exists(path):
        return path
    path = shutil.which(binary)
    if path:
        return path
    # Hardcoded fallback from recent discovery
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
        # Parse basic GPU
        for line in smi.stdout.split("\n"):
            if "NVIDIA" in line and "GeForce" in line:
                res["NVIDIA GPU"] = line.strip()
                break
    except Exception:
        res["nvidia-smi"] = "Failed or NOT_FOUND"
        res["NVIDIA GPU"] = "NOT_FOUND"

    # COLMAP
    colmap = get_colmap_path()
    res["COLMAP"] = colmap
    res["COLMAP version"] = "NOT_FOUND"
    res["COLMAP GPU SIFT"] = "NOT_FOUND"
    res["COLMAP PatchMatch"] = "NOT_FOUND"
    if colmap != "NOT_FOUND":
        try:
            _ = subprocess.run([colmap, "-h"], capture_output=True, text=True).stdout
            res["COLMAP version"] = "Found"
            pm = subprocess.run([colmap, "patch_match_stereo", "-h"], capture_output=True, text=True).stdout
            res["COLMAP PatchMatch"] = "VERIFIED" if "patch_match_stereo" in pm else "FALSE"
        except Exception:
            pass

    # OpenMVS
    res["OpenMVS InterfaceCOLMAP"] = get_openmvs_path("InterfaceCOLMAP")
    res["OpenMVS DensifyPointCloud"] = get_openmvs_path("DensifyPointCloud")
    res["OpenMVS ReconstructMesh"] = get_openmvs_path("ReconstructMesh")
    res["OpenMVS RefineMesh"] = get_openmvs_path("RefineMesh")
    res["OpenMVS TextureMesh"] = get_openmvs_path("TextureMesh")

    # Python packages
    try:
        import open3d as o3d

        res["Open3D"] = o3d.__version__
    except Exception:
        res["Open3D"] = "NOT_FOUND"

    try:
        import torch

        res["PyTorch"] = torch.__version__
        res["PyTorch CUDA"] = str(torch.cuda.is_available())
    except Exception:
        res["PyTorch"] = "NOT_FOUND"
        res["PyTorch CUDA"] = "NOT_FOUND"

    return res


if __name__ == "__main__":
    import json

    print(json.dumps(run_doctor(), indent=2))
