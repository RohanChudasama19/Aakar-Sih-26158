import os
import json
import torch
import subprocess
import time
from pathlib import Path

def print_gate(freq_data):
    print("SEMANTIC TRAINING GATE\n")
    print("Environment:")
    import sys
    print(f"Python: {sys.version.split(' ')[0]}")
    import torchvision
    print(f"torch: {torch.__version__}")
    print(f"torchvision: {torchvision.__version__}")
    print(f"torch CUDA: {torch.version.cuda}")
    print(f"torch.cuda available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.0f} MB")
    else:
        print("GPU: CPU-only / Failed to load CUDA")
        print("VRAM: N/A")
        
    print("\nDataset:")
    print("train: 200")
    print("val: 70")
    print("test: 150")
    print(f"unknown mask colors: {len(freq_data.get('unknown_colors', []))}")
    
    print("\nExact train pixel counts:")
    counts = freq_data["counts"]
    for k, v in counts.items():
        print(f"{k}: {v}")
    print(f"total: {freq_data['total_accounted']}")
    print(f"expected total: {freq_data['expected_pixels']}")
    print(f"match: {freq_data['match']}")
    
    print("\nModel:")
    print("architecture: LRASPP MobileNetV3-Large")
    print("classes: 8")
    print("pretrained weights: COCO_WITH_VOC_LABELS_V1 (BSD 3-Clause)")
    
    print("\nTraining config:")
    print("crop: 512x512")
    print("batch: 2")
    print("gradient accumulation: 8")
    print("AMP: TRUE")
    print("workers: 2")
    print("optimizer: AdamW")
    print("learning rate: 1e-3")
    
if __name__ == "__main__":
    with open("exact_frequencies.json", "r") as f:
        freq_data = json.load(f)
    print_gate(freq_data)
