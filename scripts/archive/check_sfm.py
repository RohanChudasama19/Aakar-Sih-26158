import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Inspect what execute_sfm and execute_dense expect
import inspect
from app.pipeline.runner import execute_sfm, execute_dense

print("=== execute_sfm signature ===")
sig_lines = inspect.getsource(execute_sfm).splitlines()
for i, l in enumerate(sig_lines[:50]):
    print(f"L{i}: {l}")

print()
print("=== execute_dense first 40 lines ===")
sig_lines2 = inspect.getsource(execute_dense).splitlines()
for i, l in enumerate(sig_lines2[:40]):
    print(f"L{i}: {l}")
