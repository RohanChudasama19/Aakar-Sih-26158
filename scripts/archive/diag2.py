import numpy as np
# Wait! In texture.py:
#         fix_mat = np.eye(4)
#         fix_mat[1, 1] = -1.0
#         fix_mat[2, 2] = -1.0
# This is applied to mesh vertices (which are in Rx180 frame to match mesh_final.ply?? No, mesh_raw is in original frame!)
# If I passed Rx180 to texture_mesh, it might transform the points!
