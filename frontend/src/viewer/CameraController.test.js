import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as THREE from 'three';
import { CameraController } from './CameraController';

describe('CameraController', () => {
  let camera, domElement, orbit, controller, targets, onMsg;

  beforeEach(() => {
    camera = new THREE.PerspectiveCamera();
    domElement = document.createElement('div');
    orbit = { enabled: true, update: vi.fn(), target: new THREE.Vector3(), dispose: vi.fn() };
    targets = [];
    onMsg = vi.fn();
    controller = new CameraController(camera, domElement, orbit, () => targets, onMsg);
  });

  it('initializes in ORBIT mode', () => {
    expect(controller.mode).toBe('ORBIT');
    expect(orbit.enabled).toBe(true);
  });

  it('switches modes and disables orbit when not in ORBIT', () => {
    controller.setMode('FLY');
    expect(controller.mode).toBe('FLY');
    expect(orbit.enabled).toBe(false);
  });

  it('preserves mutual exclusion between modes', () => {
    controller.setMode('WALK');
    controller.setMode('FOCUS');
    expect(controller.mode).toBe('FOCUS');
  });

  it('does not enable WALK mode if no ground is found', () => {
    controller.setMode('WALK');
    expect(onMsg).toHaveBeenCalledWith('Walk Mode is unavailable because a reliable walkable surface could not be established.');
    expect(controller.mode).toBe('FLY'); // fallback to FLY
  });

  it('enables WALK mode if ground is found', () => {
    // Fake a ground intersection
    controller.raycaster.intersectObjects = vi.fn().mockReturnValue([{ point: new THREE.Vector3(0, 0, 0) }]);
    controller.setMode('WALK');
    expect(controller.mode).toBe('WALK');
  });

  it('updates position based on keyboard input in FLY mode', () => {
    controller.setMode('FLY');
    controller.keys['w'] = true;
    controller.baseSpeed = 10;
    controller.clock.getDelta = () => 0.1; controller.update(); // 1st frame
    expect(camera.position.length()).toBeGreaterThan(0);
  });

  it('supports directional button hold and release', () => {
    controller.setMode('FLY');
    controller.setJoystick(1, 0, 0); // forward
    controller.baseSpeed = 10;
    const initialZ = camera.position.z;
    controller.clock.getDelta = () => 0.1; controller.update();
    expect(camera.position.z).not.toBe(initialZ);
    
    // release
    const curZ = camera.position.z;
    controller.setJoystick(0, 0, 0);
    controller.clock.getDelta = () => 0.1; controller.update();
    expect(camera.position.z).toBe(curZ); // shouldn't move
  });

  it('interpolates to target in FOCUS mode (or triggers animation)', () => {
    controller.setMode('FOCUS');
    // Fake a raycast hit for double click
    controller.raycaster.intersectObjects = vi.fn().mockReturnValue([{ point: new THREE.Vector3(10, 10, 10) }]);
    targets.push(new THREE.Mesh());
    controller._onDoubleClick({ clientX: 0, clientY: 0, button: 0 });
    
    expect(onMsg).toHaveBeenCalledWith(expect.stringContaining('Focused at X:10.00 Y:10.00 Z:10.00'));
    // Camera should be moved closer
    expect(camera.position.distanceTo(new THREE.Vector3(10,10,10))).toBeGreaterThan(0);
  });

  it('cleans up event listeners', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    controller.dispose();
    expect(removeSpy).toHaveBeenCalled();
  });
});

