import * as THREE from 'three';
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js';

const plyData = ply
format ascii 1.0
element vertex 4
property float x
property float y
property float z
element face 2
property list uchar int vertex_indices
property uchar red
property uchar green
property uchar blue
end_header
0 0 0
1 0 0
0 1 0
1 1 0
3 0 1 2 255 0 0
3 1 3 2 0 255 0
;

const loader = new PLYLoader();
const geo = loader.parse(plyData);
console.log('Index:', geo.index !== null);
if (geo.index) console.log('Index count:', geo.index.count);
console.log('Position count:', geo.attributes.position.count);
console.log('Color count:', geo.attributes.color ? geo.attributes.color.count : 'None');
