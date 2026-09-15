"""3D screened-Poisson surface estimation with measured-support trimming.
A connected interpolated surface is not a guarantee of real-world completeness.
"""

import numpy as np
import trimesh
from scipy.spatial import cKDTree


def reconstruct_surface(points, colors, cameras, max_points=150000):
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
    removed = len(xyz) - len(indices)
    xyz = np.asarray(cloud.points)
    if len(xyz) < 100:
        raise ValueError("Too few points remain after outlier removal")
    tree = cKDTree(xyz)
    nn = tree.query(xyz, k=2)[0][:, 1]
    spacing = max(float(np.median(nn[nn > 0])), extent * 1e-6)
    cloud = cloud.voxel_down_sample(spacing * 0.6)
    xyz = np.asarray(cloud.points)
    rgb = np.rint(np.asarray(cloud.colors) * 255).astype(np.uint8)
    cloud.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=min(32, len(xyz) - 1)))
    # Orient local surface normals towards the nearest observed camera. Unlike a
    # global +Z rule this allows arbitrary facades and relative coordinate frames.
    cameras = np.asarray(cameras, dtype=float)
    if cameras.ndim != 2 or cameras.shape[1] != 3 or not len(cameras):
        raise ValueError("Surface reconstruction requires observed camera centres")
    nearest = cKDTree(cameras).query(xyz)[1]
    normals = np.asarray(cloud.normals).copy()
    flip = np.einsum("ij,ij->i", normals, cameras[nearest] - xyz) < 0
    normals[flip] *= -1
    cloud.normals = o3d.utility.Vector3dVector(normals)
    depth = 8 if len(xyz) < 60000 else 9
    surface, density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        cloud, depth=depth, scale=1.05, linear_fit=False, n_threads=2
    )
    vertices = np.asarray(surface.vertices)
    tree = cKDTree(xyz)
    local_spacing = tree.query(xyz, k=6)[0][:, -1]
    distance, nearest = tree.query(vertices)
    # Trim areas too far from any measured point rather than retaining Poisson's
    # extrapolated enclosing sheet. Local support handles variable point density.
    tolerance = np.clip(local_spacing[nearest] * 1.8, spacing * 3, spacing * 15)
    density = np.asarray(density)
    remove = (distance > tolerance) | (density < np.quantile(density, 0.02))
    surface.remove_vertices_by_mask(remove)
    surface.remove_degenerate_triangles()
    surface.remove_duplicated_triangles()
    surface.remove_duplicated_vertices()
    surface.remove_unreferenced_vertices()
    if len(surface.triangles) < 25:
        raise ValueError("3D surface is unsupported after trimming. Capture stronger parallax or use dense COLMAP.")
    groups, counts, areas = surface.cluster_connected_triangles()
    groups = np.asarray(groups)
    counts = np.asarray(counts)
    minimum = max(25, int(len(surface.triangles) * 0.002))
    surface.remove_triangles_by_mask(counts[groups] < minimum)
    surface.remove_unreferenced_vertices()
    if len(surface.triangles) > 60000:
        surface = surface.simplify_quadric_decimation(60000)
    vertices = np.asarray(surface.vertices)
    faces = np.asarray(surface.triangles)
    if len(faces) < 25:
        raise ValueError("Only isolated fragments remain; no reliable surface was reconstructed")
    _, nearest = tree.query(vertices)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_colors=rgb[nearest], process=False)
    groups, counts, areas = surface.cluster_connected_triangles()
    areas = np.asarray(areas)
    counts = np.asarray(counts)
    largest = float(areas.max() / max(areas.sum(), 1e-12))
    status = "CONNECTED_SURFACE_ESTIMATE" if largest >= 0.6 else "FRAGMENTED_SURFACE"
    report = {
        "method": "3D_screened_Poisson_with_measured_support_trimming",
        "input_points": len(points),
        "filtered_points": len(xyz),
        "statistical_outliers_removed": removed,
        "poisson_depth": depth,
        "vertices": len(vertices),
        "faces": len(faces),
        "components": len(counts),
        "largest_component_area_fraction": largest,
        "surface_quality": status,
        "watertight": bool(mesh.is_watertight),
        "note": "True 3D interpolation preserves vertical surfaces. Interpolated areas are estimates; holes, softened detail and unobserved surfaces remain possible. Connectivity is not accuracy or completeness.",
    }
    return mesh, report
