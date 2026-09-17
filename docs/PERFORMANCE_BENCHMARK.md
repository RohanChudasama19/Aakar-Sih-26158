# Step 7: Performance Profiling, Optimization, and Scalability Benchmarking

## Test Machine

| Component | Value |
|---|---|
| Machine | Dell G15 5520 |
| OS | Windows 11 Home (Build 26200) |
| CPU | Intel Core i7-12700H (Intel64 Family 6 Model 154) |
| RAM | 16,069 MB |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| VRAM | 4096 MiB |
| GPU Driver | 581.95 |
| CUDA | Available (COLMAP 4.1.1 built with CUDA) |
| COLMAP | 4.1.1 (commit a0d785f, 2026-07-17, WITH CUDA) |
| Python | 3.x (via .venv) |
| Open3D | 0.19.0 |
| MULTI_GPU | NOT_APPLICABLE (single RTX 3050 present) |

---

## Baseline: Step 5 Zurich GPU Mission

**Job ID:** `852f389c-f74e-4477-8e76-d7204c20a67c`  
**Dataset:** Zurich MAV Real Test  
**Engine:** COLMAP_CUDA (full GPU path)  
**Run type:** COLD RUN

### Mission Parameters
| Field | Value |
|---|---|
| Video duration | 11.67 s |
| Resolution | 1920×1080 input → 1600×900 extracted |
| Input frames | 350 |
| Selected frames | 25 |
| Registered cameras | 25/25 (100%) |

### Stage-Level Baseline Timings
| Stage | Name | Duration (s) | % of Total |
|---|---|---|---|
| A | Ingest & Preprocess (readiness, extraction, undistortion) | 18.6 | 1.2% |
| B | SfM (feature extraction + matching + mapping + BA) | 32.8 | 2.1% |
| C | Dense (undistort + PatchMatch + fusion + outlier removal) | 1447.2 | **94.0%** |
| D | Mesh (Poisson + filter + texture) | 26.3 | 1.7% |
| E | Semantics | 2.4 | 0.2% |
| F | Export + ZIP | 11.5 | 0.8% |
| **Total** | | **1538.9 s (25.6 min)** | |

**Stage sum (1538.9 s) == Total processing_time_sec (1538.922 s). No double-counting confirmed.**

### Bottleneck Table (Sorted)
| Stage | Duration (s) | Notes |
|---|---|---|
| **PatchMatch Stereo** | ~1410 s (est.) | Dominant bottleneck — 91.6% of total |
| Stereo Fusion | ~26 s (est.) | Second largest dense sub-step |
| Mesh (Poisson + texture) | 26.3 s | |
| SfM (feature + match + map) | 32.8 s | |
| Export + ZIP | 11.5 s | |
| Undistortion (COLMAP) | ~1 s | |
| Readiness + preprocess | 18.6 s | Includes frame extraction |
| Semantics | 2.4 s | Heuristic fallback only |

### Quality Metrics (QUALITY profile)
| Metric | Value |
|---|---|
| Registration ratio | 100% (25/25) |
| Sparse points | 10,179 |
| Mean reprojection error | 0.988 px |
| Dense points (raw) | 644,837 |
| Dense points (filtered) | 631,819 |
| Mesh vertices | 279,320 |
| Mesh faces | 550,019 |
| Texture coverage | TEXTURED (99.998%) |
| Metric state | GEOREFERENCED_METRIC |
| GPS alignment RMSE | 0.9324 m (fit residual only) |

### Disk Usage (Zurich baseline)
| Component | Size |
|---|---|
| Input video | 25.2 MB |
| Extracted frames | 67.2 MB |
| Original frames | 57.0 MB |
| COLMAP sparse workspace | 6.9 MB |
| Dense workspace (QUALITY) | 1,197.9 MB |
| Outputs (PLY, mesh, exports) | 683.8 MB |
| Deliverables package | 374.0 MB |
| **Total workspace** | **~2,412 MB** |

### VRAM Usage
Peak VRAM during PatchMatch Stereo: **~561 MiB of 4096 MiB (13.7% utilization)**

> The RTX 3050 VRAM is severely underutilized. COLMAP PatchMatch was not VRAM-limited; it was compute-limited (2048 CUDA cores on a laptop).

---

## PatchMatch Dense Profile Benchmark

Three profiles were benchmarked on identical inputs (25 frames, 1600×900) against the same Zurich sparse workspace.

