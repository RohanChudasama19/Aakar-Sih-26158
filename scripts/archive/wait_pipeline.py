import time
from pathlib import Path

job_id = "6ffe72c9-c309-4f1f-91a6-6385e4ee6b34"
events_file = Path(f"data/{job_id}/work/events.jsonl")

print("Waiting for pipeline to complete...")
while True:
    if events_file.exists():
        try:
            with open(events_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if "Packaging output" in last_line or "Zip packaging" in last_line or "Artifact generation" in last_line or "Exporting artifacts" in last_line:
                        print("Pipeline reached packaging!")
                        time.sleep(10) # wait a bit for it to finish
                        break
                    if "failed" in last_line.lower() or "error" in last_line.lower():
                        # sometimes error is just a warning, let's just check if process exited
                        pass
        except Exception:
            pass
            
    # Also check if mission_report.json exists
    if Path(f"data/{job_id}/work/outputs/mission_report.json").exists():
        print("Pipeline mission_report.json created!")
        break
        
    time.sleep(30)
