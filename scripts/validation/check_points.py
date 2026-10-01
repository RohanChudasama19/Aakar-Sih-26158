import trimesh
pc = trimesh.load(r'data\ab067831-368b-4087-a43e-11a08ee0ae74\work\test_B\dense_v1\fused.ply')
print(f'V1 fused points: {len(pc.vertices)}')
