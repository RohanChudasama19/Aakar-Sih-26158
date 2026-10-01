import requests, time, hashlib

for i in range(10):
    try:
        r_glb = requests.get('http://127.0.0.1:8000/api/jobs/mars_hkairport01_quality/files/model.glb')
        r_ply = requests.get('http://127.0.0.1:8000/api/jobs/mars_hkairport01_quality/files/cloud_relative.ply')
        print("GLB status:", r_glb.status_code)
        if r_glb.status_code == 200:
            c = r_glb.content
            print("GLB size:", len(c))
            print("GLB SHA256:", hashlib.sha256(c).hexdigest())
        print("PLY status:", r_ply.status_code)
        break
    except Exception as e:
        time.sleep(2)
