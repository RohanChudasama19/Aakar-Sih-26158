# Implementation Plan (Phase 2)

1. **Backend Generators**: Develop python scripts utilizing scipy.spatial.cKDTree for support and density over scene_mesh.ply.
2. **Artifact Endpoints**: Serve GET /api/jobs/{jid}/heatmaps/{metric}.
3. **Frontend Loader**: Implement THREE.FileLoader for JSON ingestion.
4. **Shader Injection**: Construct HeatmapMaterial inheriting physical attributes but replacing albedo with gradient lookup.
5. **UI Integration**: Mount toolbar buttons for toggle states and color legends.
