import json
import os
from pathlib import Path
import shutil

def convert_uavid():
    input_dir = Path("data_external/uavid/raw/UAVid-v1")
    output_dir = Path("data_external/uavid/converted")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "dataset": "UAVid",
        "train_image_count": 0,
        "validation_image_count": 0,
        "test_image_count": 0,
        "labeled_image_count": 0,
        "warnings": [],
        "missing_pairs": [],
        "image_dimensions": "3840x2160",
        "mask_dimensions": "3840x2160",
        "class_map": {
            "(0, 0, 0)": "Clutter",
            "(128, 0, 0)": "Building",
            "(128, 64, 128)": "Road",
            "(0, 128, 0)": "Tree",
            "(128, 128, 0)": "Low Vegetation",
            "(64, 0, 128)": "Moving Car",
            "(192, 0, 192)": "Static Car",
            "(64, 64, 0)": "Human"
        },
        "source_paths": str(input_dir),
        "provenance": "Original UAVid-v1 archive"
    }

    for split in ["train", "val", "test"]:
        split_path = input_dir / split
        if not split_path.exists():
            continue
            
        out_split = output_dir / split
        out_split.mkdir(exist_ok=True)
        
        seqs = [d for d in split_path.iterdir() if d.is_dir()]
        
        for seq in seqs:
            img_dir = seq / "Images"
            mask_dir = seq / "Labels"
            
            out_seq = out_split / seq.name
            out_seq.mkdir(exist_ok=True)
            
            # Use symlinks to avoid duplicating 6GB of data
            if img_dir.exists():
                try:
                    target_img = out_seq / "Images"
                    if not target_img.exists():
                        os.symlink(img_dir.absolute(), target_img, target_is_directory=True)
                except OSError as e:
                    report["warnings"].append(f"Symlink failed for {seq.name} Images: {e}")
                    
                imgs = list(img_dir.glob("*.png"))
                if split == "train":
                    report["train_image_count"] += len(imgs)
                elif split == "val":
                    report["validation_image_count"] += len(imgs)
                elif split == "test":
                    report["test_image_count"] += len(imgs)
            
            if mask_dir.exists():
                try:
                    target_mask = out_seq / "Labels"
                    if not target_mask.exists():
                        os.symlink(mask_dir.absolute(), target_mask, target_is_directory=True)
                except OSError as e:
                    report["warnings"].append(f"Symlink failed for {seq.name} Labels: {e}")
                    
                masks = list(mask_dir.glob("*.png"))
                report["labeled_image_count"] += len(masks)
                
                # Check for missing masks in train/val
                if split in ["train", "val"]:
                    for img in imgs:
                        if not (mask_dir / img.name).exists():
                            report["missing_pairs"].append(str(img))
                            
    with open(output_dir / "conversion_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
if __name__ == "__main__":
    convert_uavid()