### Profile Parameters
| Parameter | QUALITY | BALANCED | FAST |
|---|---|---|---|
| max_image_size | 2048 | 1600 | 1024 |
| window_radius | 6 | 5 | 4 |
| window_step | 1 | 1 | 2 |
| num_iterations | 7 | 5 | 3 |
| geom_consistency | True | True | False |
| num_matching_views | 10 | 8 | 7 |

### Measured Timing (same hardware, same 25 Zurich frames)
| Profile | Undistort (s) | PatchMatch (s) | Fusion (s) | Total Dense (s) | Speedup vs QUALITY |
|---|---|---|---|---|---|
| **QUALITY** (baseline) | ~1 | ~1410 | ~26 | **1447** | 1.0× |
| **BALANCED** | 1.4 | 956.1 | 11.6 | **969.2** | **1.49×** |
| **FAST** | 2.2 | 45.8 | 5.0 | **52.9** | **27.4×** |

### Quality Comparison
| Profile | Fused Points | Quality Impact |
|---|---|---|
| QUALITY | 631,819 (after outlier removal) | Baseline |
| BALANCED | ~575,318 fused | −9.0% point count |
| FAST | ~182,008 fused | −71.2% point count (significant) |

**FAST is too destructive for production use.** BALANCED provides a meaningful speedup (1.49×) with acceptable quality loss (9% fewer points, similar geometry).

### Projected Total Pipeline Times (BALANCED vs QUALITY, same 25-frame input)
| Profile | Dense Stage | Other Stages | **Total** |
|---|---|---|---|
| QUALITY | 1447 s | 92 s | **1539 s** |
| BALANCED | 969 s | 92 s | **~1061 s (17.7 min)** |
| FAST | 53 s | 92 s | **~145 s (2.4 min)** |

---

## Optimizations Implemented

### OPT-1: Engine Option Case-Insensitive Fix (`runner.py`)
**Before:** `force_cpu = opts.get("engine") != "colmap"` — required exact lowercase `"colmap"`. Jobs submitted as `"COLMAP_CUDA"` incorrectly fell back to CPU SfM.  
**After:** `force_cpu = not (opts.get("engine", "") or "").lower().startswith("colmap")` — accepts `colmap`, `COLMAP_CUDA`, `colmap_cpu`, etc.  
**Impact:** Correctness fix. Ensures GPU reconstruction always runs when requested.  
**Quality impact:** None (correctness fix, not a tradeoff).

### OPT-2: Per-Subprocess Wall-Clock Timing (`dense_backend.py`)
Added `subprocess_timings.{undistort_s, patchmatch_s, fusion_s}` to the dense report dict.  
**Impact:** Enables precise identification of PatchMatch vs fusion vs undistort contribution.  
**Quality impact:** None.

### OPT-3: `num_matching_views` Cap (`dense_backend.py`)
Added `--PatchMatchStereo.num_matching_views` to all profile dicts (QUALITY=10, BALANCED=8, FAST=7).  
**Rationale:** RTX 3050 has 4096 MiB VRAM but only 2048 CUDA cores. Default COLMAP may use up to 20 source images per reference frame. Capping at 10 for QUALITY reduces per-frame stereo cost without losing coverage on 25-frame sequences where most frames already see each other.  
**Quality impact:** Minimal for UAV video (sequential, overlapping) — the nearest 10 frames provide sufficient baseline diversity.

### OPT-4: Eliminate Duplicate PointCloud Serialization (`runner.py`)
**Before:** Two `trimesh.PointCloud(...).export()` calls on identical data (dense_filtered.ply and dense_relative.ply).  
**After:** Export once to dense_filtered.ply, then `shutil.copy2()` to dense_relative.ply.  
**Impact:** Eliminates one redundant PLY serialization pass (saves ~1–3 s per mission, more for large clouds).  
**Quality impact:** None.

### OPT-5: Sub-Stage Fine-Grained Timing (`runner.py`)
Added `sub_stages` dict populated by `timed()` context manager wrapping all major operations: readiness, frame_extraction, sfm, georef, dense, mesh, semantics, viewer_artifacts, exports, zip_packaging.  
**Impact:** mission_report.json now contains per-operation timing for future bottleneck identification.  
**Quality impact:** None.

