AERORECON FINAL FAST_QUALITY PRODUCTION VALIDATION

STATUS: FAIL (CRITICAL PIPELINE CRASH)

==================================================
TIMINGS & METRICS
==================================================
Sparse Cloud (Global Mapper):
- Registered Images: 250 / 250
- Sparse Points: 800k+ (Global Mapper Unfiltered)

Dense Cloud (PatchMatch Stereo):
- Undistorted Images: 250
- Reference Targets: 105
- Runtime: CRASHED at 712.47 sec
- Result: 0 points (Failed)

Mesh & Texture:
- N/A (Pipeline aborted before mesh extraction)

==================================================
FORENSIC ANALYSIS OF FAILURE
==================================================
The requested architecture repair is mathematically incompatible with COLMAP's geometric consistency engine.

1. We undistorted ALL 250 images, making them available as sources.
2. We restricted the patch-match.cfg reference list to 105 images.
3. FAST_QUALITY enforces geom_consistency = True and 
um_matching_views = 6.

During PatchMatchStereo, COLMAP runs Photometric consistency (which succeeds), followed by Geometric consistency. Geometric consistency REQUIRES that any image used as a source must have its own depth map already computed. 

Because COLMAP's __auto__ selector chooses the 6 closest physical neighbors from the pool of 250, it frequently selects source images that were excluded from the 105 references. These excluded sources have no depth maps. COLMAP logs Skipping source image for missing depth/normal map. 

When a reference image has ALL 6 of its closest neighbors skipped, its source list becomes empty. This triggers a fatal C++ assertion:
E20260925 03:21:48.335113  9268 patch_match.cc:58] Check failed: !src_image_idxs.empty()

This causes COLMAP to abort with STATUS_STACK_BUFFER_OVERRUN (Exit Code 3221226505).

==================================================
RECOMMENDED ACTION
==================================================
To achieve a successful FAST_QUALITY production run, we must violate one of your constraints. Please authorize ONE of the following fixes:

A. Disable Geometric Consistency: Set geom_consistency = False in the FAST_QUALITY profile.
B. Compute Full Dense Cloud: Remove the 105 reference limit and compute depth maps for all 250 images.
C. Increase Source Pool: Increase 
um_matching_views to 20 so it's statistically unlikely for all sources to be missing depth maps.
