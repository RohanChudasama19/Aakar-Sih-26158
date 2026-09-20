# H3D DTM Validation

This validation strictly compares AeroRecon's geometry-only mathematical ground classification against the human-annotated H3D benchmark.

**Test Geometry Input:** `Mar19_test.laz` (No classification used)
**Validation GroundTruth:** `Mar19_test_GroundTruth.laz` (Semantic classes only used to measure evaluation accuracy, completely hidden from the prediction pipeline).

Metrics are compiled into `PHASE_LM_DTM_REPORT.json`.
