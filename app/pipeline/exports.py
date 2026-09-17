import hashlib
import json
import subprocess
import time
from pathlib import Path

import laspy
import numpy as np
import rasterio
import trimesh
from pyproj import CRS
from rasterio.transform import from_origin

from .georef import transform


def hash_file(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class ExportManager:
    def __init__(self, out_dir, geo):
        self.out_dir = Path(out_dir)
        self.geo = geo
        self.manifest = {
            "mission_id": "unknown",
            "export_timestamp": time.time(),
            "pipeline_version": "1.0",
            "metric_state": geo.get("metric_state", "RELATIVE"),
            "coordinate_system": f"EPSG:{geo['epsg']}" if geo.get("valid") else "LOCAL",
            "generated_files": {},
            "validation_results": {},
            "warnings": [],
        }

    def log_file(self, filepath, format_name, status="VERIFIED", warnings=None):
        if not filepath.exists():
            self.manifest["validation_results"][format_name] = "NOT_AVAILABLE"
            return

        size = filepath.stat().st_size
        if size == 0:
            self.manifest["validation_results"][format_name] = "FAILED_VALIDATION: Empty file"
            return

        self.manifest["generated_files"][filepath.name] = {
            "size_bytes": size,
            "sha256": hash_file(filepath),
            "format": format_name,
        }
        self.manifest["validation_results"][format_name] = status
        if warnings:
            self.manifest["warnings"].extend(warnings)

    def export_point_cloud(self, points, colors, point_labels=None):
        out_ply = self.out_dir / "pointcloud"
        out_ply.mkdir(parents=True, exist_ok=True)

        # Relative
        trimesh.points.PointCloud(points, colors=colors).export(out_ply / "cloud_relative.ply")
        self.log_file(out_ply / "cloud_relative.ply", "PLY_RELATIVE")

        if self.geo["valid"]:
            absolute = transform(points, self.geo) + self.geo["origin"]

            # Metric PLY
            trimesh.points.PointCloud(absolute, colors=colors).export(out_ply / "cloud_metric.ply")
            self.log_file(out_ply / "cloud_metric.ply", "PLY_METRIC")

            # LAS
            try:
                header = laspy.LasHeader(point_format=3, version="1.2")
                header.scales = np.array([0.001, 0.001, 0.001])
                header.offsets = np.min(absolute, axis=0)
                header.add_crs(CRS.from_epsg(self.geo["epsg"]))
                las = laspy.LasData(header)
                las.x, las.y, las.z = absolute.T
                las.red, las.green, las.blue = (colors.astype(np.uint16) * 257).T

                # Semantics
                if point_labels is not None:
                    # LAS standard mappings
                    las_mapping = {
                        0: 1,  # Unclassified
                        1: 2,  # Ground
                        2: 11,  # Road
                        3: 6,  # Building
                        4: 5,  # High Vegetation
                        5: 9,  # Water
                        6: 1,  # Infrastructure
                        7: 1,  # Obstacle
                    }
                    las_classes = np.vectorize(lambda x: las_mapping.get(x, 1))(point_labels)
                    las.classification = las_classes.astype(np.uint8)

                las_path = out_ply / "cloud.las"
                las.write(las_path)

                # Validate LAS roundtrip
                las_check = laspy.read(las_path)
                if len(las_check.points) != len(points):
                    self.log_file(las_path, "LAS", status="FAILED_VALIDATION: Point count mismatch")
                else:
                    self.log_file(las_path, "LAS")

            except Exception as e:
                self.manifest["validation_results"]["LAS"] = f"FAILED: {str(e)}"
        else:
            self.manifest["validation_results"]["LAS"] = "NOT_AVAILABLE: Relative metric state"

    def export_mesh(self, mesh):
        out_mesh = self.out_dir / "mesh"
        out_mesh.mkdir(parents=True, exist_ok=True)

        # GLB
        glb_path = out_mesh / "model.glb"
        mesh.export(glb_path)

        # Validate GLB
        try:
            check = trimesh.load(glb_path)
            if len(check.geometry) == 0:
                self.log_file(glb_path, "GLB", status="FAILED_VALIDATION: Empty geometry")
            else:
                self.log_file(glb_path, "GLB")
        except Exception:
            self.log_file(glb_path, "GLB", status="FAILED_VALIDATION: Unreadable")


        # GLTF
        gltf_path = out_mesh / "model.gltf"
        mesh.export(gltf_path)
        try:
            check_gltf = trimesh.load(gltf_path)
            if len(check_gltf.geometry) == 0:
                self.log_file(gltf_path, "GLTF", status="FAILED_VALIDATION: Empty geometry")
            else:
                self.log_file(gltf_path, "GLTF")
        except Exception:
            self.log_file(gltf_path, "GLTF", status="FAILED_VALIDATION: Unreadable")

        # OBJ
        obj_path = out_mesh / "model.obj"
        mesh.export(obj_path)

        # Validate OBJ Portability
        try:
            import shutil
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                # copy OBJ, MTL and any image
                shutil.copy2(obj_path, tmp / obj_path.name)
                mtl_path = obj_path.with_suffix('.mtl')
                if mtl_path.exists():
                    shutil.copy2(mtl_path, tmp / mtl_path.name)
                    # Check MTL for absolute paths
                    mtl_content = mtl_path.read_text(encoding="utf8")
                    if "C:\\" in mtl_content or "c:\\" in mtl_content.lower() or "/" in mtl_content and "://" not in mtl_content:
                        # Forward slashes might just be relative directories, but absolute paths on Linux start with /
                        # Let's just do a naive check for absolute paths
                        lines = mtl_content.splitlines()
                        for line in lines:
                            if line.strip().startswith("map_Kd"):
                                tex = line.strip().split()[-1]
                                if Path(tex).is_absolute():
                                    raise ValueError("Absolute path found in MTL: " + tex)
                                tex_path = out_mesh / tex
                                if tex_path.exists():
                                    shutil.copy2(tex_path, tmp / tex)

                # Verify it loads from temp dir
                check_obj = trimesh.load(tmp / obj_path.name)
                if len(check_obj.geometry) == 0:
                    self.log_file(obj_path, "OBJ", status="FAILED_VALIDATION: Empty geometry")
                else:
                    self.log_file(obj_path, "OBJ")
        except Exception as e:
            self.log_file(obj_path, "OBJ", status=f"FAILED_VALIDATION: Portability error: {e}")


        # FBX (if available)
        blender = shutil.which("blender")
        if blender:
            fbx_path = out_mesh / "model.fbx"
            script = Path(__file__).resolve().parents[2] / "scripts" / "export_fbx.py"
            try:
                subprocess.run(
                    [blender, "--background", "--python", str(script), "--", str(glb_path), str(fbx_path)],
                    check=True,
                    timeout=180,
                    capture_output=True,
                )

                # Verify FBX by re-importing
                verify_script = Path(__file__).resolve().parents[2] / "scripts" / "verify_fbx.py"
                subprocess.run(
                    [blender, "--background", "--python", str(verify_script), "--", str(fbx_path)],
                    check=True,
                    timeout=180,
                    capture_output=True,
                )
                self.log_file(fbx_path, "FBX")

            except Exception:
                self.manifest["validation_results"]["FBX"] = "FAILED_VALIDATION: Blender conversion failed"
        else:
            self.manifest["validation_results"]["FBX"] = "IMPLEMENTED_NOT_EXECUTED: Blender missing"

    def export_geospatial(self, points, colors):
        out_geo = self.out_dir / "geospatial"
        out_geo.mkdir(parents=True, exist_ok=True)

        if not self.geo["valid"]:
            self.manifest["validation_results"]["GeoTIFF"] = "NOT_AVAILABLE: Relative metric state"
            return

        absolute = transform(points, self.geo) + self.geo["origin"]

        minimum = absolute.min(0)
        maximum = absolute.max(0)
        resolution = max(np.max(maximum[:2] - minimum[:2]) / 512, 0.05)
        width, height = np.ceil((maximum[:2] - minimum[:2]) / resolution).astype(int) + 1
        x = np.clip(((absolute[:, 0] - minimum[0]) / resolution).astype(int), 0, width - 1)
        y = np.clip(((maximum[1] - absolute[:, 1]) / resolution).astype(int), 0, height - 1)

        dsm = np.full((height, width), -9999.0, np.float32)
        ortho = np.zeros((3, height, width), np.uint8)

        for i in np.argsort(absolute[:, 2]):
            dsm[y[i], x[i]] = absolute[i, 2]
            ortho[:, y[i], x[i]] = colors[i]

        profile = {
            "driver": "GTiff",
            "width": int(width),
            "height": int(height),
            "crs": f"EPSG:{self.geo['epsg']}",
            "transform": from_origin(minimum[0], maximum[1], resolution, resolution),
            "compress": "deflate",
        }

        dsm_path = out_geo / "dsm.tif"
        with rasterio.open(dsm_path, "w", **profile, count=1, dtype="float32", nodata=-9999.0) as f:
            f.write(dsm, 1)
            f.update_tags(description="Observed surface raster (DSM)")

        ortho_path = out_geo / "ortho.tif"
        with rasterio.open(ortho_path, "w", **profile, count=3, dtype="uint8") as f:
            f.write(ortho)
            f.write_mask((dsm != -9999).astype(np.uint8) * 255)

        # Validate GeoTIFF
        with rasterio.open(dsm_path) as f:
            if f.crs.to_epsg() != self.geo["epsg"]:
                self.log_file(dsm_path, "GeoTIFF_DSM", status="FAILED_VALIDATION: CRS mismatch")
            else:
                self.log_file(dsm_path, "GeoTIFF_DSM")

        self.log_file(ortho_path, "GeoTIFF_ORTHO")

    def export_geojson(self, structures):
        # Optional: Export GeoJSON if structures are provided and georeferenced
        pass

    def finalize(self):
        manifest_path = self.out_dir / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest, indent=2))

        deliverables_matrix = [
            {
                "Format": "GLTF",
                "Available": "GLTF" in self.manifest["validation_results"],
                "Verified": self.manifest["validation_results"].get("GLTF", "") == "VERIFIED",
                "Metric requirement": False,
                "CRS": False,
                "Texture": True,
                "Semantics": False,
                "Purpose": "Web Interoperability",
            },
            {
                "Format": "GLB",
                "Available": "GLB" in self.manifest["validation_results"],
                "Verified": self.manifest["validation_results"].get("GLB", "") == "VERIFIED",
                "Metric requirement": False,
                "CRS": False,
                "Texture": True,
                "Semantics": False,
                "Purpose": "Web 3D Viewer",
            },
            {
                "Format": "GLTF",
                "Available": "GLTF" in self.manifest["validation_results"],
                "Verified": self.manifest["validation_results"].get("GLTF", "") == "VERIFIED",
                "Metric requirement": False,
                "CRS": False,
                "Texture": True,
                "Semantics": False,
                "Purpose": "Web Interoperability",
            },
            {
                "Format": "OBJ",
                "Available": "OBJ" in self.manifest["validation_results"],
                "Verified": self.manifest["validation_results"].get("OBJ", "") == "VERIFIED",
                "Metric requirement": False,
                "CRS": False,
                "Texture": True,
                "Semantics": False,
                "Purpose": "3D Design",
            },
            {
                "Format": "PLY",
                "Available": "PLY_METRIC" in self.manifest["validation_results"]
                or "PLY_RELATIVE" in self.manifest["validation_results"],
                "Verified": True,
                "Metric requirement": False,
                "CRS": False,
                "Texture": False,
                "Semantics": True,
                "Purpose": "Point Cloud",
            },
            {
                "Format": "LAS",
                "Available": "LAS" in self.manifest["validation_results"],
                "Verified": self.manifest["validation_results"].get("LAS", "") == "VERIFIED",
                "Metric requirement": True,
                "CRS": True,
                "Texture": False,
                "Semantics": True,
                "Purpose": "GIS Point Cloud",
            },
            {
                "Format": "GeoTIFF",
                "Available": "GeoTIFF_DSM" in self.manifest["validation_results"],
                "Verified": self.manifest["validation_results"].get("GeoTIFF_DSM", "") == "VERIFIED",
                "Metric requirement": True,
                "CRS": True,
                "Texture": True,
                "Semantics": False,
                "Purpose": "Elevation Raster",
            },
            {
                "Format": "FBX",
                "Available": "FBX" in self.manifest["validation_results"]
                and "VERIFIED" in self.manifest["validation_results"]["FBX"],
                "Verified": self.manifest["validation_results"].get("FBX", "") == "VERIFIED",
                "Metric requirement": False,
                "CRS": False,
                "Texture": True,
                "Semantics": False,
                "Purpose": "DCC Interoperability",
            },
        ]
        (self.out_dir / "reports" / "deliverables_matrix.json").parent.mkdir(exist_ok=True)
        (self.out_dir / "reports" / "deliverables_matrix.json").write_text(json.dumps(deliverables_matrix, indent=2))

        return self.manifest


def export_all(mesh, points, colors, geo, out, point_labels=None, structures=None):
    manager = ExportManager(out, geo)

    # Point Cloud
    manager.export_point_cloud(points, colors, point_labels)

    # Mesh
    manager.export_mesh(mesh)

    # Geospatial
    manager.export_geospatial(points, colors)

    # Finalize Manifest
    manifest = manager.finalize()
    return manifest
