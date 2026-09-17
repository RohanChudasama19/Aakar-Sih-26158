"""
Independent Spatial Accuracy Validation
========================================
This module validates reconstruction spatial accuracy using independent checkpoints
that are NOT used in the Phase-4 GPS/camera Sim(3) alignment fit.

CRITICAL DISTINCTION
--------------------
* GPS alignment residual (rmse_m in mission_report.json) — a Sim(3) FIT residual
  computed on the same camera/GPS pairs used to estimate the transform. Not independent.

* Independent checkpoint RMSE (this module) — computed on survey-grade reference
  points that never participate in alignment. Genuinely independent.

Correspondence methods (in preferred order):
  METHOD A (EXPLICIT) — recon_x/y/z pre-supplied in CSV or from interactive picking.
  METHOD B (CLOSEST_SURFACE) — nearest point on triangle surface within search_radius_m.
                                Approximate; appropriate only when checkpoint corresponds
                                to a visible reconstructed surface.

Vertical datum handling
-----------------------
GPS altitudes, barometric altitudes, RTK heights, and surveyed elevations may use
different vertical datums (ELLIPSOIDAL, ORTHOMETRIC, LOCAL, UNKNOWN).
If vertical datums cannot be reconciled, RMSE_Z and RMSE_3D are marked NOT_VALIDATED.
Horizontal validation may still be reported where appropriate.

SIH Pass Rule (internal)
-------------------------
RMSE_3D <= 1.0 m  AND  valid_checkpoint_count >= MIN_INDEPENDENT_CHECKPOINTS

Report always displays: Horizontal RMSE, Vertical RMSE, and 3D RMSE.
"""

from __future__ import annotations

import csv
import io
import math
import struct
import warnings
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIN_INDEPENDENT_CHECKPOINTS: int = 4
DEFAULT_CHECKPOINT_SEARCH_RADIUS_M: float = 2.0
WEAK_CORRESPONDENCE_THRESHOLD_FACTOR: float = 0.5  # > 50% of search_radius -> WEAK
RMSE_3D_PASS_THRESHOLD_M: float = 1.0


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_ENOUGH_CHECKPOINTS = "NOT_ENOUGH_CHECKPOINTS"
    INVALID_REFERENCE = "INVALID_REFERENCE"


class CheckpointRole(str, Enum):
    CONTROL = "CONTROL"  # May conceptually relate to alignment. NEVER in validation RMSE.
    CHECKPOINT = "CHECKPOINT"  # Independent post-alignment validation observations only.


class CorrespondenceMethod(str, Enum):
    EXPLICIT = "EXPLICIT"
    CLOSEST_SURFACE = "CLOSEST_SURFACE"


class CheckpointStatus(str, Enum):
    VALID = "VALID"
    OUTSIDE_COVERAGE = "OUTSIDE_COVERAGE"
    WEAK_CORRESPONDENCE = "WEAK_CORRESPONDENCE"
    INVALID_VERTICAL_DATUM = "INVALID_VERTICAL_DATUM"
    INVALID_REFERENCE = "INVALID_REFERENCE"


class VerticalDatum(str, Enum):
    ELLIPSOIDAL = "ELLIPSOIDAL"
    ORTHOMETRIC = "ORTHOMETRIC"
    LOCAL = "LOCAL"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class CheckpointValidationError(ValueError):
    pass


class InvalidCRSError(ValueError):
    pass


# ---------------------------------------------------------------------------
# CSV Parsing
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = {"checkpoint_id", "latitude", "longitude", "elevation", "role"}


