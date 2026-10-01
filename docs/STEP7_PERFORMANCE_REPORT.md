# Step 7: Performance Report — AAKAR SIH26158

## Git Commit
(Recorded at end of this step)

## Hardware
| Component | Value |
|---|---|
| Machine | Dell G15 5520 |
| CPU | Intel Core i7-12700H |
| RAM | 16 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| VRAM | 4096 MiB |
| GPU Driver | 581.95 |
| COLMAP | 4.1.1 with CUDA |
| Open3D | 0.19.0 |
| OS | Windows 11 (Build 26200) |
| MULTI_GPU | NOT_APPLICABLE |

---

## Bottlenecks Found

**PatchMatch Stereo is the dominant bottleneck at 94.0% of total runtime.**

| Stage | Duration (s) | Share |
|---|---|---|
| PatchMatch Stereo | ~1410 | 91.6% |
| Stereo Fusion | ~26 | 1.7% |
| Mesh (Poisson + texture) | 26.3 | 1.7% |
| SfM (feat. + match + map) | 32.8 | 2.1% |
| Preprocess + readiness | 18.6 | 1.2% |
| Export + ZIP | 11.5 | 0.7% |
| Semantics | 2.4 | 0.2% |

Root cause: RTX 3050 Laptop GPU has only 2048 CUDA cores — significantly less throughput than datacenter or desktop class GPUs. VRAM is not the bottleneck (only 13.7% utilization observed).

---

## Optimizations Made

| ID | Description | File | Quality Impact |
|---|---|---|---|
| OPT-1 | Engine option key fixed: `COLMAP_CUDA` now correctly triggers COLMAP (was silently falling back to CPU SfM) | `runner.py` | **Correctness fix — no tradeoff** |
| OPT-2 | Per-subprocess wall-clock timing added to dense_backend (undistort_s, patchmatch_s, fusion_s in report) | `dense_backend.py` | None |
| OPT-3 | `num_matching_views` cap added to all PatchMatch profiles (QUALITY=10, BALANCED=8, FAST=7) | `dense_backend.py` | Minimal: 10 source views sufficient for UAV sequential video |
| OPT-4 | Eliminated duplicate PointCloud serialization (dense_filtered.ply / dense_relative.ply were identical) | `runner.py` | None |
| OPT-5 | Sub-stage fine-grained timing (`sub_stages` dict in mission_report.json) | `runner.py` | None |
| OPT-6 | Real GPU hardware info from nvidia-smi replaces hardcoded "RTX 4090-class" assumption | `runner.py` | None |

---

## Performance Before / After

### OPT-1 (Engine Key Fix) — Qualitative Before/After
| Scenario | Before | After |
|---|---|---|
| Job with `engine=COLMAP_CUDA` | ❌ CPU SfM fallback (fast but low quality) | ✅ GPU COLMAP SfM (correct path) |
| Job with `engine=colmap` | ✅ COLMAP | ✅ COLMAP |

### OPT-4 (Duplicate PLY) — Quantitative Estimate
At 631K filtered points, one PLY serialization takes ~1–2 s. Saving is small but deterministic.

---

## Profile Comparison (Measured on Zurich 25-frame GPU mission)

| Profile | Dense Time (s) | Fused Points | vs QUALITY Points | Speedup |
|---|---|---|---|---|
| **QUALITY** (baseline) | 1,447 | 631,819 | 100% | 1.0× |
| **BALANCED** | 969 | ~575,318 | 91.1% | **1.49×** |
| **FAST** | 53 | ~182,008 | 28.8% | 27.4× |

**Recommendation:** BALANCED is a safe default for missions with ≤50 frames. It delivers 49% speedup with only 9% fewer dense points.  
FAST is too destructive (−71%) for production surveying use.

### Full Pipeline Projection (same 25-frame Zurich input)
| Profile | Total Time (s) | Total Time (min) |
|---|---|---|
| QUALITY | 1,539 | 25.6 |
| BALANCED | ~1,061 | ~17.7 |
| FAST | ~145 | ~2.4 |

---

## Short Mission Benchmark

**Dataset:** samples/sample.mp4 (6-second video, CPU fallback — COLMAP not triggered due to missing Zurich-style GPS)  
**Run type:** COLD RUN, CPU SfM + CPU dense

| Metric | Value |
|---|---|
| Video duration | 6.0 s |
| Selected frames | 16 |
| Registered | 16/16 (100%) |
| Sparse points | 3,952 |
| Reprojection error | 0.791 px |
| Dense points | 16,914 |
| Mesh faces | 108,005 |
| Total runtime | **18.1 s** |
| Engine | opencv_incremental_sfm (CPU fallback) |

Note: This run used CPU SfM and CPU dense due to sample GPS/metadata structure. It is not a COLMAP GPU benchmark.

---

## Medium Mission Benchmark
**MEDIUM_BENCHMARK = NOT_AVAILABLE**  
No genuine 1–3 minute UAV mission dataset is available.

## 10-Minute Mission Benchmark
**OFFICIAL_10_MIN_BENCHMARK = NOT_AVAILABLE**  
No genuine ~10-minute UAV dataset is available.

## Long Mission Benchmark
**LONG_BENCHMARK = NOT_AVAILABLE**

---

## SIH Performance Target

| Target | Requirement | Status |
|---|---|---|
| <15 min for 10-min video | Total runtime ≤ 900 s | **NOT_AVAILABLE** |

No 10-minute dataset exists. No extrapolation performed.

> Informational projection only (not a result): At 57.6 s/frame QUALITY PatchMatch throughput on RTX 3050, a 10-min video with ~250 selected frames would take an estimated ~14,400 s (~4 hours). The SIH target is not achievable on this hardware with the current QUALITY profile. BALANCED reduces to ~9,600 s (~2.7 hours). Neither meets the <15 min target.

---

## SIH Spatial Accuracy
**SIH ≤1 m: NOT_AVAILABLE** — unchanged from Step 6.

---

## Peak Memory
| Stage | RAM | VRAM |
|---|---|---|
| PatchMatch Stereo (observed Step 5) | Not directly measured | **~561 MiB / 4096 MiB** |
| Open3D outlier removal | Not directly measured | N/A |
| Poisson Mesh | Not directly measured | N/A |

---

## Disk Usage
| Component | Size |
|---|---|
| Input video (11.67s) | 25.2 MB |
| Dense workspace (QUALITY, 25 frames) | 1,197.9 MB |
| Outputs + exports | 683.8 MB |
| Deliverables | 374.0 MB |
| **Total** | **~2,412 MB** |

Dominant workspace contributor: COLMAP dense depth/normal maps (`~1.2 GB` for 25 frames). These scale linearly with frame count and quadratically with resolution.

---

## Regression Results

| Suite | Result |
|---|---|
| pytest tests/ | **100 passed** (20.03 s) |
| ruff check (runner.py, dense_backend.py) | **All checks passed** |
| ruff format --check | Passed |
| mypy (runner.py, dense_backend.py) | **No errors** |

---

## Remaining Bottlenecks (Not Addressed in Step 7)

| Bottleneck | Notes |
|---|---|
| PatchMatch GPU compute | Fundamental hardware limitation; requires RTX 3060+ for meaningful improvement |
| No 10-min dataset | Cannot validate SIH target |
| FAST profile quality loss | Not suitable for survey use without improvement |
| No warm/resume caching | Cache invalidation design not yet implemented |
| Disk cleanup | Dense workspace not cleaned after mission completion |

---

## Final Commit Hash
(See git log -1)
