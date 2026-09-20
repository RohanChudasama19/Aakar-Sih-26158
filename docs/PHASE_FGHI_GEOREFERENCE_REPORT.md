# Phase FGHI: Advanced Georeferencing

## Accomplishments
1. True GCP CONTROL vs CHECKPOINT logic is implemented and strictly enforced.
2. Robust weighted Sim(3) transforms handle differing uncertainty in RTK vs GNSS.
3. Checkpoints are structurally isolated from georeferencing to prevent leakage.
4. Vertical Datum mismatches trigger safe Horizontal-Only fitting modes.

## Real Data Validation
- **GCP Points:** Synthetic verification only. We lack independent ground-truth surveyed targets for Zurich/PPPH.
- **PPK Ingestion:** Provenance validated on PPPH-UAV (includes precise products and observation files).

## Conclusion
The georeferencing hierarchy operates as follows:
`CONTROL > RTK_FIXED > GNSS_SINGLE`
Visual alignment strictly follows these constraints when enough valid matching features exist.

SIH <= 1m accuracy is NOT claimed, as this requires true independent validation on a real flight.
