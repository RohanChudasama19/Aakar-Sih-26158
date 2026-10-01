import os
import numpy as np
from PIL import Image
from pathlib import Path
import json

COLOR_MAP = {
    (0, 0, 0): "Clutter",
    (128, 0, 0): "Building",
    (128, 64, 128): "Road",
    (0, 128, 0): "Tree",
    (128, 128, 0): "Low Vegetation",
    (64, 0, 128): "Moving Car",
    (192, 0, 192): "Static Car",
    (64, 64, 0): "Human"
}

def recompute_frequencies():
    train_dir = Path("data_external/uavid/converted/train")
    
    counts = {name: 0 for name in COLOR_MAP.values()}
    total_pixels = 0
    expected_pixels = 0
    unknown_colors = set()
    
    for seq in train_dir.iterdir():
        if seq.is_dir():
            mask_dir = seq / "Labels"
            if mask_dir.exists():
                for mask_path in mask_dir.glob("*.png"):
                    mask = Image.open(mask_path).convert("RGB")
                    mask_np = np.array(mask)
                    h, w, c = mask_np.shape
                    
                    # vectorized count using 1D hash (R*65536 + G*256 + B)
                    mask_1d = mask_np[:, :, 0].astype(np.int32) * 65536 + \
                              mask_np[:, :, 1].astype(np.int32) * 256 + \
                              mask_np[:, :, 2].astype(np.int32)
                              
                    expected_pixels += h * w
                    
                    for color, name in COLOR_MAP.items():
                        hash_val = color[0] * 65536 + color[1] * 256 + color[2]
                        cls_count = np.sum(mask_1d == hash_val)
                        counts[name] += int(cls_count)
                        total_pixels += int(cls_count)
                        
                    # find any unknown
                    known_mask = np.zeros(mask_1d.shape, dtype=bool)
                    for color in COLOR_MAP:
                        hash_val = color[0] * 65536 + color[1] * 256 + color[2]
                        known_mask |= (mask_1d == hash_val)
                    if not known_mask.all():
                        unknown_idx = ~known_mask
                        unknown = np.unique(mask_np[unknown_idx], axis=0)
                        for u in unknown:
                            unknown_colors.add(tuple(u))

    result = {
        "counts": counts,
        "total_accounted": total_pixels,
        "expected_pixels": expected_pixels,
        "unknown_colors": list(unknown_colors),
        "match": total_pixels == expected_pixels
    }
    
    with open("exact_frequencies.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    recompute_frequencies()
