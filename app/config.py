import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("DATA_DIR", str(ROOT / "data"))).resolve()
DATA.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA / 'jobs.db'}")
REDIS_URL = os.getenv("REDIS_URL", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_BUCKET = os.getenv("S3_BUCKET", "aerorecon")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024**3)))
API_TOKEN = os.getenv("API_TOKEN", "")
