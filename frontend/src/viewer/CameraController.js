import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class CameraController {
  constructor(camera, domElement, orbitControls, getTargets, onMessage) {
    this.camera = camera;
    this.domElement = domElement;
    this.orbit = orbitControls;
    this.getTargets = getTargets; // () => [mesh1, mesh2]
    this.onMessage = onMessage || console.log;

    this.mode = 'ORBIT'; // ORBIT, FOCUS, WALK, FLY
    
    // Input state
    this.keys = {};
    this.mouse = new THREE.Vector2();
    this.pointerDown = false;
    this.lastPointer = { x: 0, y: 0 };
    
    // Config
    this.baseSpeed = 10.0;
    this.speedMultiplier = 1.0; // slow=0.5, normal=1, fast=3
    this.eyeHeight = 2.0;
    
    // State
    this.clock = new THREE.Clock();
    this.targetFocus = null;
    this.focusMarker = new THREE.Mesh(
      new THREE.SphereGeometry(0.5, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xff0000, depthTest: false })
    );
    this.focusMarker.renderOrder = 999;
    
    // Raycaster
    this.raycaster = new THREE.Raycaster();
    
    this._onKeyDown = this._onKeyDown.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);
    this._onPointerDown = this._onPointerDown.bind(this);
    this._onPointerMove = this._onPointerMove.bind(this);
    this._onPointerUp = this._onPointerUp.bind(this);
    this._onDoubleClick = this._onDoubleClick.bind(this);
    
    window.addEventListener('keydown', this._onKeyDown);
    window.addEventListener('keyup', this._onKeyUp);
    this.domElement.addEventListener('pointerdown', this._onPointerDown);
    this.domElement.addEventListener('pointermove', this._onPointerMove);
    window.addEventListener('pointerup', this._onPointerUp);
    this.domElement.addEventListener('dblclick', this._onDoubleClick);
    
    this.cameraDirection = new THREE.Vector3();
    this.cameraRight = new THREE.Vector3();
    
    // Virtual joystick state
    this.joystick = { forward: 0, right: 0, up: 0 };
  }
  
  setSpeed(multiplier) {
    this.speedMultiplier = multiplier;
  }
  
  setMode(newMode) {
    if (this.mode === newMode) return;
    
    // Teardown old mode
    if (this.mode === 'ORBIT') {
      this.orbit.enabled = false;
    }
    
    this.mode = newMode;
    this.onMessage(`Camera Mode: ${newMode}`);
    
    // Setup new mode
    if (this.mode === 'ORBIT') {
      this.orbit.enabled = true;
    }
    else if (this.mode === 'WALK') {
      // Try to find ground
      const success = this._snapToGround();
      if (!success) {
        this.onMessage("Walk Mode is unavailable because a reliable walkable surface could not be established.");
        this.setMode('FLY');
      }
    }
    
    this.keys = {}; // reset keys on mode switch
    this.pointerDown = false;
  }
  
  // Expose virtual buttons for UI
  setJoystick(forward, right, up) {
    this.joystick.forward = forward;
    this.joystick.right = right;
    this.joystick.up = up;
  }

  _onKeyDown(e) {
    if (e.key === 'Escape') this.setMode('ORBIT');
    if (e.key.toLowerCase() === 'r') this.resetView();
    if (e.key.toLowerCase() === 'f') this.triggerFocus();
    
    this.keys[e.key.toLowerCase()] = true;
  }

  _onKeyUp(e) {
    this.keys[e.key.toLowerCase()] = false;
  }

  _onPointerDown(e) {
    if (this.mode !== 'FLY' && this.mode !== 'WALK') return;
    if (e.button !== 0) return;
    this.pointerDown = true;
    this.lastPointer = { x: e.clientX, y: e.clientY };
  }

  _onPointerMove(e) {
    if (!this.pointerDown) return;
    if (this.mode !== 'FLY' && this.mode !== 'WALK') return;
    
    const dx = e.clientX - this.lastPointer.x;
    const dy = e.clientY - this.lastPointer.y;
    this.lastPointer = { x: e.clientX, y: e.clientY };
    
    const sensitivity = 0.002;
    
    // Mouse look
    this.camera.rotation.order = 'YXZ';
    this.camera.rotation.y -= dx * sensitivity;
    this.camera.rotation.x -= dy * sensitivity;
    this.camera.rotation.x = Math.max(-Math.PI/2, Math.min(Math.PI/2, this.camera.rotation.x));
  }

  _onPointerUp(e) {
    this.pointerDown = false;
  }

  _onDoubleClick(e) {
    if (this.mode === 'FOCUS' || this.mode === 'ORBIT') {
      const rect = this.domElement.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObjects(this.getTargets(), true);
      
      if (intersects.length > 0) {
        const point = intersects[0].point;
        this.animateTo(point);
      } else {
        this.onMessage("No surface hit.");
      }
    }
  }
  
  triggerFocus() {
    this.raycaster.setFromCamera(new THREE.Vector2(0,0), this.camera);
    const intersects = this.raycaster.intersectObjects(this.getTargets(), true);
    if (intersects.length > 0) {
      this.animateTo(intersects[0].point);
    }
  }

  animateTo(targetPoint) {
    // Determine bounds to scale marker
    const targets = this.getTargets();
    if (!targets.length) return;
    
    // Move marker
    this.focusMarker.position.copy(targetPoint);
    if (!this.focusMarker.parent) {
      this.camera.parent?.add(this.focusMarker);
    }
    
    // In Orbit mode, move target. In others, just move camera towards it.
    if (this.mode === 'ORBIT') {
      this.orbit.target.copy(targetPoint);
      this.orbit.update();
    }
    
    // Zoom in slightly
    const dir = new THREE.Vector3().subVectors(targetPoint, this.camera.position);
    const dist = dir.length();
    if (dist > 5) {
      dir.normalize();
      this.camera.position.add(dir.multiplyScalar(dist * 0.5));
    }
    this.onMessage(`Focused at X:${targetPoint.x.toFixed(2)} Y:${targetPoint.y.toFixed(2)} Z:${targetPoint.z.toFixed(2)}`);
  }
  
  zoom(delta) { const dir = new THREE.Vector3().subVectors(this.orbit.target, this.camera.position); const dist = dir.length(); dir.normalize(); this.camera.position.add(dir.multiplyScalar(delta * dist * 0.2)); if (this.mode === 'ORBIT') this.orbit.update(); }
  resetView() {
    this.onMessage("Resetting view...");
    const targets = this.getTargets();
    if (targets.length === 0) return;
    
    const box = new THREE.Box3();
    targets.forEach(t => box.expandByObject(t));
    if (box.isEmpty()) return;
    
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    
    const maxDim = Math.max(size.x, size.y, size.z);
    this.baseSpeed = maxDim / 10.0; 
    this.eyeHeight = maxDim / 50.0;
    
    if (this.mode === 'ORBIT') {
      this.orbit.target.copy(center);
      this.camera.position.copy(center).add(new THREE.Vector3(0, maxDim, maxDim));
      this.orbit.update();
    }
  }
  
  _snapToGround() {
    // Cast ray down from current x,y
    this.raycaster.set(this.camera.position, new THREE.Vector3(0, 0, -1)); // assuming Z is up? Wait, Z is up in AeroRecon.
    // Let's check scene up
    const down = new THREE.Vector3(0, -1, 0);
    if (this.camera.up.z > 0.5) down.set(0, 0, -1);
    
    this.raycaster.set(this.camera.position.clone().addScaledVector(down, -1000), down);
    const intersects = this.raycaster.intersectObjects(this.getTargets(), true);
    if (intersects.length > 0) {
      const g = intersects[0].point;
      this.camera.position.copy(g).addScaledVector(down, -this.eyeHeight);
      return true;
    }
    return false;
  }

  update() {
    const dt = Math.min(this.clock.getDelta(), 0.1); // max 100ms
    
    if (this.mode === 'ORBIT') {
      this.orbit.update();
      return;
    }
    
    if (this.mode === 'FLY' || this.mode === 'WALK') {
      let fwd = 0;
      let right = 0;
      let up = 0;
      
      if (this.keys['w'] || this.keys['arrowup']) fwd += 1;
      if (this.keys['s'] || this.keys['arrowdown']) fwd -= 1;
      if (this.keys['d'] || this.keys['arrowright']) right += 1;
      if (this.keys['a'] || this.keys['arrowleft']) right -= 1;
      if (this.keys[' ']) up += 1;
      if (this.keys['shift']) up -= 1;
      
      fwd += this.joystick.forward;
      right += this.joystick.right;
      up += this.joystick.up;
      
      const speed = this.baseSpeed * this.speedMultiplier * dt;
      
      this.camera.getWorldDirection(this.cameraDirection);
      this.cameraRight.crossVectors(this.cameraDirection, this.camera.up).normalize();
      
      if (this.mode === 'WALK') {
        // Project movement onto horizontal plane (assume up is camera.up)
        this.cameraDirection.sub(this.camera.up.clone().multiplyScalar(this.cameraDirection.dot(this.camera.up))).normalize();
      }
      
      if (fwd !== 0) this.camera.position.addScaledVector(this.cameraDirection, fwd * speed);
      if (right !== 0) this.camera.position.addScaledVector(this.cameraRight, right * speed);
      
      if (this.mode === 'FLY') {
        if (up !== 0) this.camera.position.addScaledVector(this.camera.up, up * speed);
      } else if (this.mode === 'WALK') {
        // Snap to ground every frame
        const down = this.camera.up.clone().multiplyScalar(-1);
        this.raycaster.set(this.camera.position.clone().addScaledVector(this.camera.up, this.eyeHeight * 2), down);
        const intersects = this.raycaster.intersectObjects(this.getTargets(), true);
        if (intersects.length > 0) {
          const g = intersects[0].point;
          this.camera.position.copy(g).addScaledVector(this.camera.up, this.eyeHeight);
        }
      }
    }
  }

  dispose() {
    window.removeEventListener('keydown', this._onKeyDown);
    window.removeEventListener('keyup', this._onKeyUp);
    this.domElement.removeEventListener('pointerdown', this._onPointerDown);
    this.domElement.removeEventListener('pointermove', this._onPointerMove);
    window.removeEventListener('pointerup', this._onPointerUp);
    this.domElement.removeEventListener('dblclick', this._onDoubleClick);
    if (this.focusMarker.parent) this.focusMarker.parent.remove(this.focusMarker);
    this.focusMarker.geometry.dispose();
    this.focusMarker.material.dispose();
  }
}


