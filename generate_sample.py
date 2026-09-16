import os
from pathlib import Path

from PIL import Image

os.environ["AERORECON_DATA_DIR"] = str(Path.cwd() / "data")
from app.crud import create_job

from app.db import init_db
from app.pipeline.runner import run_pipeline


async def main():
    await init_db()

    # Create job
    job = await create_job("sample_mission")
    jid = job["id"]
    print(f"Created job: {jid}")

    job_dir = Path("data/jobs") / jid
    inputs_dir = job_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    # Create fake images
    for i in range(3):
        img_path = inputs_dir / f"img_{i}.jpg"
        img = Image.new("RGB", (100, 100), color=(i*50, 100, 150))
        img.save(img_path)

    # Write empty telemetry to avoid failure
    (inputs_dir / "telemetry.csv").write_text("image_file,gps_lat,gps_lon,gps_alt\nimg_0.jpg,0,0,10\nimg_1.jpg,0,0.0001,10\nimg_2.jpg,0,0.0002,10")

    # Override pipeline steps to just produce the artifacts?
    # Or just run the real CPU pipeline! test_pipeline.py runs it in 15 seconds.
    print("Running pipeline...")
    await run_pipeline(jid)
    print("Pipeline complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
