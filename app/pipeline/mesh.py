import cv2
import numpy as np
import trimesh
from PIL import Image

from .georef import transform


def build_mesh(points, colors, geo, sfm, k, directory, max_vertices=None):
    from .surface import reconstruct_surface

    local = transform(points, geo)
    cameras = np.array([-p[:, :3].T @ p[:, 3] for p in sfm["poses"].values()])
    cameras = transform(cameras, geo)
    surface, report = reconstruct_surface(local, colors, cameras)
    result = texture_mesh(surface, geo, sfm, k, directory)
    report["textured_face_fraction"] = float(result.metadata["textured_face_fraction"])
    if report["textured_face_fraction"] < 0.5:
        report["surface_quality"] = "LOW_TEXTURE_SUPPORT"
    return result, report


def texture_mesh(mesh, geo, sfm, k, directory):
    # Face atlas prevents seam UV ambiguity. Each tile samples one original camera.
    xyz = (mesh.vertices - geo["translation"]) @ geo["rotation"] / geo["scale"]
    triangles = xyz[mesh.faces]
    centroids = triangles.mean(1)
    normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normal /= np.linalg.norm(normal, axis=1, keepdims=True) + 1e-12
    score = np.zeros(len(triangles))
    selected = np.full(len(triangles), -1, int)
    projections = {}
    for j, pose in sfm["poses"].items():
        image = cv2.imread(str(directory / f"{j:06d}.png"))
        h, w = image.shape[:2]
        cam = xyz @ pose[:, :3].T + pose[:, 3]
        p = cam @ k.T
        uv = p[:, :2] / np.maximum(p[:, 2:3], 1e-8)
        triuv = uv[mesh.faces]
        inside = (
            (triuv[:, :, 0] >= 1)
            & (triuv[:, :, 0] < w - 1)
            & (triuv[:, :, 1] >= 1)
            & (triuv[:, :, 1] < h - 1)
            & (cam[mesh.faces, 2] > 0)
        ).all(1)
        # Dynamic masks exclude both triangle vertices and center from texture choice.
        mask = cv2.imread(str(directory.parent / "masks" / f"{j:06d}.png.png"), 0)
        check = np.concatenate([triuv, triuv.mean(1, keepdims=True)], axis=1).astype(int)
        inside &= (mask[np.clip(check[:, :, 1], 0, h - 1), np.clip(check[:, :, 0], 0, w - 1)] > 0).all(1)
        view = (-pose[:, :3].T @ pose[:, 3]) - centroids
        distance = np.linalg.norm(view, axis=1)
        angle = np.abs(np.sum(normal * view, axis=1)) / (distance + 1e-9)
        weight = inside * angle / (distance**2 + 1e-9)
        better = weight > score
        selected[better] = j
        score[better] = weight[better]
        projections[j] = uv
    grid = int(np.ceil(np.sqrt(len(triangles))))
    tile = max(4, min(32, 4096 // grid))
    atlas = np.full((grid * tile, grid * tile, 3), 120, np.uint8)
    coords = []
    loaded = {j: cv2.imread(str(directory / f"{j:06d}.png")) for j in sfm["poses"]}
    aa, bb = np.meshgrid(np.linspace(0, 1, tile), np.linspace(0, 1, tile))
    # The upper triangle is used; duplicate edge texels keep interpolation stable.
    b = np.minimum(bb, 1 - aa)
    for f, face in enumerate(mesh.faces):
        row, col = divmod(f, grid)
        if selected[f] >= 0:
            tri = projections[selected[f]][face]
            uv = tri[0] + aa[:, :, None] * (tri[1] - tri[0]) + b[:, :, None] * (tri[2] - tri[0])
            sampled = cv2.remap(
                loaded[selected[f]], uv[:, :, 0].astype(np.float32), uv[:, :, 1].astype(np.float32), cv2.INTER_LINEAR
            )
            atlas[row * tile : (row + 1) * tile, col * tile : (col + 1) * tile] = sampled[:, :, ::-1]
        else:
            atlas[row * tile : (row + 1) * tile, col * tile : (col + 1) * tile] = mesh.visual.vertex_colors[
                face, :3
            ].mean(0)
        x, y = col * tile, row * tile
        size = grid * tile
        coords.extend(
            [
                ((x + 0.5) / size, 1 - (y + 0.5) / size),
                ((x + tile - 0.5) / size, 1 - (y + 0.5) / size),
                ((x + 0.5) / size, 1 - (y + tile - 0.5) / size),
            ]
        )
    result = trimesh.Trimesh(
        mesh.vertices[mesh.faces].reshape(-1, 3),
        np.arange(len(mesh.faces) * 3).reshape(-1, 3),
        vertex_normals=mesh.vertex_normals[mesh.faces].reshape(-1, 3),
        process=False,
    )
    material = trimesh.visual.material.PBRMaterial(
        baseColorTexture=Image.fromarray(atlas),
        baseColorFactor=[255, 255, 255, 255],
        metallicFactor=0.0,
        roughnessFactor=1.0,
        doubleSided=True,
    )
    result.visual = trimesh.visual.texture.TextureVisuals(uv=np.asarray(coords), material=material)
    result.metadata["textured_face_fraction"] = float(np.mean(selected >= 0))
    return result
