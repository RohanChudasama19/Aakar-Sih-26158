# 8-MINUTE SIH PRESENTATION SCRIPT

## 0:00 - 1:00: Problem & Solution
"Welcome judges. Today we present AeroRecon (SIH26158), a robust, offline-first 3D reconstruction intelligence platform. We solve the problem of opaque, black-box photogrammetry by exposing deterministic scientific heatmaps and explicit geometric quality data directly to the user."

## 1:00 - 2:00: Project & Mission Management
[Click through Dashboard -> Project List -> New Mission]
"Here is the mission lifecycle. We input GPS and video metadata, select a reconstruction profile (e.g. Quality, Balanced, Fast), and submit. The pipeline queues jobs natively through Redis, ensuring offline continuity without cloud dependencies."

## 2:00 - 4:00: MARS Demonstration (High Quality)
[Open mars_hkairport01_quality]
"Here is the MARS dataset reconstructed. Notice the 355k face topology. 
I can Orbit, Walk, or Fly through the scene."
[Activate Heatmaps]
"This is the scientific intelligence layer. 
- Point Density highlights sampling resolution.
- Surface Support displays real distances between the dense cloud and final mesh centroid.
- Potential Camera Visibility validates our projection matrix."

## 4:00 - 5:00: Surface Inspection
[Click a face on the runway]
"When we click a surface, we don't get an interpolated gradient. We get the exact, deterministic raw value that drove this color. If independent reference data is missing, we explicitly label Geometric Error as NOT_VERIFIED to maintain scientific integrity."

## 5:00 - 6:00: Quality Intelligence & Export
[Click Reports and Exports]
"All data dynamically aggregates into Quality Intelligence reports. Exports are natively packaged as GLB, PLY, and GeoTIFF."

## 6:00 - 7:00: Colorado (Degraded Case)
[Open 95f51b12-b771-47bf-9201-c3700f9475a7]
"AeroRecon doesn't just display perfect datasets. Here is the Colorado degraded case. Notice how the heatmaps perfectly align with the shattered topology, proving our rendering isn't faked or baked into the texture—it maps dynamically to any 3D structure."

## 7:00 - 8:00: Conclusion
"AeroRecon guarantees offline continuity, deterministic metric mapping, and rigorous scientific transparency. Thank you."
