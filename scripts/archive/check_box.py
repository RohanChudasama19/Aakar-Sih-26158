import json
import urllib.request
url = 'http://127.0.0.1:8000/api/jobs/mars_hkairport01_quality/files/model.glb'
urllib.request.urlretrieve(url, 'temp.glb')
