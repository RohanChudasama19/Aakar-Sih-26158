import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import inspect
from app.pipeline import dense_backend

src = inspect.getsource(dense_backend)
# Print full dense backend
print(src[:6000])
