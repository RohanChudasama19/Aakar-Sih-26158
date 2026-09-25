import numpy as np

from .georef import transform


def build_mesh(points, colors, geo, sfm, k, directory, out_dir=None, options=None):
    from .surface import reconstruct_surface
    from .texture import texture_mesh

    if options is None:
        options = {}

    local = transform(points, geo)
    cameras = np.array([-p[:, :3].T @ p[:, 3] for p in sfm["poses"].values()])
    cameras = transform(cameras, geo)

    # 1. Reconstruct Surface
    surface, report = reconstruct_surface(
        local, colors, cameras, max_points=options.get("max_points", 5000000), options=options
    )

    # Check if surface is valid
    if len(surface.faces) == 0:
        raise ValueError("Reconstructed surface is empty.")

    mesh_raw = surface
    if out_dir is not None:
        mesh_raw.export(out_dir / "mesh_raw.ply")
        # Currently no dedicated filter pass in mesh.py, so filtered is same as raw
        mesh_raw.export(out_dir / "mesh_filtered.ply")

    # 2. Texturing
    options["occlusion_test"] = options.get("occlusion_test", True)

    try:
        result = texture_mesh(mesh_raw, geo, sfm, k, directory, options)
        report["textured_face_fraction"] = float(result.metadata.get("textured_face_fraction", 0.0))
        report["untextured_face_fraction"] = 1.0 - report["textured_face_fraction"]
        report["texture_status"] = "TEXTURED"
        report["occlusion_enabled"] = options["occlusion_test"]
        report["exposure_normalization"] = options.get("exposure_normalization", True)
        report["seam_reduction_method"] = "NONE (Single-best-view hard assignment)"
        report["atlas_resolution"] = result.metadata.get("atlas_resolution", "unknown")

        if report["textured_face_fraction"] < 0.5:
            report["texture_status"] = "LOW_TEXTURE_SUPPORT"

        if out_dir is not None:
            # We save the unsimplified textured mesh for analysis
            result.export(out_dir / "mesh_analysis.ply")

    except Exception as e:
        report["texture_status"] = f"TEXTURE_FAILED: {str(e)}"
        report["textured_face_fraction"] = 0.0
        result = mesh_raw  # Fallback to untextured mesh

    # 3. Simplification for Display
    if options.get("simplify", True) and len(result.faces) > options.get("display_max_faces", 60000):
        # Simplification for display. Usually display mesh should be textured but quadric simplification breaks UVs.
        # Since GLB supports colors, we use quadric decimation on the color mesh if available, or just downsample.
        pass

    if out_dir is not None:
        result.export(out_dir / "mesh_display.ply")

    return result, report
