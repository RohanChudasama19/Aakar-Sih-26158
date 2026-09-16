import time
from pathlib import Path

import httpx

ROOT = Path.cwd()

def main():
    client = httpx.Client(base_url="http://localhost:8000")

    files = {
        "video": ("sample.mp4", open(ROOT / "samples" / "sample.mp4", "rb")),
        "gps": ("gps.csv", open(ROOT / "samples" / "gps.csv", "rb")),
        "flight": ("flight.json", open(ROOT / "samples" / "flight.json", "rb"))
    }

    res = client.post("/api/jobs", files=files)
    job = res.json()
    jid = job["id"]
    print(f"Created Job: {jid}")

    # Start Processing
    res = client.post(f"/api/jobs/{jid}/start", params={"engine": "cpu"})
    print(f"Started job: {res.status_code}")

    # Wait for completion
    while True:
        res = client.get(f"/api/jobs/{jid}")
        status = res.json()["status"]
        print(f"Status: {status}")
        if status in ["completed", "failed", "error"]:
            break
        time.sleep(2)

    print(f"Final status: {status}")
    if status == "completed":
        print(f"Use Job ID: {jid} for E2E tests.")
        with open("e2e_jid.txt", "w") as out:
            out.write(jid)

if __name__ == '__main__':
    main()
