# The texture UVs are 96.3% in [0,1] range -- that's good projection coverage.
# The gray rendering must be because Open3D doesn't load embedded GLB textures properly.
# The GLB has UVs but no separate texture FILE -- the image atlas is embedded in the binary.
# Let's verify the GLB has an actual embedded atlas image.
import struct, os
from pathlib import Path

glb_path = "demo/mars_hkairport01_quality/mesh.glb"
with open(glb_path, 'rb') as f:
    magic = f.read(4)
    version = struct.unpack('<I', f.read(4))[0]
    length = struct.unpack('<I', f.read(4))[0]
    print(f"GLB magic: {magic} version={version} total_length={length:,}")
    
    # Read chunks
    while f.tell() < length:
        chunk_len = struct.unpack('<I', f.read(4))[0]
        chunk_type = f.read(4)
        chunk_data = f.read(chunk_len)
        print(f"  Chunk type={chunk_type} len={chunk_len:,}")
        if chunk_type == b'JSON':
            j = chunk_data.decode('utf-8', errors='replace')[:200]
            print(f"  JSON preview: {j}")
        elif chunk_type == b'BIN\x00':
            print(f"  Binary chunk: {chunk_len:,} bytes")
