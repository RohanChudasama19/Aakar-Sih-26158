import os
import subprocess
import json
import time

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode == 0, res.stdout

def main():
    print("=== STARTING REAL TEST ===")
    ok, out = run_cmd(".\\.venv-semantic\\Scripts\\python scripts/semantic/train.py --epochs 1")
    print(out)
    
    ok, out = run_cmd(".\\.venv-semantic\\Scripts\\python scripts/semantic/export_onnx.py")
    print(out)

if __name__ == "__main__":
    main()
