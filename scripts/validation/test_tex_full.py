import json
import numpy as np
import trimesh
from pathlib import Path
import open3d as o3d

work = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data\b3198000-1dd2-4a74-95ee-937f56510279\work")
mesh = trimesh.load(str(work / "outputs" / "mesh_raw.ply"))
geo = json.loads((work / "alignment.json").read_text())
sfm = {"poses": {}}
poses = json.loads((work / "poses.json").read_text())
for k, v in poses.items():
    sfm["poses"][int(k)] = np.array(v)

import json
flight = json.loads((work.parent / "inputs" / "flight.json").read_text())
from app.schemas import intrinsics
cam_model = intrinsics(flight, 1600, 900)
K = cam_model.to_matrix()

from app.pipeline.texture import AeroreconTextureBackend
options = {"occlusion_test": True, "exposure_normalization": True, "atlas_tile_size": 16}
backend = AeroreconTextureBackend()

out_mesh = backend.run(mesh, geo, sfm, K, work / "frames", options)
out_mesh.export(str(work / "outputs" / "mesh_textured_test.glb"))

print("atlas size:", out_mesh.visual.material.image.size)
tf = float(out_mesh.metadata.get("textured_face_fraction", 0.0))
print("textured faces:", int(tf * len(mesh.faces)))
print("total supported faces:", len(mesh.faces))
print("coverage %:", round(tf * 100, 2))
