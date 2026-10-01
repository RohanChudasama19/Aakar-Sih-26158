import sqlite3
import numpy as np

db = "workspace/HKairport01_FAST_C_FINAL/inputs/colmap.db"
conn = sqlite3.connect(db)

# Create a test prior
image_id = 1
position = np.array([1.0, 2.0, 3.0], dtype=np.float64).tobytes()
cov = np.eye(3, dtype=np.float64).tobytes()
# corr_sensor_type = 0 (maybe IMAGE?), corr_sensor_id = 1
conn.execute("INSERT OR REPLACE INTO pose_priors (pose_prior_id, corr_data_id, corr_sensor_id, corr_sensor_type, position, position_covariance, coordinate_system) VALUES (1, 1, 1, 0, ?, ?, 0)", (position, cov))
conn.commit()
conn.close()
