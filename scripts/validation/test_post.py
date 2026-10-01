import requests
import json
url = "http://127.0.0.1:8000/api/jobs"
files = {
    "video": ("video.mp4", b"dummy video content", "video/mp4"),
    "gps": ("gps.csv", b"dummy gps content", "text/csv"),
    "flight": ("flight.json", b"{}", "application/json"),
}
data = {
    "name": "Test Mission",
    "engine": "cpu",
    "max_frames": "60",
}
resp = requests.post(url, data=data, files=files)
print(resp.status_code)
print(resp.text)
