# Dataset Adapter Report

This document reports the status of dataset adapters for external datasets integrated into AeroRecon.

## Summary Status

| Dataset | Access | Real sample obtained? | Adapter implemented? | Real adapter run? | Canonical validation result |
|---------|--------|-----------------------|----------------------|-------------------|-----------------------------|
| MARS-LVIG | ACCESS_BLOCKED (Google Drive) | No | Yes (Mocked for logic validation) | No | VALID_WITH_WARNINGS |
| Zurich Urban MAV | ACCESS_BLOCKED (Requires manual/direct zip location) | No | Yes (Mocked for logic validation) | No | VALID_WITH_WARNINGS |
| UseGeo | ACCESS_BLOCKED (Synology Drive page) | No | Yes (Mocked for logic validation) | No | VALID_WITH_WARNINGS |
| UAVid | ACCESS_BLOCKED (Requires Account) | No | Yes (Mocked for logic validation) | No | VALID_WITH_WARNINGS |
| H3D | ACCESS_BLOCKED (Requires Application) | No | Yes (Mocked for logic validation) | No | VALID_WITH_WARNINGS |
| PPPH-UAV Example | VERIFIED (Zenodo) | Yes (34MB) | Yes | Yes | VALID_WITH_WARNINGS |

*Note: Validation warnings are expected as these are partial/dummy datasets lacking complete video/imagery modalities where only specific sensors (e.g., GNSS) are being ingested.*

## Detailed Adapter Notes

### MARS-LVIG
- **Real Sample**: No
- **Missing Information**: Raw ROS bags are inaccessible programmatically without interactive auth/browsers due to Google Drive virus scan warnings on large files.
- **Next Phase Readiness**: Adapter logic and canonical schema are defined. Requires manual user download of ROS bags to execute on real data.

### PPPH-UAV Example Data
- **Real Sample**: Yes, 6.Example.zip downloaded directly from Zenodo.
- **Missing Information**: None for GNSS targets.
- **Next Phase Readiness**: Ready for RINEX processing and trajectory generation.

### Zurich Urban MAV
- **Real Sample**: No, zip links are behind 301 redirects and specific manual pages.
- **Next Phase Readiness**: Schema defined for IMU, barometer, and trajectory parsing.

### UseGeo
- **Real Sample**: No, hosted on an interactive Synology Drive web portal.
- **Next Phase Readiness**: Schema defined for independent image sequences and reference LiDAR/photogrammetry.

### UAVid
- **Real Sample**: No, requires account and signed usage terms.
- **Next Phase Readiness**: Taxonomy mapping (UAVid to AeroRecon) is recorded. Ready for semantic model training once user manually provides the dataset.

### H3D Hessigheim
- **Real Sample**: No, requires institutional form submission.
- **Next Phase Readiness**: Ready for reference DTM and point cloud validation against standard AeroRecon outputs once data is provided.
