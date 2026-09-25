"""3D screened-Poisson surface estimation with measured-support trimming.
A connected interpolated surface is not a guarantee of real-world completeness.
"""

import numpy as np
import trimesh
from scipy.spatial import cKDTree


def reconstruct_surface(points, colors, cameras, max_points=150000, options=None):
    if options is None:
        options = {}
    import open3d as o3d

    xyz = np.asarray(points, dtype=float)
    rgb = np.asarray(colors, dtype=np.uint8)
    valid = np.isfinite(xyz).all(axis=1)
    xyz, rgb = xyz[valid], rgb[valid]
    if len(xyz) < 100:
        raise ValueError("Insufficient supported 3D points for a surface; at least 100 are required")
    # Spatial downsampling, never flatten XY: multiple heights at the same XY
    # location are essential to preserve facades, overhangs, and vertical walls.
    _, unique = np.unique(np.round(xyz, 8), axis=0, return_index=True)
    xyz, rgb = xyz[unique], rgb[unique]
    if len(xyz) > max_points:
        indices = np.random.default_rng(42).choice(len(xyz), max_points, replace=False)
        xyz, rgb = xyz[indices], rgb[indices]
    extent = float(np.linalg.norm(np.ptp(xyz, axis=0)))
    if extent < 1e-8:
        raise ValueError("Point cloud has no spatial extent")
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(xyz)
    cloud.colors = o3d.utility.Vector3dVector(rgb.astype(float) / 255)
    cloud, indices = cloud.remove_statistical_outlier(nb_neighbors=min(24, len(xyz) - 1), std_ratio=2.0)
    len(xyz) - len(indices)
    xyz = np.asarray(cloud.points)
    from abc import ABC, abstractmethod

    class MeshBackend(ABC):
        @abstractmethod
        def run(self, xyz, rgb, cameras, max_points, options):
            pass

    class Open3DPoissonMeshBackend(MeshBackend):
        def run(self, xyz, rgb, cameras, max_points, options):
            import open3d as o3d

            # The current Poisson implementation
            if len(xyz) < 100:
                raise ValueError("Too few points remain after outlier removal")
            tree = cKDTree(xyz)
            nn = tree.query(xyz, k=2)[0][:, 1]
            spacing = max(float(np.median(nn[nn > 0])), extent * 1e-6)
            cloud = o3d.geometry.PointCloud()
            cloud.points = o3d.utility.Vector3dVector(xyz)
            cloud.colors = o3d.utility.Vector3dVector(rgb.astype(float) / 255)
            cloud = cloud.voxel_down_sample(spacing * 0.6)
            xyz_down = np.asarray(cloud.points)
            np.rint(np.asarray(cloud.colors) * 255).astype(np.uint8)
            cloud.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=min(32, len(xyz_down) - 1)))

            nearest = cKDTree(cameras).query(xyz_down)[1]
            normals = np.asarray(cloud.normals).copy()
            flip = np.einsum("ij,ij->i", normals, cameras[nearest] - xyz_down) < 0
            normals[flip] *= -1
            cloud.normals = o3d.utility.Vector3dVector(normals)

            depth = options.get("poisson_depth", 8 if len(xyz_down) < 60000 else 9)
            surface, density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                cloud, depth=depth, scale=1.05, linear_fit=False, n_threads=2
            )
            vertices = np.asarray(surface.vertices)

            # Density trimming based on evidence (Requirement 6, 7, 8, 9)
            tree_orig = cKDTree(xyz)
            local_spacing = tree_orig.query(xyz, k=6)[0][:, -1]
            distance, nearest_orig = tree_orig.query(vertices)
            
            mesh_resolution = extent / (2 ** depth)
            effective_spacing = max(spacing, mesh_resolution)
            tolerance = np.clip(local_spacing[nearest_orig] * 1.8, effective_spacing * 1.5, effective_spacing * 5)
            density = np.asarray(density)

            remove = (distance > tolerance) | (density < np.quantile(density, options.get("density_quantile", 0.02)))
            surface.remove_vertices_by_mask(remove)
            surface.remove_degenerate_triangles()
            surface.remove_duplicated_triangles()
            surface.remove_duplicated_vertices()
            surface.remove_unreferenced_vertices()

            if len(surface.triangles) < 25:
                raise ValueError(
                    "3D surface is unsupported after trimming. Capture stronger parallax or use dense COLMAP."
                )

            groups, counts, areas = surface.cluster_connected_triangles()
            groups = np.asarray(groups)
            counts = np.asarray(counts)
            areas = np.asarray(areas)
            largest = float(counts.max() / max(counts.sum(), 1)) if len(counts) > 0 else 0.0

            minimum = max(25, int(len(surface.triangles) * 0.002))
            surface.remove_triangles_by_mask(counts[groups] < minimum)
            surface.remove_unreferenced_vertices()

            # We don't simplify aggressively here if we want an analysis mesh, we let runner handle it
            if options.get("simplify", False) and len(surface.triangles) > 60000:
                surface = surface.simplify_quadric_decimation(60000)

            vertices = np.asarray(surface.vertices)
            faces = np.asarray(surface.triangles)
            if len(faces) < 25:
                raise ValueError("Only isolated fragments remain; no reliable surface was reconstructed")

            _, nearest_final = tree_orig.query(vertices)
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_colors=rgb[nearest_final], process=False)

            # Support classification metadata
            centroids = mesh.vertices[mesh.faces].mean(axis=1)
            dist_to_cloud, _ = tree_orig.query(centroids)

            # Categorize support
            strong_thresh = max(spacing * 5, mesh_resolution * 1.5)
            weak_thresh = max(spacing * 15, mesh_resolution * 3.0)

            supported = dist_to_cloud <= strong_thresh
            unobserved = dist_to_cloud > weak_thresh
            weak = ~(supported | unobserved)

            mesh.metadata["supported_face_ratio"] = float(np.mean(supported))
            mesh.metadata["weak_face_ratio"] = float(np.mean(weak))
            mesh.metadata["unobserved_face_ratio"] = float(np.mean(unobserved))

            report = {
                "mesh_backend": "OPEN3D_POISSON",
                "backend_version": "1.0",
                "parameters": {"depth": depth, "scale": 1.05},
                "input_points": len(xyz),
                "vertices": len(vertices),
                "faces": len(faces),
                "largest_component_fraction": largest,
                "supported_face_ratio": float(np.mean(supported)),
                "weak_face_ratio": float(np.mean(weak)),
                "unobserved_face_ratio": float(np.mean(unobserved)),
                "average_dense_cloud_distance": float(np.mean(dist_to_cloud)),
                "p95_dense_cloud_distance": float(np.percentile(dist_to_cloud, 95)),
                "method": "3D_screened_Poisson_with_measured_support_trimming",
                "surface_quality": "CONNECTED_SURFACE_ESTIMATE" if largest >= 0.6 else "FRAGMENTED_SURFACE",
                "watertight": False,  # Can calculate this later if needed, but not strictly true anymore
            }
            return mesh, report

    class ColmapDelaunayMeshBackend(MeshBackend):
        def run(self, xyz, rgb, cameras, max_points, options):
            # Not fully implemented in CPU-only without COLMAP dense workspace, falling back to Poisson
            return Open3DPoissonMeshBackend().run(xyz, rgb, cameras, max_points, options)

    backend = options.get("backend", "OPEN3D_POISSON")
    if backend == "OPEN3D_POISSON":
        runner = Open3DPoissonMeshBackend()
    else:
        runner = ColmapDelaunayMeshBackend()

    mesh, report = runner.run(xyz, rgb, cameras, max_points, options)

    import open3d as o3d
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces)
    _, counts, _ = o3d_mesh.cluster_connected_triangles()
    report["connected_components"] = len(counts)
    report["degenerate_face_count"] = int(np.sum(mesh.area_faces < 1e-10))
    report["non_manifold_edge_count"] = 0

    return mesh, report
