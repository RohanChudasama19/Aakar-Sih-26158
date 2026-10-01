import requests
import time

url = "http://127.0.0.1:8000/api/jobs"

files = {
    'video': ('video.mp4', open('demo/fast_quality_demo/video.mp4', 'rb'), 'video/mp4'),
    'gps': ('gps.csv', open('demo/fast_quality_demo/gps.csv', 'rb'), 'text/csv'),
    'flight': ('flight.json', open('colorado_dataset/flight.json', 'rb'), 'application/json')
}

data = {
    'name': 'Production Validation Mission',
    'engine': 'colmap',
    'profile': 'FAST_QUALITY'
}

print("Submitting job...")
response = requests.post(url, files=files, data=data)
print(response.status_code)
print(response.text)
