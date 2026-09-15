# Judge Demo Guide
## AeroRecon Presentation Protocol

### 1. The Scenario
Explain the problem: "First responders need rapid 3D intelligence from a single, unplanned drone flight without relying on cloud processing."

### 2. Execution (Live Demo)
1. **Open UI:** Navigate to `http://localhost:8000`.
2. **Upload Sample:** Click "New Mission" and select "Use bundled sample files." (This uses the synthetic campus smoke test).
3. **Start Reconstruction:** Click Start. Show the live real-time pipeline status (Ingest -> Camera Poses -> Dense Geometry -> Mesh & Texture -> Georeference -> Scene Report).
4. **Explanation:** Mention the pipeline is running locally (CPU or CUDA). Show the detailed logs if applicable.

### 3. Reviewing Results
1. **3D Viewer:** Orbit the reconstructed scene. Point out the surface quality and any gaps (emphasize "Evidence before inference").
2. **Measurements:** Use the Distance or Planar Area tool to show metric capabilities. Note the explicit "Accuracy Unverified" warning for GPS-aligned data without checkpoints.
3. **Exports:** Show the "Export Center" and download the complete ZIP deliverable. Extract it to show the GeoTIFF, LAS, GLB, and metadata JSON files.

### 4. Key Differentiators to Highlight
- No cloud required.
- Single-pass video capable (no grid flight needed).
- Strict engineering pipeline and metric traceability.
