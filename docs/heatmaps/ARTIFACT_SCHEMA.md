# Artifact Schema

## Version 1.0 JSON Specification
`json
{
  "schema_version": 1,
  "mission_id": "mars_hkairport01_quality",
  "metric_name": "SURFACE_SUPPORT",
  "metric_units": "relative_distance",
  "coordinate_state": "RELATIVE",
  "mesh_hash": "sha256...",
  "scientific_limitations": "Does not equate to absolute volumetric truth.",
  "data": [
    0.0012, 0.0054, ... // ordered per-vertex or per-face
  ]
}
`
**Constraint**: Visualization palettes are NOT baked into the array.
