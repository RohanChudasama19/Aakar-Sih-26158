from abc import ABC, abstractmethod

import cv2
import numpy as np
import trimesh
from PIL import Image


class TextureBackend(ABC):
    @abstractmethod
    def run(self, mesh, geo, sfm, k, directory, options):
        pass


class AeroreconTextureBackend(TextureBackend):
    def run(self, mesh, geo, sfm, k, directory, options):

        xyz = mesh.vertices
        if geo["metric_state"] != "RELATIVE":
            xyz = (mesh.vertices - geo["translation"]) @ geo["rotation"] / geo["scale"]

        cam_centers = np.array([-pose[:, :3].T @ pose[:, 3] for pose in sfm["poses"].values()])
        c_min, c_max = cam_centers.min(0), cam_centers.max(0)
        m_min, m_max = xyz.min(0), xyz.max(0)

        # Sane bounds check (camera centers should be reasonably close to the scene)
        if np.any(m_max < c_min - 1000) or np.any(m_min > c_max + 1000):
            raise ValueError("Coordinate-frame mismatch detected in texture projection.")


        triangles = xyz[mesh.faces]
        centroids = triangles.mean(1)

        # Calculate face normals
        normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        normal_norm = np.linalg.norm(normal, axis=1, keepdims=True) + 1e-12
        normal /= normal_norm

        # Normalize all pose keys to int so str-key callers ("1","2"…) and
        # int-key callers (1,2…) both work.  This must happen before `selected`
        # is populated and before `loaded` is built, so every dict shares the
        # same key type and `selected[f] in loaded` is always a valid lookup.
        poses_int: dict = {int(k): v for k, v in sfm["poses"].items()}

        score = np.zeros(len(triangles))
        selected = np.full(len(triangles), -1, int)
        projections = {}

        for j, pose in poses_int.items():
            image_path = directory / f"{int(j):06d}.png"
            if not image_path.exists():
                continue

            image = cv2.imread(str(image_path))
            if image is None:
                continue

            h, w = image.shape[:2]
            cam = xyz @ pose[:, :3].T + pose[:, 3]
            p = cam @ k.T
            uv = p[:, :2] / np.maximum(p[:, 2:3], 1e-8)
            triuv = uv[mesh.faces]

            # Base inside checks
            inside = (
                (triuv[:, :, 0] >= 1)
                & (triuv[:, :, 0] < w - 1)
                & (triuv[:, :, 1] >= 1)
                & (triuv[:, :, 1] < h - 1)
                & (cam[mesh.faces, 2] > 0)
            ).all(1)

            # Dynamic masks
            mask_path = directory.parent / "masks" / f"{int(j):06d}.png.png"
            if mask_path.exists():
                mask = cv2.imread(str(mask_path), 0)
                if mask is not None:
                    check = np.concatenate([triuv, triuv.mean(1, keepdims=True)], axis=1).astype(int)
                    inside &= (mask[np.clip(check[:, :, 1], 0, h - 1), np.clip(check[:, :, 0], 0, w - 1)] > 0).all(1)

            # Occlusion testing using Open3D RaycastingScene (very fast)
            if inside.any() and options.get("occlusion_test", False):
                try:
                    # Initialize Open3D raycaster once per mesh if not already done
                    if getattr(mesh, "_o3d_ray_scene", None) is None:
                        import open3d as o3d

                        o3d_mesh = o3d.t.geometry.TriangleMesh()
                        o3d_mesh.vertex.positions = o3d.core.Tensor(np.asarray(xyz, dtype=np.float32))
                        o3d_mesh.triangle.indices = o3d.core.Tensor(np.asarray(mesh.faces, dtype=np.uint32))
                        scene = o3d.t.geometry.RaycastingScene()
                        scene.add_triangles(o3d_mesh)
                        mesh._o3d_ray_scene = scene

                    ray_origins = (-pose[:, :3].T @ pose[:, 3]).reshape(1, 3)
                    ray_origins = np.repeat(ray_origins, np.sum(inside), axis=0)
                    ray_directions = centroids[inside] - ray_origins

                    # Construct rays tensor [origins, directions]
                    rays = np.concatenate([ray_origins, ray_directions], axis=1).astype(np.float32)
                    rays_tensor = o3d.core.Tensor(rays)

                    # Cast rays
                    ans = mesh._o3d_ray_scene.cast_rays(rays_tensor)
                    index_ray = ans["primitive_ids"].numpy()

                    visible_faces = np.where(inside)[0]

                    # It intersects the target face first
                    occluded = index_ray != visible_faces

                    # Update inside mask
                    inside[visible_faces[occluded]] = False
                except Exception as e:
                    import warnings

                    warnings.warn(f"Occlusion testing failed: {e}")
                    pass  # Fallback to no occlusion test

            view = (-pose[:, :3].T @ pose[:, 3]) - centroids
            distance = np.linalg.norm(view, axis=1)
            angle = np.abs(np.sum(normal * view, axis=1)) / (distance + 1e-9)

            # Weight by resolution and viewing angle
            weight = inside * angle / (distance**2 + 1e-9)
            better = weight > score

            selected[better] = j
            score[better] = weight[better]
            projections[j] = uv

        grid = int(np.ceil(np.sqrt(len(triangles))))
        tile = options.get("atlas_tile_size", max(4, min(32, 4096 // max(1, grid))))
        atlas_size = grid * tile

        atlas = np.full((atlas_size, atlas_size, 3), 120, np.uint8)
        coords = []

        loaded = {
            j: cv2.imread(str(directory / f"{int(j):06d}.png"))
            for j in poses_int
            if (directory / f"{int(j):06d}.png").exists()
        }
        aa, bb = np.meshgrid(np.linspace(0, 1, tile), np.linspace(0, 1, tile))
        b = np.minimum(bb, 1 - aa)

        # Photometric exposure normalization
        if options.get("exposure_normalization", True) and len(loaded) > 0:
            # simple mean brightness scaling
            means = {j: loaded[j].mean() for j in loaded}
            global_mean = np.mean(list(means.values()))
            for j in loaded:
                ratio = global_mean / (means[j] + 1e-5)
                # prevent extreme scaling
                ratio = np.clip(ratio, 0.5, 2.0)
                loaded[j] = cv2.convertScaleAbs(loaded[j], alpha=ratio, beta=0)

        for f, face in enumerate(mesh.faces):
            row, col = divmod(f, grid)
            if selected[f] >= 0 and selected[f] in loaded and loaded[selected[f]] is not None:
                tri = projections[selected[f]][face]
                uv = tri[0] + aa[:, :, None] * (tri[1] - tri[0]) + b[:, :, None] * (tri[2] - tri[0])
                sampled = cv2.remap(
                    loaded[selected[f]],
                    uv[:, :, 0].astype(np.float32),
                    uv[:, :, 1].astype(np.float32),
                    cv2.INTER_LINEAR,
                )
                atlas[row * tile : (row + 1) * tile, col * tile : (col + 1) * tile] = sampled[:, :, ::-1]
            else:
                atlas[row * tile : (row + 1) * tile, col * tile : (col + 1) * tile] = mesh.visual.vertex_colors[
                    face, :3
                ].mean(0)

            x, y = col * tile, row * tile
            coords.extend(
                [
                    ((x + 0.5) / atlas_size, 1 - (y + 0.5) / atlas_size),
                    ((x + tile - 0.5) / atlas_size, 1 - (y + 0.5) / atlas_size),
                    ((x + 0.5) / atlas_size, 1 - (y + tile - 0.5) / atlas_size),
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
        result.metadata["mean_viewing_angle"] = float(np.mean(score[selected >= 0]) if np.any(selected >= 0) else 0)
        result.metadata["atlas_resolution"] = f"{atlas_size}x{atlas_size}"

        return result


class ColmapMeshTexturerBackend(TextureBackend):
    def run(self, mesh, geo, sfm, k, directory, options):
        # Fallback to python backend if colmap doesn't exist or isn't viable right now
        return AeroreconTextureBackend().run(mesh, geo, sfm, k, directory, options)


def texture_mesh(mesh, geo, sfm, k, directory, options=None):
    if options is None:
        options = {}

    backend_choice = options.get("texture_backend", "AERORECON_TEXTURE")
    if backend_choice == "COLMAP_MESH_TEXTURER":
        backend = ColmapMeshTexturerBackend()
    else:
        backend = AeroreconTextureBackend()

    return backend.run(mesh, geo, sfm, k, directory, options)
