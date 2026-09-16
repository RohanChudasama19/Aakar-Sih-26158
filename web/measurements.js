/**
 * AeroRecon Measurement Math Module
 * Pure functions for geometric measurements.
 */

// Define the canonical vertical axis from AeroRecon's world convention.
// For standard OpenSfM/SfM exports typically used here, Z is up (inverse gravity).
export const VERTICAL_AXIS = "z";

export function getMeasurementCapabilities(metricState) {
    const isMetric = metricState === "METRIC_SCALE" || metricState === "GEOREFERENCED_METRIC";
    return {
        metric_distance: isMetric,
        area: isMetric,
        slope: isMetric,
        world_coordinates: metricState === "GEOREFERENCED_METRIC",
        unit: isMetric ? "m" : "model units",
        area_unit: isMetric ? "m²" : "model units²"
    };
}

export function distance3D(a, b) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dz = b.z - a.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

export function horizontalDistance(a, b, vAxis = VERTICAL_AXIS) {
    let dx = b.x - a.x;
    let dy = b.y - a.y;
    let dz = b.z - a.z;
    if (vAxis === 'z') return Math.sqrt(dx * dx + dy * dy);
    if (vAxis === 'y') return Math.sqrt(dx * dx + dz * dz);
    return Math.sqrt(dy * dy + dz * dz); // x vertical
}

export function verticalDifference(a, b, vAxis = VERTICAL_AXIS) {
    if (vAxis === 'z') return b.z - a.z;
    if (vAxis === 'y') return b.y - a.y;
    return b.x - a.x;
}

export function deltaXYZ(a, b) {
    return {
        x: b.x - a.x,
        y: b.y - a.y,
        z: b.z - a.z
    };
}

export function slope(a, b, vAxis = VERTICAL_AXIS) {
    const horiz = horizontalDistance(a, b, vAxis);
    const vert = verticalDifference(a, b, vAxis);
    const rad = Math.atan2(Math.abs(vert), horiz);
    const deg = rad * (180 / Math.PI);
    const percentage = horiz === 0 ? (vert === 0 ? 0 : Infinity) : (Math.abs(vert) / horiz) * 100;
    
    return {
        horizontal: horiz,
        vertical: vert,
        degrees: deg,
        percentage: percentage
    };
}

export function angle3(a, b, c) {
    // Angle at B between BA and BC
    const ba = { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
    const bc = { x: c.x - b.x, y: c.y - b.y, z: c.z - b.z };
    
    const lenBA = Math.sqrt(ba.x * ba.x + ba.y * ba.y + ba.z * ba.z);
    const lenBC = Math.sqrt(bc.x * bc.x + bc.y * bc.y + bc.z * bc.z);
    
    if (lenBA === 0 || lenBC === 0) return 0;
    
    const dot = ba.x * bc.x + ba.y * bc.y + ba.z * bc.z;
    const cosTheta = dot / (lenBA * lenBC);
    
    // Clamp to [-1, 1] for robustness
    const clamped = Math.max(-1, Math.min(1, cosTheta));
    return Math.acos(clamped) * (180 / Math.PI);
}

export function planarArea3D(points) {
    // Newell's method for arbitrary 3D polygon area
    if (points.length < 3) return 0;
    
    let nx = 0, ny = 0, nz = 0;
    for (let i = 0; i < points.length; i++) {
        const curr = points[i];
        const next = points[(i + 1) % points.length];
        nx += (curr.y - next.y) * (curr.z + next.z);
        ny += (curr.z - next.z) * (curr.x + next.x);
        nz += (curr.x - next.x) * (curr.y + next.y);
    }
    
    return Math.sqrt(nx * nx + ny * ny + nz * nz) / 2.0;
}

export function triangleArea(a, b, c) {
    const ab = { x: b.x - a.x, y: b.y - a.y, z: b.z - a.z };
    const ac = { x: c.x - a.x, y: c.y - a.y, z: c.z - a.z };
    
    const cross = {
        x: ab.y * ac.z - ab.z * ac.y,
        y: ab.z * ac.x - ab.x * ac.z,
        z: ab.x * ac.y - ab.y * ac.x
    };
    
    return Math.sqrt(cross.x * cross.x + cross.y * cross.y + cross.z * cross.z) / 2.0;
}

export function formatNumber(num, precision = 3) {
    if (num === null || num === undefined || isNaN(num)) return "N/A";
    if (num === Infinity) return "Infinity";
    return num.toFixed(precision);
}
