import trimesh
import os
import glob

colorado_dir = 'data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs'
glb_path = os.path.join(colorado_dir, 'model.glb')

print("Loading GLB...")
try:
    glb = trimesh.load(glb_path, force='mesh')
    print(f"GLB Faces: {len(glb.faces)}")
except Exception as e:
    print(e)
    
ply_files = glob.glob(os.path.join(colorado_dir, '*.ply'))
for p in ply_files:
    try:
        mesh = trimesh.load(p)
        if hasattr(mesh, 'faces'):
            print(f"{os.path.basename(p)} Faces: {len(mesh.faces)}")
    except:
        pass
