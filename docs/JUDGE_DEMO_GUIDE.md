# AeroRecon - Judge Demo Guide

This document outlines the standard 5-8 minute live demonstration flow for SIH 26158 evaluators.

## 1. What to Click
1. **Open AeroRecon:** Navigate to the local host URL.
2. **Create Mission:** Click New Mission, upload the dataset (video, GPS, metadata).
3. **Show Readiness:** Expand the "Upload progress" logs to show the readiness gate actively rejecting blurry/unusable frames.
4. **Live Pipeline:** Point out the Server-Sent Events (SSE) updating the visual pipeline stages in real-time.
5. **Open Completed Mission:** Cancel the live upload and open the pre-completed "Zurich GPU" mission to save time.
6. **Six-Mode Viewer:** Cycle through the views: Textured Mesh -> Dense Point Cloud -> Mesh (Geometry) -> Semantic -> Confidence.
7. **Map:** Switch to the 2D Map view to show the drone trajectory overlay and bounds.
8. **Measurements:** Draw a 3D line on a building and show the resulting metric length.
9. **Validation / Exports:** Show the generated Accuracy Report (clearly marked Unverified) and trigger a .zip download of the exported formats.

## 2. What to Explain
* Emphasize the **Readiness Gate** which catches bad flights before wasting compute hours.
* Explain the **Single-Transform Paradigm**. The entire model is reconstructed locally and transformed globally exactly once to prevent distortion, locking all outputs to the same reference frame.
* Point out the **Semantic Heuristics**, explaining how it separates buildings and ground geometrically.

## 3. Safe Claims
* The application correctly pipelines all constraints (SfM -> Dense -> Mesh -> Texture -> Export).
* The Web UI is completely functional and decoupled from the backend worker.
* Exports natively support multiple industry standard formats.
* The system is robust to cancellations and retries.

## 4. Claims to strictly AVOID (Do Not Make)
* **DO NOT** claim the system is "survey-grade" or achieves the $\leq1$ m target accuracy. We do not have independent validation checkpoints.
* **DO NOT** claim the system processes 10 minutes of video in under 15 minutes. It will fail this target on average hardware.
* **DO NOT** claim the semantic output is "AI generated." It uses a geometric heuristic fallback because no model weights were bundled.
* **DO NOT** claim the system has advanced multi-band texture blending. UV seams are present.
