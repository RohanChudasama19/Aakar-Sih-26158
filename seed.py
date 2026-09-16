import asyncio
import os
from pathlib import Path

from app.db import init_db


async def seed():
    os.environ["AERORECON_DATA_DIR"] = str(Path.cwd() / "data")
    await init_db()

    # Check if a completed job exists
    jobs_dir = Path("data/jobs")
    if jobs_dir.exists():
        for jid in jobs_dir.iterdir():
            manifest = jid / "manifest.json"
            if manifest.exists():
                print(f"Found existing job: {jid.name}")
                return jid.name

    print("No completed job found. Cannot run E2E without artifacts.")
    return None

if __name__ == '__main__':
    asyncio.run(seed())
