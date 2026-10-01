import assert from 'assert';
import { triangleArea, surfaceArea3D } from './web/measurements.js';

const t1 = [
    {x: 0, y: 0, z: 0},
    {x: 3, y: 0, z: 0},
    {x: 0, y: 4, z: 0}
];
const t2 = [
    {x: 0, y: 0, z: 0},
    {x: 2, y: 0, z: 0},
    {x: 0, y: 2, z: 0}
];
const t3 = [
    {x: 2, y: 0, z: 0},
    {x: 2, y: 2, z: 0},
    {x: 0, y: 2, z: 0}
];

const sa1 = surfaceArea3D([t1]);
const sa2 = surfaceArea3D([t2, t3]);
assert.strictEqual(sa1, 6);
assert.strictEqual(sa2, 4);
console.log('Surface area tests passed');
