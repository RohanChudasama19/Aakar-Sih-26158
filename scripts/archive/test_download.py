import requests
import hashlib

def sha256(content):
    return hashlib.sha256(content).hexdigest()

r_glb = requests.get('http://127.0.0.1:8000/api/jobs/mars_hkairport01_quality/files/model.glb')
r_ply = requests.get('http://127.0.0.1:8000/api/jobs/mars_hkairport01_quality/files/cloud_relative.ply')

print("GLB status:", r_glb.status_code)
if r_glb.status_code == 200:
    c = r_glb.content
    print("GLB size:", len(c))
    print("GLB SHA256:", sha256(c))
    print("GLB SHA matches expected:", sha256(c) == "c69eac810289a09273aec8c0aa0b4eb4307b72f7a5b92c420058e3f87bb183a0")

print("PLY status:", r_ply.status_code)
if r_ply.status_code == 200:
    c = r_ply.content
    print("PLY size:", len(c))
    print("PLY SHA256:", sha256(c))
