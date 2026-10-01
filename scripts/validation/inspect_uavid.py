import os
import glob
import cv2
import numpy as np
import json
import torch
import subprocess
from pathlib import Path

def get_dir_size(path='.'):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

def inspect_uavid():
    root = Path("data_external/uavid/raw/UAVid-v1")
    report = {
        "splits": {"train": {}, "val": {}, "test": {}},
        "missing_pairs": [],
        "dimension_mismatches": [],
        "formats": {"image": set(), "mask": set()},
        "dimensions": {"image": set(), "mask": set()},
        "classes": {}
    }
    
    # Check splits
    for split in ["train", "val", "test"]:
        split_path = root / split
        if not split_path.exists():
            continue
        
        seqs = [d for d in split_path.iterdir() if d.is_dir()]
        report["splits"][split]["seq_count"] = len(seqs)
        report["splits"][split]["seqs"] = [d.name for d in seqs]
        
        split_img_cnt = 0
        split_mask_cnt = 0
        
        for seq in seqs:
            img_dir = seq / "Images"
            mask_dir = seq / "Labels"
            
            imgs = list(img_dir.glob("*.*")) if img_dir.exists() else []
            masks = list(mask_dir.glob("*.*")) if mask_dir.exists() else []
            
            split_img_cnt += len(imgs)
            split_mask_cnt += len(masks)
            
            for img_path in imgs:
                report["formats"]["image"].add(img_path.suffix.lower())
                mask_path = mask_dir / (img_path.stem + ".png") # commonly PNG for masks
                if not mask_path.exists():
                    report["missing_pairs"].append(str(img_path))
                else:
                    # Dimensions and Classes
                    img = cv2.imread(str(img_path))
                    mask = cv2.imread(str(mask_path))
                    
                    if img is not None:
                        report["dimensions"]["image"].add(f"{img.shape[1]}x{img.shape[0]}")
                    if mask is not None:
                        report["dimensions"]["mask"].add(f"{mask.shape[1]}x{mask.shape[0]}")
                        
                    if img is not None and mask is not None and img.shape[:2] != mask.shape[:2]:
                        report["dimension_mismatches"].append(str(img_path))
                        
                    # Sample classes from first few images in train split to save time
                    if split == "train" and np.random.rand() < 0.2:
                        unique_colors = np.unique(mask.reshape(-1, mask.shape[2]), axis=0)
                        for color in unique_colors:
                            # BGR to RGB tuple
                            c_tup = (int(color[2]), int(color[1]), int(color[0]))
                            c_str = str(c_tup)
                            if c_str not in report["classes"]:
                                report["classes"][c_str] = 0
                            # Estimate frequency by counting in this mask
                            mask_pixels = np.all(mask == color, axis=-1).sum()
                            report["classes"][c_str] += int(mask_pixels)
                            
        report["splits"][split]["images"] = split_img_cnt
        report["splits"][split]["masks"] = split_mask_cnt

    report["formats"]["image"] = list(report["formats"]["image"])
    report["formats"]["mask"] = list(report["formats"]["mask"])
    report["dimensions"]["image"] = list(report["dimensions"]["image"])
    report["dimensions"]["mask"] = list(report["dimensions"]["mask"])

    return report

def check_env():
    env = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if hasattr(torch.version, 'cuda') else None,
    }
    
    try:
        smi = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], text=True).strip()
        env["gpu"] = smi
    except Exception as e:
        env["gpu"] = f"Failed to run nvidia-smi: {e}"
        
    return env

if __name__ == "__main__":
    report = inspect_uavid()
    env = check_env()
    
    with open("uavid_inspect.json", "w") as f:
        json.dump({"report": report, "env": env}, f, indent=2)
    print("Done")
