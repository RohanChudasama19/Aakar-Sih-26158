# Step 4 Measurement Verification

## Supported Tools
- 3D Distance
- Horizontal Distance
- Vertical Difference
- XYZ Delta
- Planar Area (Newell's Method)
- Slope (Angle and Grade)
- Angle (Between 3 points)

## Formulas / Methods
- Horizontal distance uses sqrt(dx^2 + dy^2) as Z is the canonical vertical axis.
- Planar area uses **Newell's method** for arbitrary 3D polygons, projecting them securely across planes.
- Slope uses tan2(abs(vert), horiz) clamped.

## Representation Compatibility
- Measurements operate directly on THREE.Raycaster against genuine geometry points. Compatible with Mesh, Textured Mesh, Semantic (geometric tool overlay only), Confidence, and Point Cloud (snaps to valid vertices).

## Metric-State Behavior
- Checked centrally using getMeasurementCapabilities(metricState) policy.
- Outputs meters for GEOREFERENCED_METRIC and METRIC_SCALE.
- Outputs 'model units' strictly for RELATIVE.

## Screenshot Evidence
Verified using headless Chromium and Playwright. Screenshots are saved:
- docs/measurement_verification/distance.png
- docs/measurement_verification/area.png
- docs/measurement_verification/slope.png
- docs/measurement_verification/angle.png
- docs/measurement_verification/relative_disabled.png (verified logic)
