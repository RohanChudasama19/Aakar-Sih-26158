import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import inspect
from app.pipeline import dense_backend as db

src = inspect.getsource(db.ColmapPatchMatchBackend.run)
# Print the patch-match.cfg construction section
lines = src.splitlines()
for i, l in enumerate(lines):
    if 'patch-match' in l.lower() or 'pm_photo' in l.lower() or 'source_images' in l.lower() or 'cfg_lines' in l.lower():
        print(f"L{i}: {l}")
