# Phase 8: Exports and Deliverables

## Audit of Existing Exports
- **PLY**: Currently generates `cloud.ply` using trimesh. Needs semantic propagation and explicit `_relative` / `_metric` naming.
- **OBJ**: Written via trimesh (`model.obj`). Lacks formal validation (checking MTL references, relative paths).
- **LAS**: Written via laspy. CRS is attached. Needs validation via roundtrip check.
- **GeoTIFF**: Rasterio DSM generation exists, but needs validation and bounds checking.
- **GLB / GLTF**: Written via trimesh. Lacks validation checks.
- **FBX**: Relies on Blender. Marks as unavailable if missing.
- **ZIP Packaging**: Handled by `shutil.make_archive` blindly archiving the output directory. Needs structured folders (`mesh/`, `pointcloud/`, `reports/`).
- **Manifest**: Missing completely. Needs checksums (SHA-256) and file sizes.

## Export Architecture Plan
1. **ExportManager**: Core class to coordinate all export tasks.
2. **Exporters**: Pluggable backend structure for format-specific logic (e.g. `MeshExporter`, `PointCloudExporter`, `RasterExporter`).
3. **Validation Framework**: Post-export validation step for each format.
4. **GeoJSON**: Extract structural boundaries from Semantic phase (building regions) into valid WGS84 GeoJSON if georeferenced.
5. **Manifest & Reports**: Generate `manifest.json` with SHA-256, sizes, and validation states. Combine sub-reports into `mission_report.json`.
6. **Packaging**: Create a structured `mission_<id>_deliverables.zip` containing specific verified artifacts.
