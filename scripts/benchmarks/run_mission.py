import os
from app.pipeline.runner import run_pipeline
import json

out_dir = r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data\1ae9eba0-28ce-45d7-ada7-ed98679e8463\work"
import shutil
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)

res = run_pipeline(
    r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data\1ae9eba0-28ce-45d7-ada7-ed98679e8463\inputs",
    out_dir,
    options={"engine": "colmap", "use_gpu": True, "force_profile": "BALANCED"}
)
print("--- PIPELINE DONE ---")
print(json.dumps(res, indent=2))
