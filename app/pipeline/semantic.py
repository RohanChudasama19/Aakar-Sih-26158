"""Transparent geometric/color baseline. These are heuristic labels, not an aerial neural classifier."""

import numpy as np
from scipy.spatial import cKDTree

from .georef import transform


def classify(points, colors, geo, mesh, out):
    p = transform(points, geo)
    c = colors.astype(float)
    labels = np.zeros(len(p), dtype=np.uint8)
    vegetation = (c[:, 1] > c[:, 0] * 1.12) & (c[:, 1] > c[:, 2] * 1.07)
    if geo["valid"]:
        base = np.percentile(p[:, 2], 10)
        elevated = p[:, 2] > base + 2
        labels[elevated] = 1
        neutral = np.ptp(c, axis=1) < 25
        labels[neutral & ~elevated] = 2
    labels[vegetation] = 3
    labels[np.max(c, axis=1) < 35] = 4
    if (out / "cloud.las").exists():
        import laspy

        las = laspy.read(out / "cloud.las")
        las.classification = np.array([2, 6, 11, 5, 1], dtype=np.uint8)[labels]
        las.write(out / "cloud.las")
    names = ["terrain_candidate", "building_candidate", "road_candidate", "vegetation_candidate", "unknown"]
    nearest = cKDTree(p).query(mesh.triangles_center)[1]
    face_labels = labels[nearest]
    areas = mesh.area_faces
    stats = {
        name: {
            "point_fraction_pct": float(np.mean(labels == i) * 100),
            "surface_area": float(areas[face_labels == i].sum()),
        }
        for i, name in enumerate(names)
    }
    np.savez_compressed(out / "semantic_labels.npz", points=p, labels=labels, face_labels=face_labels)
    return {
        "method": "color_height_heuristics",
        "validated": False,
        "area_units": "m2" if geo["valid"] else "relative_units_squared",
        "classes": stats,
        "warning": "Candidate labels only. Roads/buildings can be misclassified; use a trained aerial classifier before operational decisions.",
    }