def parse_checkpoint_csv(path: Path | str) -> list[dict]:
    """Parse and validate a checkpoint CSV file.

    Required columns: checkpoint_id, latitude, longitude, elevation, role
    Optional columns: recon_x, recon_y, recon_z, vertical_datum,
                      reference_accuracy_horizontal_m, reference_accuracy_vertical_m,
                      survey_method

    Role values: CHECKPOINT (validation-only) | CONTROL (alignment placeholder, never in RMSE)

    Returns a list of dicts with parsed/validated fields.
    Raises CheckpointValidationError on schema violations.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")  # handle BOM
    reader = csv.DictReader(io.StringIO(text.strip()))

    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise CheckpointValidationError(f"Checkpoint CSV is missing required columns: {missing}")

    rows = []
    seen_ids: set[str] = set()

    for i, raw in enumerate(reader, start=2):  # line 1 = header
        cp_id = raw.get("checkpoint_id", "").strip()
        if not cp_id:
            raise CheckpointValidationError(f"Line {i}: empty checkpoint_id")
        if cp_id in seen_ids:
            raise CheckpointValidationError(f"Duplicate checkpoint_id: '{cp_id}'")
        seen_ids.add(cp_id)

        try:
            lat = float(raw["latitude"])
            lon = float(raw["longitude"])
            elev = float(raw["elevation"])
        except (ValueError, KeyError) as e:
            raise CheckpointValidationError(f"Line {i} ({cp_id}): non-numeric coordinate - {e}") from e

        if not (-90.0 <= lat <= 90.0):
            raise CheckpointValidationError(f"Line {i} ({cp_id}): latitude {lat} is outside +-90")
        if not (-180.0 <= lon <= 180.0):
            raise CheckpointValidationError(f"Line {i} ({cp_id}): longitude {lon} is outside +-180")

        role_str = raw.get("role", "").strip().upper()
        if role_str not in {r.value for r in CheckpointRole}:
            raise CheckpointValidationError(
                f"Line {i} ({cp_id}): invalid role '{role_str}'. Must be CHECKPOINT or CONTROL."
            )
        role = CheckpointRole(role_str)

        recon_x = recon_y = recon_z = None
        has_explicit = all(raw.get(k, "").strip() not in ("", None) for k in ("recon_x", "recon_y", "recon_z"))
        if has_explicit:
            try:
                recon_x = float(raw["recon_x"])
                recon_y = float(raw["recon_y"])
                recon_z = float(raw["recon_z"])
            except ValueError as e:
                raise CheckpointValidationError(f"Line {i} ({cp_id}): invalid recon_x/y/z - {e}") from e

        vd_str = raw.get("vertical_datum", "UNKNOWN").strip().upper() or "UNKNOWN"
        try:
            vertical_datum = VerticalDatum(vd_str)
        except ValueError:
            warnings.warn(f"Checkpoint {cp_id}: unknown vertical_datum '{vd_str}', treating as UNKNOWN")
            vertical_datum = VerticalDatum.UNKNOWN

        rows.append(
            {
                "checkpoint_id": cp_id,
                "latitude": lat,
                "longitude": lon,
                "elevation": elev,
                "role": role,
                "recon_x": recon_x,
                "recon_y": recon_y,
                "recon_z": recon_z,
                "has_explicit_correspondence": has_explicit,
                "vertical_datum": vertical_datum,
                "reference_accuracy_horizontal_m": _safe_float(raw.get("reference_accuracy_horizontal_m")),
                "reference_accuracy_vertical_m": _safe_float(raw.get("reference_accuracy_vertical_m")),
                "survey_method": raw.get("survey_method", "UNKNOWN").strip() or "UNKNOWN",
            }
        )

    if not rows:
        raise CheckpointValidationError("Checkpoint CSV contains no data rows")

    return rows


def _safe_float(v: str | None) -> float | None:
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# CRS Projection
# ---------------------------------------------------------------------------
def project_checkpoints(
    checkpoints: list[dict],
    epsg: int,
    origin_utm: "np.ndarray",
) -> list[dict]:
    """Convert (lat, lon, elevation) to local UTM frame coordinates in the reconstruction frame."""
    try:
        from pyproj import Transformer
    except ImportError as e:
        raise InvalidCRSError("pyproj is required for CRS conversion") from e

    try:
        tx = Transformer.from_crs(4326, epsg, always_xy=True)
    except Exception as e:
        raise InvalidCRSError(f"Invalid EPSG {epsg}: {e}") from e

    origin = np.asarray(origin_utm, dtype=float)
    result = []
    for cp in checkpoints:
        easting_m, northing_m = tx.transform(cp["longitude"], cp["latitude"])
        local_x = easting_m - origin[0]
        local_y = northing_m - origin[1]
        local_z = cp["elevation"] - origin[2]
        result.append(
            {
                **cp,
                "utm_e": easting_m,
                "utm_n": northing_m,
                "local_x": local_x,
                "local_y": local_y,
                "local_z": local_z,
            }
        )
    return result


# ---------------------------------------------------------------------------
# PLY Reading
# ---------------------------------------------------------------------------
def _read_ply_vertices(ply_path: Path) -> np.ndarray:
    """Read XYZ vertices from a binary or ASCII PLY file. Returns (N,3) array."""
    data = ply_path.read_bytes()
    header_end = data.find(b"end_header")
    if header_end == -1:
        raise ValueError("Invalid PLY: no end_header")
    header = data[:header_end].decode("ascii", errors="replace")
    body = data[header_end + len("end_header") :].lstrip(b"\r\n")

    n_verts = 0
    is_binary_le = False
    for line in header.splitlines():
        line = line.strip()
        if line.startswith("element vertex"):
            n_verts = int(line.split()[-1])
        if line == "format binary_little_endian 1.0":
            is_binary_le = True

    if n_verts == 0:
        return np.zeros((0, 3), dtype=np.float32)

    props: list[tuple[str, str]] = []
    in_vertex = False
    for line in header.splitlines():
        line = line.strip()
        if line.startswith("element vertex"):
            in_vertex = True
            continue
        if line.startswith("element ") and in_vertex:
            break
        if in_vertex and line.startswith("property"):
            parts = line.split()
            if len(parts) == 3:
                props.append((parts[1], parts[2]))

    if is_binary_le:
        fmt_map = {
            "float": "f",
            "float32": "f",
            "double": "d",
            "float64": "d",
            "uchar": "B",
            "uint8": "B",
            "char": "b",
            "int8": "b",
            "short": "h",
            "int16": "h",
            "ushort": "H",
            "uint16": "H",
            "int": "i",
            "int32": "i",
            "uint": "I",
            "uint32": "I",
        }
        fmt = "<" + "".join(fmt_map.get(t, "f") for t, _ in props)
        stride = struct.calcsize(fmt)
        prop_names = [n for _, n in props]
        xi = prop_names.index("x")
        yi = prop_names.index("y")
        zi = prop_names.index("z")
        verts = np.empty((n_verts, 3), dtype=np.float64)
        for k in range(n_verts):
            row = struct.unpack_from(fmt, body, k * stride)
            verts[k, 0] = row[xi]
            verts[k, 1] = row[yi]
            verts[k, 2] = row[zi]
        return verts
    else:
        lines = body.decode("ascii", errors="replace").strip().splitlines()
        prop_names = [n for _, n in props]
        xi = prop_names.index("x")
        yi = prop_names.index("y")
        zi = prop_names.index("z")
        verts_list: list[list[float]] = []
        for line in lines[:n_verts]:
            vals = line.split()
            verts_list.append([float(vals[xi]), float(vals[yi]), float(vals[zi])])
        return np.array(verts_list, dtype=np.float64)


def _read_ply_faces(ply_path: Path) -> "np.ndarray | None":
    """Read triangle face indices from a PLY. Returns (F,3) int array or None."""
    data = ply_path.read_bytes()
    header_end = data.find(b"end_header")
    if header_end == -1:
        return None
    header = data[:header_end].decode("ascii", errors="replace")
    body = data[header_end + len("end_header") :].lstrip(b"\r\n")

    n_verts = 0
    n_faces = 0
    is_binary_le = False
    for line in header.splitlines():
        s = line.strip()
        if s.startswith("element vertex"):
            n_verts = int(s.split()[-1])
        if s.startswith("element face"):
            n_faces = int(s.split()[-1])
        if s == "format binary_little_endian 1.0":
            is_binary_le = True

    if n_faces == 0:
        return None

    props: list[tuple[str, str]] = []
    in_vertex = False
    for line in header.splitlines():
        s = line.strip()
        if s.startswith("element vertex"):
            in_vertex = True
            continue
        if s.startswith("element ") and in_vertex:
            break
        if in_vertex and s.startswith("property") and not s.startswith("property list"):
            parts = s.split()
            if len(parts) == 3:
                props.append((parts[1], parts[2]))

    if is_binary_le:
        fmt_map = {
            "float": "f",
            "float32": "f",
            "double": "d",
            "float64": "d",
            "uchar": "B",
            "uint8": "B",
            "char": "b",
            "int8": "b",
            "short": "h",
            "int16": "h",
            "ushort": "H",
            "uint16": "H",
            "int": "i",
            "int32": "i",
            "uint": "I",
            "uint32": "I",
        }
        vert_fmt = "<" + "".join(fmt_map.get(t, "f") for t, _ in props)
        vert_stride = struct.calcsize(vert_fmt)
        verts_end = n_verts * vert_stride

        faces = []
        offset = verts_end
        for _ in range(n_faces):
            if offset >= len(body):
                break
            n_idx = struct.unpack_from("<B", body, offset)[0]
            offset += 1
            if n_idx == 3:
                a, b, c = struct.unpack_from("<iii", body, offset)
                faces.append([a, b, c])
            offset += n_idx * 4
        return np.array(faces, dtype=np.int32) if faces else None
    return None


# ---------------------------------------------------------------------------
# Closest point on triangle
# ---------------------------------------------------------------------------
def _closest_point_on_triangle(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, float]:
    """Project point p onto triangle (a, b, c). Returns (closest_point, distance)."""
    ab = b - a
    ac = c - a
    ap = p - a
    d1, d2 = float(np.dot(ab, ap)), float(np.dot(ac, ap))
    if d1 <= 0 and d2 <= 0:
        return a, float(np.linalg.norm(p - a))
    bp = p - b
    d3, d4 = float(np.dot(ab, bp)), float(np.dot(ac, bp))
    if d3 >= 0 and d4 <= d3:
        return b, float(np.linalg.norm(p - b))
    cp_v = p - c
    d5, d6 = float(np.dot(ab, cp_v)), float(np.dot(ac, cp_v))
    if d6 >= 0 and d5 <= d6:
        return c, float(np.linalg.norm(p - c))
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        pt = a + v * ab
        return pt, float(np.linalg.norm(p - pt))
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        pt = a + w * ac
        return pt, float(np.linalg.norm(p - pt))
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        pt = b + w * (c - b)
        return pt, float(np.linalg.norm(p - pt))
    denom = 1.0 / (vc + vb + va)
    v = vb * denom
    u = va * denom
    pt = a + v * ab + u * ac
    return pt, float(np.linalg.norm(p - pt))


# ---------------------------------------------------------------------------
# Correspondence
# ---------------------------------------------------------------------------
def find_correspondence(
    cp: dict,
    ply_path: "Path | None",
    geo: dict,
    search_radius_m: float = DEFAULT_CHECKPOINT_SEARCH_RADIUS_M,
) -> dict:
    """Find the reconstructed surface point corresponding to a checkpoint.

    METHOD A (EXPLICIT): Uses pre-supplied recon_x/y/z (in local UTM frame). Preferred.
    METHOD B (CLOSEST_SURFACE): Finds closest point on actual mesh triangles.
        KD-tree accelerates candidate selection; then projects onto candidate triangles.
        NOT equivalent to nearest-vertex matching.

    WARNING: CLOSEST_SURFACE matching is appropriate only when the surveyed checkpoint
    physically corresponds to a visible reconstructed surface. It must not be treated
    as equivalent to manually surveyed feature correspondence in all situations.
    """
    cp_local = np.array([cp["local_x"], cp["local_y"], cp["local_z"]])
    s = float(geo["scale"])
    R = np.array(geo["rotation"])
    t = np.array(geo["translation"])

    # METHOD A
    if cp.get("has_explicit_correspondence") and cp.get("recon_x") is not None:
        match_local = np.array([cp["recon_x"], cp["recon_y"], cp["recon_z"]])
        dist = float(np.linalg.norm(cp_local - match_local))
        return {
            **cp,
            "correspondence_method": CorrespondenceMethod.EXPLICIT.value,
            "correspondence_distance_m": dist,
            "checkpoint_status": CheckpointStatus.VALID.value,
            "match_x": float(match_local[0]),
            "match_y": float(match_local[1]),
            "match_z": float(match_local[2]),
        }

    # METHOD B
    if not ply_path or not Path(ply_path).exists():
        return {
            **cp,
            "correspondence_method": CorrespondenceMethod.CLOSEST_SURFACE.value,
            "correspondence_distance_m": None,
            "checkpoint_status": CheckpointStatus.OUTSIDE_COVERAGE.value,
            "match_x": None,
            "match_y": None,
            "match_z": None,
        }

    verts_sfm = _read_ply_vertices(Path(ply_path))
    if len(verts_sfm) == 0:
        return {
            **cp,
            "correspondence_method": CorrespondenceMethod.CLOSEST_SURFACE.value,
            "correspondence_distance_m": None,
            "checkpoint_status": CheckpointStatus.OUTSIDE_COVERAGE.value,
            "match_x": None,
            "match_y": None,
            "match_z": None,
        }

    verts_local = (s * verts_sfm) @ R.T + t

    try:
        from scipy.spatial import KDTree

        kd = KDTree(verts_local)
        dist_vertex, idx_vertex = kd.query(cp_local, workers=1)
    except ImportError:
        dists = np.linalg.norm(verts_local - cp_local, axis=1)
        idx_vertex = int(np.argmin(dists))
        dist_vertex = float(dists[idx_vertex])

    if dist_vertex > search_radius_m:
        return {
            **cp,
            "correspondence_method": CorrespondenceMethod.CLOSEST_SURFACE.value,
            "correspondence_distance_m": float(dist_vertex),
            "checkpoint_status": CheckpointStatus.OUTSIDE_COVERAGE.value,
            "match_x": None,
            "match_y": None,
            "match_z": None,
        }

    faces = _read_ply_faces(Path(ply_path))
    best_dist = float(dist_vertex)
    best_pt = verts_local[idx_vertex]

    if faces is not None and len(faces) > 0:
        try:
            from scipy.spatial import KDTree

            kd2 = KDTree(verts_local)
            cand_idxs = kd2.query_ball_point(cp_local, min(dist_vertex * 3 + 1.0, search_radius_m + 0.5))
        except ImportError:
            cand_idxs = list(range(len(verts_local)))
        cand_set = set(int(i) for i in cand_idxs)
        for face in faces:
            if int(face[0]) in cand_set or int(face[1]) in cand_set or int(face[2]) in cand_set:
                a = verts_local[face[0]]
                b = verts_local[face[1]]
                c = verts_local[face[2]]
                pt, d = _closest_point_on_triangle(cp_local, a, b, c)
                if d < best_dist:
                    best_dist = d
                    best_pt = pt

    weak_thresh = WEAK_CORRESPONDENCE_THRESHOLD_FACTOR * search_radius_m
    if best_dist > search_radius_m:
        status = CheckpointStatus.OUTSIDE_COVERAGE.value
        best_pt_out = None
    elif best_dist > weak_thresh:
        status = CheckpointStatus.WEAK_CORRESPONDENCE.value
        best_pt_out = best_pt
    else:
        status = CheckpointStatus.VALID.value
        best_pt_out = best_pt

    return {
        **cp,
        "correspondence_method": CorrespondenceMethod.CLOSEST_SURFACE.value,
        "correspondence_distance_m": float(best_dist),
        "checkpoint_status": status,
        "match_x": float(best_pt_out[0]) if best_pt_out is not None else None,
        "match_y": float(best_pt_out[1]) if best_pt_out is not None else None,
        "match_z": float(best_pt_out[2]) if best_pt_out is not None else None,
    }


# ---------------------------------------------------------------------------
# Residuals and RMSE
# ---------------------------------------------------------------------------
def compute_residuals(
    checkpoints: list[dict],
    recon_vertical_datum: VerticalDatum = VerticalDatum.UNKNOWN,
) -> list[dict]:
    """Compute per-checkpoint error components.

    CRITICAL: CONTROL-role checkpoints are excluded from this function.
    They must NEVER appear in validation RMSE, as they may conceptually participate
    in alignment. This is enforced here — callers must pre-filter to CHECKPOINT role.
    """
    result = []
    for cp in checkpoints:
        # Safety: double-check role
        if cp.get("role") == CheckpointRole.CONTROL or cp.get("role") == "CONTROL":
            continue

        if cp.get("checkpoint_status") not in (
            CheckpointStatus.VALID.value,
            CheckpointStatus.WEAK_CORRESPONDENCE.value,
        ):
            result.append(
                {
                    **cp,
                    "dx": None,
                    "dy": None,
                    "dz": None,
                    "horizontal_error_m": None,
                    "error_3d_m": None,
                    "vertical_datum_mismatch": False,
                }
            )
            continue

        if cp.get("match_x") is None:
            result.append(
                {
                    **cp,
                    "dx": None,
                    "dy": None,
                    "dz": None,
                    "horizontal_error_m": None,
                    "error_3d_m": None,
                    "vertical_datum_mismatch": False,
                }
            )
            continue

        dx = cp["local_x"] - cp["match_x"]
        dy = cp["local_y"] - cp["match_y"]
        dz = cp["local_z"] - cp["match_z"]
        horiz = math.sqrt(dx**2 + dy**2)
        err3d = math.sqrt(dx**2 + dy**2 + dz**2)

        cp_datum = cp.get("vertical_datum", VerticalDatum.UNKNOWN)
        if isinstance(cp_datum, str):
            try:
                cp_datum = VerticalDatum(cp_datum)
            except ValueError:
                cp_datum = VerticalDatum.UNKNOWN

        mismatch = (
            cp_datum != VerticalDatum.UNKNOWN
            and recon_vertical_datum != VerticalDatum.UNKNOWN
            and cp_datum != recon_vertical_datum
        )

        result.append(
            {
                **cp,
                "dx": float(dx),
                "dy": float(dy),
                "dz": float(dz),
                "horizontal_error_m": float(horiz),
                "error_3d_m": float(err3d),
                "vertical_datum_mismatch": mismatch,
            }
        )
    return result


def compute_rmse(residuals: list[dict]) -> dict:
    """Aggregate residuals into RMSE metrics. Only includes rows where dx is not None."""
    valid = [r for r in residuals if r.get("dx") is not None]
    n = len(valid)

    if n == 0:
        return {
            "checkpoint_count_used": 0,
            "rmse_x_m": None,
            "rmse_y_m": None,
            "rmse_z_m": None,
            "rmse_horizontal_m": None,
            "rmse_3d_m": None,
            "mean_3d_error_m": None,
            "median_3d_error_m": None,
            "max_3d_error_m": None,
            "vertical_z_validated": False,
        }

    dx_sq = [r["dx"] ** 2 for r in valid]
    dy_sq = [r["dy"] ** 2 for r in valid]
    dz_sq = [r["dz"] ** 2 for r in valid]
    h_sq = [r["horizontal_error_m"] ** 2 for r in valid]
    e3d = [r["error_3d_m"] for r in valid]
    z_validated = not any(r.get("vertical_datum_mismatch", False) for r in valid)

    return {
        "checkpoint_count_used": n,
        "rmse_x_m": float(math.sqrt(sum(dx_sq) / n)),
        "rmse_y_m": float(math.sqrt(sum(dy_sq) / n)),
        "rmse_z_m": float(math.sqrt(sum(dz_sq) / n)) if z_validated else None,
        "rmse_horizontal_m": float(math.sqrt(sum(h_sq) / n)),
        "rmse_3d_m": float(math.sqrt(sum(v**2 for v in e3d) / n)) if z_validated else None,
        "mean_3d_error_m": float(sum(e3d) / n),
        "median_3d_error_m": float(sorted(e3d)[n // 2]),
        "max_3d_error_m": float(max(e3d)),
        "vertical_z_validated": z_validated,
    }


def decide_status(rmse: dict, n_valid: int) -> ValidationStatus:
    """Apply the SIH internal pass rule: RMSE_3D <= 1.0 m AND n_valid >= 4."""
    if n_valid < MIN_INDEPENDENT_CHECKPOINTS:
        return ValidationStatus.NOT_ENOUGH_CHECKPOINTS
    if rmse["rmse_3d_m"] is None:
        return ValidationStatus.FAILED  # Cannot validate 3D; conservative
    if rmse["rmse_3d_m"] <= RMSE_3D_PASS_THRESHOLD_M:
        return ValidationStatus.PASSED
    return ValidationStatus.FAILED


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------
def validate(
    geo: dict,
    ply_path: "Path | str | None",
    checkpoint_csv_path: "Path | str",
    search_radius_m: float = DEFAULT_CHECKPOINT_SEARCH_RADIUS_M,
    recon_vertical_datum: VerticalDatum = VerticalDatum.UNKNOWN,
) -> dict[str, Any]:
    """Run independent spatial accuracy validation.

    IMPORTANT: CONTROL-role checkpoints are parsed for documentation but never
    used in RMSE computation. The Phase-4 Sim(3) alignment fit uses GPS trajectory
    positions, not these checkpoints. A test verifies this leakage prevention.
    """
    epsg = geo.get("epsg")
    origin = geo.get("origin")
    warnings_list: list[str] = []

    if not epsg or not origin:
        return {
            "status": ValidationStatus.INVALID_REFERENCE.value,
            "reason": "Georeferencing parameters (epsg/origin) not available.",
            "method": "N/A",
            "crs": None,
            "checkpoint_count_total": 0,
            "checkpoint_count_used": 0,
        }

    try:
        raw_cps = parse_checkpoint_csv(Path(checkpoint_csv_path))
    except CheckpointValidationError as e:
        return {
            "status": ValidationStatus.INVALID_REFERENCE.value,
            "reason": str(e),
            "method": "N/A",
            "crs": f"EPSG:{epsg}",
            "checkpoint_count_total": 0,
            "checkpoint_count_used": 0,
        }

    total = len(raw_cps)
    n_control = sum(1 for cp in raw_cps if cp["role"] == CheckpointRole.CONTROL)
    n_checkpoint = total - n_control

    if n_checkpoint == 0:
        return {
            "status": ValidationStatus.NOT_AVAILABLE.value,
            "reason": "No CHECKPOINT-role rows found. All rows are CONTROL or empty.",
            "crs": f"EPSG:{epsg}",
            "checkpoint_count_total": total,
            "checkpoint_count_used": 0,
        }

    try:
        projected = project_checkpoints(raw_cps, epsg, origin)
    except InvalidCRSError as e:
        return {
            "status": ValidationStatus.INVALID_REFERENCE.value,
            "reason": str(e),
            "crs": f"EPSG:{epsg}",
            "checkpoint_count_total": total,
            "checkpoint_count_used": 0,
        }

    ply_path_obj = Path(ply_path) if ply_path else None
    matched = []
    for cp in projected:
        if cp["role"] == CheckpointRole.CONTROL:
            matched.append(
                {
                    **cp,
                    "correspondence_method": "N/A (CONTROL - excluded from validation RMSE)",
                    "correspondence_distance_m": None,
                    "checkpoint_status": "CONTROL",
                    "match_x": None,
                    "match_y": None,
                    "match_z": None,
                }
            )
        else:
            matched.append(find_correspondence(cp, ply_path_obj, geo, search_radius_m))

    residuals = compute_residuals(
        [
            cp
            for cp in matched
            if cp.get("role") == CheckpointRole.CHECKPOINT
            or (isinstance(cp.get("role"), str) and cp.get("role") == "CHECKPOINT")
        ],
        recon_vertical_datum=recon_vertical_datum,
    )

    if any(r.get("vertical_datum_mismatch") for r in residuals):
        warnings_list.append(
            "Some checkpoints have a vertical datum differing from reconstruction datum. "
            "RMSE_Z and RMSE_3D may be unreliable. Horizontal RMSE is still valid."
        )
    weak = [r for r in residuals if r.get("checkpoint_status") == CheckpointStatus.WEAK_CORRESPONDENCE.value]
    if weak:
        warnings_list.append(
            f"{len(weak)} checkpoint(s) with weak auto-correspondence "
            f"(distance > {WEAK_CORRESPONDENCE_THRESHOLD_FACTOR * search_radius_m:.1f} m): "
            f"{[w['checkpoint_id'] for w in weak]}"
        )

    rmse = compute_rmse(residuals)
    n_valid = rmse["checkpoint_count_used"]
    status = decide_status(rmse, n_valid)

    methods = {r.get("correspondence_method") for r in residuals if r.get("dx") is not None}
    method_str = "+".join(sorted(str(m) for m in methods)) if methods else "N/A"

    def _role_str(r: Any) -> str:
        return r.value if hasattr(r, "value") else str(r)

    def _datum_str(d: Any) -> str:
        return d.value if hasattr(d, "value") else str(d)

    cp_detail = []
    for r in matched:
        cp_detail.append(
            {
                "checkpoint_id": r["checkpoint_id"],
                "role": _role_str(r["role"]),
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "elevation": r["elevation"],
                "vertical_datum": _datum_str(r.get("vertical_datum", VerticalDatum.UNKNOWN)),
                "survey_method": r.get("survey_method", "UNKNOWN"),
                "reference_accuracy_horizontal_m": r.get("reference_accuracy_horizontal_m"),
                "reference_accuracy_vertical_m": r.get("reference_accuracy_vertical_m"),
                "correspondence_method": r.get("correspondence_method"),
                "correspondence_distance_m": r.get("correspondence_distance_m"),
                "checkpoint_status": r.get("checkpoint_status"),
                "dx": r.get("dx"),
                "dy": r.get("dy"),
                "dz": r.get("dz"),
                "horizontal_error_m": r.get("horizontal_error_m"),
                "error_3d_m": r.get("error_3d_m"),
                "vertical_datum_mismatch": r.get("vertical_datum_mismatch", False),
            }
        )

    return {
        "status": status.value,
        "data_source": "SYNTHETIC" if "_synthetic" in str(checkpoint_csv_path) else "REAL",
        "method": method_str,
        "crs": f"EPSG:{epsg}",
        "vertical_datum_reconstruction": _datum_str(recon_vertical_datum),
        "search_radius_m": search_radius_m,
        "threshold_m": RMSE_3D_PASS_THRESHOLD_M,
        "min_checkpoints_required": MIN_INDEPENDENT_CHECKPOINTS,
        "checkpoint_count_total": total,
        "checkpoint_count_control": n_control,
        "checkpoint_count_checkpoint": n_checkpoint,
        "checkpoint_count_used": n_valid,
        "checkpoint_count_rejected": n_checkpoint - n_valid,
        "rmse_x_m": rmse["rmse_x_m"],
        "rmse_y_m": rmse["rmse_y_m"],
        "rmse_z_m": rmse["rmse_z_m"],
        "rmse_horizontal_m": rmse["rmse_horizontal_m"],
        "rmse_3d_m": rmse["rmse_3d_m"],
        "mean_3d_error_m": rmse["mean_3d_error_m"],
        "median_3d_error_m": rmse["median_3d_error_m"],
        "max_3d_error_m": rmse["max_3d_error_m"],
        "vertical_z_validated": rmse["vertical_z_validated"],
        "pass_rule": (
            f"RMSE_3D <= {RMSE_3D_PASS_THRESHOLD_M} m AND valid_checkpoint_count >= {MIN_INDEPENDENT_CHECKPOINTS}"
        ),
        "warnings": warnings_list,
        "checkpoints": cp_detail,
    }
