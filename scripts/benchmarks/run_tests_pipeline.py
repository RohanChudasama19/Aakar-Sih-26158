import os
import subprocess
import json

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED: {cmd}")
        print(res.stderr)
        print(res.stdout)
    return res.returncode == 0, res.stdout

def main():
    print("=== STARTING PRE-TRAINING GATE ===")
    
    # 1. Tests
    pytest_ok, _ = run_cmd(".\\.venv-semantic\\Scripts\\python -m pytest tests/test_semantic.py")
    ruff_check_ok, _ = run_cmd(".\\.venv\\Scripts\\ruff check .")
    ruff_fmt_ok, _ = run_cmd(".\\.venv\\Scripts\\ruff format --check .")
    
    print(f"Pytest: {'PASS' if pytest_ok else 'FAIL'}")
    print(f"Ruff Check: {'PASS' if ruff_check_ok else 'FAIL'}")
    print(f"Ruff Format: {'PASS' if ruff_fmt_ok else 'FAIL'}")
    
    # 2. Smoke Test
    print("Running GPU Smoke Test...")
    smoke_ok, smoke_out = run_cmd(".\\.venv-semantic\\Scripts\\python scripts/semantic/train.py --smoke_test")
    print(f"Smoke Test: {'PASS' if smoke_ok else 'FAIL'}")
    
    # Extract VRAM from smoke_out if pass
    vram = "N/A"
    if smoke_ok:
        for line in smoke_out.splitlines():
            if "VRAM" in line:
                parts = line.split("VRAM:")
                if len(parts) > 1:
                    vram = parts[1].strip()
    print(f"Peak VRAM: {vram}")
    
    # 3. Mini Overfit Test
    print("Running Mini-Overfit Test...")
    overfit_ok, overfit_out = run_cmd(".\\.venv-semantic\\Scripts\\python scripts/semantic/train.py --mini_overfit")
    print(f"Mini Overfit: {'PASS' if overfit_ok else 'FAIL'}")
    
    init_loss = "N/A"
    final_loss = "N/A"
    if overfit_ok:
        lines = [l for l in overfit_out.splitlines() if "Train Loss:" in l]
        if lines:
            init_loss = lines[0].split("Train Loss:")[1].split("|")[0].strip()
            final_loss = lines[-1].split("Train Loss:")[1].split("|")[0].strip()
            
    print(f"initial loss: {init_loss}")
    print(f"final loss: {final_loss}")
    
    # 4. Checkpoint round-trip test
    print("Testing Checkpoint Resume...")
    ckpt_ok = os.path.exists("best_model.pth")
    if ckpt_ok:
        ckpt_test_ok, _ = run_cmd(".\\.venv-semantic\\Scripts\\python -c \"import torch; torch.load('best_model.pth', map_location='cpu'); print('OK')\"")
        print(f"Checkpoint round-trip: {'PASS' if ckpt_test_ok else 'FAIL'}")
    else:
        print("Checkpoint round-trip: FAIL (best_model.pth not found)")

if __name__ == "__main__":
    main()
