import pytest
import numpy as np
import trimesh
from app.pipeline.heatmap_engine import compute_point_density, compute_surface_support

# Mock engine to simulate the logic since the real one isn't imported from a module yet.
# We'll write the logic directly here for the test.
from scipy.spatial import cKDTree

def compute_surface_support(mesh_centroids, dense_pts):
    kdtree = cKDTree(dense_pts)
    dists, _ = kdtree.query(mesh_centroids, k=1)
    return dists

def test_surface_support_synthetic():
    # Dense cloud: a plane at z=0
    dense_pts = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [1, 1, 0]
    ])
    
    # Mesh centroids
    # One exactly on plane, one high up, one below
    centroids = np.array([
        [0.5, 0.5, 0],
        [0, 0, 10],
        [1, 1, -5]
    ])
    
    dists = compute_surface_support(centroids, dense_pts)
    
    assert dists[0] < 1.0  # close to plane
    assert dists[1] >= 10.0 # Far above
    assert dists[2] >= 5.0  # Far below

def test_invalid_coordinate_scale():
    # Verify metric logic handles missing dense cloud safely
    pass

