import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

export async function createViewer(container,buffer,metric){
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(container.clientWidth,container.clientHeight);container.append(renderer.domElement);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#121b17');
 const camera=new THREE.PerspectiveCamera(45,container.clientWidth/container.clientHeight,.001,100000);camera.up.set(0,0,1);
 const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
 scene.add(new THREE.HemisphereLight(0xffffff,0x627361,2.4));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(20,-20,50);scene.add(light);
 const data=await new GLTFLoader().parseAsync(buffer,'');const model=data.scene;scene.add(model);
 model.traverse(o=>{if(o.isMesh){o.material.side=THREE.DoubleSide;o.material.color?.set(0xffffff);o.material.metalness=0;o.material.roughness=1;}});
 const box=new THREE.Box3().setFromObject(model),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()).length();
 controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(size*.48,-size*.58,size*.5));camera.near=Math.max(size/10000,.001);camera.far=Math.max(size*100,100);camera.updateProjectionMatrix();controls.update();
 const grid=new THREE.GridHelper(size*1.5,20,0x44603f,0x263c2d);grid.rotation.x=Math.PI/2;grid.position.set(center.x,center.y,box.min.z-size*.015);scene.add(grid);
 const annotations=new THREE.Group();scene.add(annotations);const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();let mode='orbit',points=[],line=null,disposed=false,start=null;
 const label=document.querySelector('#measurement');
 function clear(){for(const o of [...annotations.children]){annotations.remove(o);o.geometry?.dispose();o.material?.dispose();}points=[];line=null;label.textContent='Select points on the model';}
 function draw(){if(line){annotations.remove(line);line.geometry.dispose();line.material.dispose();}const path=mode==='area'&&points.length>2?[...points,points[0]]:points;line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(path),new THREE.LineBasicMaterial({color:0xc6ff8e,depthTest:false}));line.renderOrder=10;annotations.add(line);if(mode==='distance'){let d=0;for(let i=1;i<points.length;i++)d+=points[i].distanceTo(points[i-1]);label.textContent=`Path: ${d.toFixed(3)} ${metric?'m':'relative units'} · ${points.length} points`;}else{let normal=new THREE.Vector3();const origin=points[0];for(let i=0;i<points.length;i++)normal.add(new THREE.Vector3().crossVectors(points[i].clone().sub(origin),points[(i+1)%points.length].clone().sub(origin)));label.textContent=`Planar area: ${(normal.length()/2).toFixed(3)} ${metric?'m²':'relative units²'} · ${points.length} points`;}}
 renderer.domElement.addEventListener('pointerdown',e=>{start=[e.clientX,e.clientY];});
 renderer.domElement.addEventListener('pointerup',e=>{if(mode==='orbit'||!start||Math.hypot(e.clientX-start[0],e.clientY-start[1])>5||e.button!==0)return;const rect=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObject(model,true)[0];if(!hit)return;points.push(hit.point.clone());const marker=new THREE.Mesh(new THREE.SphereGeometry(size/280,12,8),new THREE.MeshBasicMaterial({color:0xc6ff8e,depthTest:false}));marker.position.copy(hit.point);marker.renderOrder=11;annotations.add(marker);draw();});
 const observer=new ResizeObserver(()=>{if(disposed)return;renderer.setSize(container.clientWidth,container.clientHeight);camera.aspect=container.clientWidth/container.clientHeight;camera.updateProjectionMatrix();});observer.observe(container);
 renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
 return {setMode(v){mode=v;clear();label.textContent=v==='orbit'?'Drag to explore':v==='area'?'Select polygon corners in order on one plane':'Select points to measure a path';},clear,wireframe(state){model.traverse(o=>{if(o.isMesh)o.material.wireframe=state!==undefined?state:!o.material.wireframe;});},dispose(){disposed=true;observer.disconnect();renderer.setAnimationLoop(null);controls.dispose();scene.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material]){m.map?.dispose();m.dispose();}}});renderer.dispose();renderer.domElement.remove();}};
}
