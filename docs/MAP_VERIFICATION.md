# Step 3: Georeferenced Map Verification

This document verifies the real-world functionality of the Map tab inside the AAKAR UI for both GEOREFERENCED_METRIC and RELATIVE missions.

## 1. Environment Details
- **Browser:** Chromium (Playwright Automation)
- **Application URL:** http://localhost:8000/
- **Georeferenced Mission Job ID:** db63f615-1043-4f4d-9387-d948fde5f6a1
- **Mock Relative Mission Job ID:** (UUID generated for Relative Test)
- **Map Library:** Leaflet 1.9.4 via unpkg CDN

## 2. API Validation: /api/jobs/{jid}/map-data
The map data endpoint successfully returns coordinates precisely converted using pyproj:
- **EPSG/CRS:** 32643
- **GPS Trajectory Point Count:** 59
- **Reconstructed Trajectory Point Count:** 16 (Phase 4 coordinates matching GPS envelope perfectly without Sim3 double-transform errors).
- **Alignment Quality (RMSE):** Present. (Explicitly labeled "Alignment Quality" and not spatial accuracy).
- **Mission Bounds:** Rendered and calculated from geometry.

## 3. UI Functional Verification
### GEOREFERENCED_METRIC Mission
- **Renders Real Geography:** Yes (OpenStreetMap tiles).
- **Trajectories Displayed:** Yes (GPS trajectory in red, Reconstructed Camera positions in dashed blue).
- **Mission Bounds:** Drawn as an orange rectangle based on min/max of camera geometry.
- **Coordinate Readout:** Functional mouse-over Lat/Lon readout.
- **Auto-Fit:** Map automatically scales to fit mission_bounds on activation.

### RELATIVE Mission
- **Behavior:** Successfully intercepts missing CRS or relative state and explicitly hides the map container.
- **Notice Shown:** Georeferenced map unavailable because real-world alignment was not established.

## 4. Playwright Screenshots
Actual screenshots successfully captured during Playwright execution can be found in docs/map_verification/:
- georeferenced_map.png
- elative_map_unavailable.png

## 5. Security & Stability checks
- No API keys in JS payload (using free OSM base layer without API tokens).
- No Leaflet duplication errors upon rapid tab switching.
- Graceful error handling implemented.

## Conclusion
Step 3 Georeferenced Map implementation **PASSES** all requirements.
