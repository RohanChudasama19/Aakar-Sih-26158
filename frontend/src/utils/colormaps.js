export function getColormapColor(val, min, max, invert=false) {
    if (isNaN(val) || val === null || val === undefined) return [1, 0, 1]; // Magenta for UNKNOWN
    
    let t = (val - min) / (max - min || 1);
    t = Math.max(0, Math.min(1, t));
    if (invert) t = 1 - t;
    
    // Simple Turbo/Jet-like colormap
    const r = Math.max(0, Math.min(1, 1.5 - Math.abs(1 - 4 * (t - 0.5))));
    const g = Math.max(0, Math.min(1, 1.5 - Math.abs(1 - 4 * (t - 0.25))));
    const b = Math.max(0, Math.min(1, 1.5 - Math.abs(1 - 4 * t)));
    
    return [r, g, b];
}

export function getColorScaleForMetric(metric) {
    switch (metric) {
        case 'SURFACE_SUPPORT': return { invert: true }; // High distance = bad (red)
        case 'RECONSTRUCTION_RISK': return { invert: true }; // High risk = bad (red)
        case 'GEOMETRIC_ERROR': return { invert: true }; // High error = bad (red)
        case 'POINT_DENSITY': return { invert: false }; // High density = good (blue/green)
        case 'POTENTIAL_CAMERA_VISIBILITY': return { invert: false }; // High count = good
        default: return { invert: false };
    }
}
