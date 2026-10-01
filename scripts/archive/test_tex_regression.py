import numpy as np
import trimesh
from app.pipeline.texture import texture_mesh
import cv2
import tempfile
from pathlib import Path

def test_texture_keys():
    mesh = trimesh.Trimesh(vertices=[[0,0,5], [1,0,5], [0,1,5]], faces=[[0,1,2]])
    mesh.visual.vertex_colors = np.array([[255,0,0,255],[0,255,0,255],[0,0,255,255]])
    K = np.array([[500,0,250],[0,500,250],[0,0,1]])
    
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        
        # Test 1: String keys, missing image
        sfm_str = {'poses': {'1': np.eye(3,4)}}
        m1 = texture_mesh(mesh.copy(), {'metric_state': 'RELATIVE'}, sfm_str, K, tdp)
        assert hasattr(m1.visual.material, 'baseColorTexture')
        
        # Test 2: Integer keys, valid image
        img = np.full((500,500,3), 150, dtype=np.uint8)
        cv2.imwrite(str(tdp / "000002.png"), img)
        m2 = texture_mesh(mesh.copy(), {'metric_state': 'RELATIVE'}, {'poses': {2: np.eye(3,4)}}, K, tdp)
        arr = np.array(m2.visual.material.baseColorTexture)
        assert np.abs(np.mean(arr) - 150) < 10
        
        # Test 3: String keys, valid image
        cv2.imwrite(str(tdp / "000003.png"), img)
        m3 = texture_mesh(mesh.copy(), {'metric_state': 'RELATIVE'}, {'poses': {'3': np.eye(3,4)}}, K, tdp)
        arr3 = np.array(m3.visual.material.baseColorTexture)
        assert np.abs(np.mean(arr3) - 150) < 10
        
        print("ALL TEXTURE REGRESSION TESTS PASSED.")

test_texture_keys()
