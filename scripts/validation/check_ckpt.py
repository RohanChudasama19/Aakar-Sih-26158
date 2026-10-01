import torch
import hashlib
from pathlib import Path

try:
    ckpt = torch.load("best_model.pth", map_location="cpu")
    epoch = ckpt.get("epoch", "unknown")
    h = hashlib.sha256(Path("best_model.pth").read_bytes()).hexdigest()[:8]
    print(f"epoch: {epoch}")
    print(f"hash: {h}")
except Exception as e:
    print(f"Error: {e}")
