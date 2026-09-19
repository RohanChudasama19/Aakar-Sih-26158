# Sensor Fusion Data Readiness

This report tracks the availability of genuine sensor data required for Phase D (Sensor Fusion) testing, extracted directly from the verified real dataset samples.

| Field | MARS-LVIG | Zurich Urban MAV |
|-------|-----------|------------------|
| **RGB** | ACCESS_BLOCKED | AVAILABLE |
| **frame timestamps** | ACCESS_BLOCKED | AVAILABLE |
| **GPS** | ACCESS_BLOCKED | AVAILABLE |
| **IMU accel** | ACCESS_BLOCKED | AVAILABLE |
| **IMU gyro** | ACCESS_BLOCKED | AVAILABLE |
| **orientation** | ACCESS_BLOCKED | NOT_AVAILABLE |
| **barometer** | ACCESS_BLOCKED | AVAILABLE |
| **RTK** | ACCESS_BLOCKED | NOT_AVAILABLE |
| **ground-truth trajectory** | ACCESS_BLOCKED | AVAILABLE |
| **intrinsics** | ACCESS_BLOCKED | AVAILABLE |
| **camera-IMU extrinsics** | ACCESS_BLOCKED | AVAILABLE |
| **gimbal** | ACCESS_BLOCKED | NOT_AVAILABLE |
| **absolute timestamp** | ACCESS_BLOCKED | NOT_AVAILABLE |
| **coordinate frames documented** | ACCESS_BLOCKED | AVAILABLE |
| **real adapter verified** | ACCESS_BLOCKED | AVAILABLE |

*Note: MARS-LVIG requires a manual download by the user to bypass Google Drive limitations before its schema and exact availability can be confirmed.*


### Phase D Validations
- Zurich temporal synchronization: VERIFIED_REAL_DATA
- Zurich IMU coordinate convention: UNKNOWN
- PPPH time parsing: VERIFIED_REAL_DATA
- MARS synchronization: NOT_AVAILABLE

