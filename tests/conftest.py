import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="aakar-tests-")
os.environ["REDIS_URL"] = ""
os.environ["S3_ENDPOINT"] = ""
os.environ["API_TOKEN"] = ""

# Ensure the DB schema exists for tests that use TestClient (avoids "no such table: jobs" 500s)
from app.db import init_db  # noqa: E402
init_db()
