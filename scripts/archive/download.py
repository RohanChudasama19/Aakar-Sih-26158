import urllib.request
url = "https://raw.githubusercontent.com/colmap/colmap/be5e29107936a5a0f1262d04a74288bde157e007/src/colmap/controllers/incremental_pipeline.cc"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    lines = response.read().decode('utf-8').split('\n')
    for i, line in enumerate(lines):
        if 'Discarding reconstruction' in line:
            print(f"Line {i+1}: {line}")
            for j in range(i-10, i+10):
                print(f"{j+1}: {lines[j]}")
