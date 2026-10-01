import requests
import time
import sys
import shutil

video_path = 'demo/live_mars_input/derived_mars_video.mp4'
pid = 'baed1f34-c548-4511-8218-99bdc1d9a6fc'

files = {
    'video': open(video_path, 'rb'),
    'gps': open('samples/gps.csv', 'rb'),
    'flight': open('flight_20s.json', 'rb')
}
data = {
    'name': 'MARS Video Full Quality Rehearsal',
    'project_id': pid,
    'profile': 'QUALITY',
    'engine': 'colmap',
    'max_frames': 600
}

r = requests.post('http://127.0.0.1:8000/api/jobs', files=files, data=data)
if r.status_code not in (200, 201, 202):
    print(f"Failed to submit: {r.text}")
    sys.exit(1)

jid = r.json()['id']
print(f"Submitted Job ID: {jid}")
with open("rehearsal_job_id.txt", "w") as f:
    f.write(jid)

# Track storage
free_before = shutil.disk_usage("C:/").free
peak_used = 0
start_time = time.time()

print(f"Starting free space: {free_before / (1024**3):.2f} GB")

while True:
    st = requests.get(f'http://127.0.0.1:8000/api/jobs/{jid}').json()
    status = st['status']
    print(f"[{time.time()-start_time:.1f}s] Status: {status}")
    
    current_free = shutil.disk_usage("C:/").free
    used_so_far = free_before - current_free
    if used_so_far > peak_used:
        peak_used = used_so_far
        
    if status in ('completed', 'failed', 'RECONSTRUCTION_BLOCKED', 'cancelled'):
        print("Final Report:")
        if 'report' in st and st['report']:
            import json
            print(json.dumps(st['report'], indent=2))
        else:
            print("No report returned.")
        break
    time.sleep(10)

total_time = time.time() - start_time
free_after = shutil.disk_usage("C:/").free

print(f"Total time: {total_time:.2f}s")
print(f"Peak storage used: {peak_used / (1024**3):.2f} GB")
print(f"Final free space: {free_after / (1024**3):.2f} GB")