### OPT-6: Real Hardware Info in Report (`runner.py`)
**Before:** Report always claimed `"gpu_assumption_for_target": "RTX 4090-class, 24 GB VRAM"`.  
**After:** Calls `nvidia-smi` at report generation time to record actual GPU name, driver, VRAM total.  
**Impact:** Prevents misleading hardware claims in mission reports.  
**Quality impact:** None.

---

## Benchmark Matrix

| Dataset | Video (s) | Res | Selected Frames | Registered | SfM (s) | Dense (s) | Mesh (s) | Export (s) | Total (s) | Peak VRAM | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Zurich GPU (QUALITY) | 11.67 | 1600×900 | 25 | 25/25 | 32.8 | 1447.2 | 26.3 | 11.5 | **1539** | ~561 MiB | COMPLETED |
| Sample CPU (short) | 6.0 | — | 16 | 16/16 | 1.8 | 2.5 | 7.9 | 4.3 | **18.1** | N/A (CPU) | COMPLETED (CPU fallback) |
| Medium mission | — | — | — | — | — | — | — | — | — | — | **NOT_AVAILABLE** |
| ~10-min mission | — | — | — | — | — | — | — | — | — | — | **NOT_AVAILABLE** |

---

## Quality Matrix

| Dataset | Reg % | Sparse Pts | Reproj Err (px) | Dense Pts | Mesh Faces | Texture | Metric State |
|---|---|---|---|---|---|---|---|
| Zurich GPU (QUALITY) | 100% | 10,179 | 0.988 | 631,819 | 550,019 | TEXTURED | GEOREF_METRIC |
| Sample CPU (short) | 100% | 3,952 | 0.791 | 16,914 | 108,005 | TEXTURED | GEOREF_METRIC |

---

## Performance Target

| Target | Requirement | Status |
|---|---|---|
| <15 min for 10-min video | Total ≤ 900 s | **NOT_AVAILABLE** |

**Reason:** No genuine ~10-minute UAV dataset is available for testing. No extrapolation from the 11.67-second Zurich input is performed. The 25.6-minute runtime for the 11.67-second Zurich video confirms this hardware is *not* expected to achieve the SIH target for longer missions without significant algorithmic changes (e.g., hierarchical PatchMatch, GPU upgrade).

> If a 10-minute video yielded 1500 frames and 250 were selected, projected QUALITY PatchMatch time would be ~14,400 s (~4 hours). This is based on the observed ~57.6 s/frame rate on the RTX 3050 Laptop. This projection is for information only — **it is not a benchmark result**.

---

## Scalability Analysis

### What Scales Approximately Linearly
- Feature extraction (per-image SIFT)
- Sequential matching (per-adjacent-pair)
- Stereo fusion (merging per-image depth maps)
- Export generation

### What Scales Super-Linearly
- **PatchMatch Stereo** — scales with both number of images AND scene complexity. Per-image cost grows with `num_matching_views` and image resolution.
- **Poisson meshing** — scales with dense point count (~O(n log n))
- COLMAP mapper (scales O(n²) in worst case for all-pairs matching, but sequential matching mitigates this)

### Memory-Limited Stages
- PatchMatch VRAM: observed 561 MiB / 4096 MiB. Not VRAM-limited at 25 frames × 1600×900. Longer missions with more frames may approach limits.
- Dense point outlier removal (Open3D): loaded fully in RAM. At 631K points fine; at 10M+ points could become limiting.

---

## Remaining Bottlenecks

| Bottleneck | Root Cause | Mitigation Path (not implemented) |
|---|---|---|
| PatchMatch dominates (94%) | RTX 3050 Laptop — 2048 CUDA cores, laptop thermal limits | GPU upgrade; hierarchical depth map fusion; resolution reduction |
| No 10-min dataset | No real UAV data available | Acquire real mission footage |
| FAST profile too lossy (-71% points) | Low resolution + no geometric consistency | Not suitable for production |
| Sequential matching overlap=200 | Overly wide matching for short missions | Tune to actual frame count |

---

## Limitations

1. **Only one real GPU mission available** (Zurich, 11.67 s). All scalability analysis is architectural reasoning, not measured.
2. **No medium or long mission data.** Cannot state MEDIUM or LONG benchmark results.
3. **RTX 3050 Laptop GPU is thermally constrained.** Sustained PatchMatch performance may degrade over long runs due to thermal throttling. Not measured.
4. **SIH ≤1 m accuracy remains NOT_AVAILABLE** — performance work does not affect this.
