import requests

s_url = "http://127.0.0.1:8000/api/samples"
url = "http://127.0.0.1:8000/api/jobs"

video = requests.get(s_url + "/sample.mp4").content
gps = requests.get(s_url + "/gps.csv").content
flight = requests.get(s_url + "/flight.json").content

files = {
    "video": ("sample.mp4", video, "video/mp4"),
    "gps": ("gps.csv", gps, "text/csv"),
    "flight": ("flight.json", flight, "application/json"),
}
data = {
    "name": "Synthetic campus smoke test",
    "engine": "cpu",
    "max_frames": "60",
}
resp = requests.post(url, data=data, files=files)
print(resp.status_code)
print(resp.text)
