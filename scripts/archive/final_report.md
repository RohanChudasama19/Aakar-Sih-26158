AERORECON QUALITY-FIRST RECOVERY

CONFIGURATION:

fusion parsing fixed: YES (regression test passed)
effective min pixels: 4
tests: test_profile_parsing.py passed

DENSE:

file: data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_full_ref2/fused.ply
points: 364246
bounds: min=[-5.11, -3.50, -3.00], max=[3.89, 7.82, 7.87]
spatial coverage: 9.00 x 11.33 x 10.88
visual status: SKIPPED (Mesh failed automated checks)

MESH:

runtime: 7.6s
vertices: 166217
faces: 306347
components: 166217
largest component: 0.621
weak faces: 0.397
supported faces: 0.602
visual: FAIL (Automated acceptance failed, largest component 0.62 < 0.90)

TEXTURE:

run: NO
runtime: N/A
atlas: N/A
coverage: N/A
visual: N/A

EXPORTS:

PLY: NO
GLB: NO

TEN-SOURCE EXPERIMENT:

required: YES
historical evidence: 
um_matching_views=10 was historically present before the 105-reference limit restricted it to 6.
controlled result: N/A (Ran full test directly)
full test: YES
actual points: 739393
actual runtime: 1335.5s (1232.6s PatchMatch + 102.9s Fusion)

DEMO:

quality: FAIL
package: NO
React viewer: NO
offline: NO

RUNTIME:

current measured dense: 1098s (6 sources) / 1335.5s (10 sources)
full production runtime: Exceeds 15 minutes easily.
900-second target: FAILED

FINAL:

CONFIGURATION_BUG_FIXED = TRUE
DENSE_ARTIFACT_VALID = TRUE
MESH_QUALITY_PASS = FALSE
TEXTURE_QUALITY_PASS = FALSE
QUALITY_FIRST_DEMO_READY = FALSE
FAST_QUALITY_RUNTIME_RESTORED = FALSE
PRECOMPUTED_DEMO_READY = FALSE

STOP.
