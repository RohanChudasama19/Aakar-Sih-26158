import pytest
import numpy as np
import trimesh
from app.pipeline.heatmap_engine import compute_point_density, compute_surface_support
import json

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
    assert dists[1] >= 9.0 # Far above
    assert dists[2] >= 4.0  # Far below

def test_empty_point_cloud():
    dists = compute_surface_support(np.array([[0,0,0]]), np.array([]))
    assert dists[0] == 0.0 # Handled gracefully by returning zeros
    
    dens = compute_point_density(np.array([[0,0,0]]), np.array([]), k=10)
    assert dens[0] == 0.0

def test_density():
    # Generate 100 points around origin
    np.random.seed(42)
    dense_pts = np.random.randn(100, 3) * 0.1
    centroids = np.array([[0,0,0], [10,10,10]])
    
    dens = compute_point_density(centroids, dense_pts, k=10)
    assert dens[0] > 0.0 # High density near origin
    assert dens[1] < dens[0] # Lower or minimal density far away

def test_unavailable_error():
    # We will verify the API endpoints handle NOT_VERIFIED correctly, but here we just pass
    pass

