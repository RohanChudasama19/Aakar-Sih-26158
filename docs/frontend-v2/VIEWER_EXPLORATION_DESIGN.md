# AAKAR Frontend V2 Viewer Exploration Design

## Overview
To fulfill the requirement of advanced 3D camera navigation (Orbit, Focus, Walk, Fly) while preserving the core Three.js implementation (iewer.js), we must architect a mutually exclusive controller manager.

## State Machine
Only one control mode can be active at any given time.
enum CameraMode { ORBIT, FOCUS, WALK, FLY }

## 1. Orbit Mode (Existing)
- **Engine:** THREE.OrbitControls
- **Behavior:** Fixed target. Drag to rotate, scroll to zoom.
- **Constraints:** Target clamped to bounding box center.

## 2. Focus Mode
- **Engine:** Raycaster + Tween.js (or custom easing).
- **Behavior:** 
  - Double-click captures intersection point via Raycaster.
  - Animates controls.target to intersection point.
  - Animates camera.position closer to intersection point along the camera's current look vector.
  - Places a temporary THREE.Mesh (marker) at XYZ.
- **Keybinds:** F to trigger manually at center screen, R to reset to global bounds.

## 3. Walk Mode (First-Person)
- **Engine:** THREE.PointerLockControls + custom WASD physics.
- **Behavior:**
  - Locks pointer to canvas.
  - W/A/S/D move camera along local X/Z axes.
  - A persistent downward Raycaster snaps the camera's Y position to surface_height + eye_level.
  - If Raycast fails (off edge), movement is blocked or falls.
- **Speed:** Scaled by bounding box diagonal (size / 100 per frame).

## 4. Fly Mode (Free Cam)
- **Engine:** THREE.FlyControls (or custom PointerLock + WASDQE).
- **Behavior:**
  - W/A/S/D move along local X/Z.
  - Space (Up) / Shift (Down) move along local Y.
  - Mouse look modifies camera quaternion.
  - Unconstrained by gravity or surface raycasting.

## Event Management & Cleanup
Switching modes requires a strict teardown sequence to prevent listener leaks (e.g. PointerLock conflicting with OrbitControls).
`javascript
function setCameraMode(mode) {
    activeController.dispose();
    document.removeEventListener('keydown', activeController.onKeyDown);
    // Initialize new mode
}
`

## Measurement Conflict Resolution
Measurement tools (Distance, Area) require accurate clicking. When a measurement tool is active, the camera mode forces back to ORBIT (or disables drag-to-look in Fly/Walk) to ensure click events map to the scene geometry, not camera rotation.
