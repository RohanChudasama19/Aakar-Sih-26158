import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import inspect
from app.pipeline import colmap as colmap_mod

# Full colmap.sparse function
src = inspect.getsource(colmap_mod.sparse)
print(src)
