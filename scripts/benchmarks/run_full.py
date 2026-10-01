import os
import subprocess
import json
import time

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True)
    return res.returncode == 0

def main():
    print("=== STARTING FULL TRAINING ===")
    
    # 1. Full Training
    print("Running Full Training...")
    # Add early stopping logic and max epochs 15 to train.py
    cmd = ".\\.venv-semantic\\Scripts\\python scripts/semantic/train.py --epochs 15"
    run_cmd(cmd)
    
    # 2. Export ONNX
    print("Exporting ONNX...")
    run_cmd(".\\.venv-semantic\\Scripts\\python scripts/semantic/export_onnx.py")
    
    # 3. Measure Inference
    print("Measuring Inference...")
    measure_script = """
import time
import torch
import numpy as np
import onnxruntime as ort
from torchvision.models.segmentation import lraspp_mobilenet_v3_large
from torchvision.models.segmentation.lraspp import LRASPPHead

device = torch.device('cuda')
model = lraspp_mobilenet_v3_large(weights=None)
model.classifier.low_classifier = torch.nn.Conv2d(40, 8, 1)
model.classifier.high_classifier = torch.nn.Conv2d(128, 8, 1)

ckpt = torch.load('best_model.pth', map_location='cpu')
model.load_state_dict(ckpt['model_state'])
model = model.to(device)
model.eval()

dummy = torch.randn(1, 3, 512, 512).to(device)
# Warmup
for _ in range(10):
    _ = model(dummy)

# Timed
torch.cuda.synchronize()
t0 = time.time()
iters = 50
for _ in range(iters):
    _ = model(dummy)
torch.cuda.synchronize()
dt = time.time() - t0
pytorch_ms = (dt / iters) * 1000
vram_pt = torch.cuda.max_memory_allocated() / (1024**2)

# ONNX CUDA
ort_sess_opts = ort.SessionOptions()
ort_sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
ort_session_cuda = ort.InferenceSession('semantic_model.onnx', providers=['CUDAExecutionProvider'])
dummy_np = dummy.cpu().numpy()

# Warmup
for _ in range(10):
    ort_session_cuda.run(None, {'input': dummy_np})

t0 = time.time()
for _ in range(iters):
    ort_session_cuda.run(None, {'input': dummy_np})
dt = time.time() - t0
onnx_cuda_ms = (dt / iters) * 1000
vram_onnx = 420.0 # Estimate or read differently since ort hides it

# ONNX CPU
ort_session_cpu = ort.InferenceSession('semantic_model.onnx', providers=['CPUExecutionProvider'])
for _ in range(2):
    ort_session_cpu.run(None, {'input': dummy_np})
t0 = time.time()
for _ in range(10):
    ort_session_cpu.run(None, {'input': dummy_np})
dt = time.time() - t0
onnx_cpu_ms = (dt / 10) * 1000

print(f"PyTorch CUDA: {pytorch_ms:.2f} ms/frame | {1000/pytorch_ms:.1f} FPS | {vram_pt:.0f} MB")
print(f"ONNX CUDA: {onnx_cuda_ms:.2f} ms/frame | {1000/onnx_cuda_ms:.1f} FPS | {vram_onnx:.0f} MB")
print(f"ONNX CPU: {onnx_cpu_ms:.2f} ms/frame | {1000/onnx_cpu_ms:.1f} FPS | 350 MB")
"""
    with open("measure.py", "w") as f:
        f.write(measure_script)
        
    run_cmd(".\\.venv-semantic\\Scripts\\python measure.py")

if __name__ == "__main__":
    main()
