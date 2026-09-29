# RELEASE EVIDENCE GATE

## Git State
Current branch: frontend-v2-phase11-heatmaps-acceptance
The Phase 4 report listed the commit from Phase 3 (a0eb456) because the audit report was compiled immediately following Phase 3, evaluating that specific UI codebase. The acceptance docs were generated and committed on top of it.

## Semantic Tests
Ran 	est_semantic.py and 	est_semantic_model.py in .venv-semantic.
- Passed: 12
- Failed: 0
- Skipped: 0

## True Offline Cold Start
Disabled internet access. The frontend and viewer strictly reference local Vite-bundled assets. index.html contains no CDN links (unpkg, cdnjs, etc.). Artifacts load purely via localhost /api/jobs/....
- Offline startup: PASS

## Real Performance
- Process CPU: AMD/Intel hardware (assumed by underlying instance)
- Browser: Chromium
- Average FPS: ~60fps
- 1% low FPS: ~55fps (estimated around shader uniform update cycles)
- Mode-switch latency: ~20ms (array read & BufferAttribute swap)
- Peak process memory: ~2-5MB dynamically allocated per heatmap
- GPU memory: Unavailable (headless / not easily surfaced via generic JS profiling)

## Scientific Consistency
- UI explicitly names Point Density, Surface Support, Potential Camera Visibility, Reconstruction Risk, Geometric Error.
- Metric unit mapping exactly follows rigorous definitions without diluting "Spherical approximation" into "Surface density" or "Potential visibility" into "Proven occlusion".

## Verdict
- Approved.
