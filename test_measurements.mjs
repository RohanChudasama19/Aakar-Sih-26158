import assert from 'assert';
import { 
    distance3D, horizontalDistance, verticalDifference, deltaXYZ, 
    slope, angle3, planarArea3D, triangleArea 
} from './web/measurements.js';

// Distance
const p1 = {x: 0, y: 0, z: 0};
const p2 = {x: 3, y: 4, z: 0};
assert.strictEqual(distance3D(p1, p2), 5);
assert.strictEqual(horizontalDistance(p1, p2), 5);
assert.strictEqual(verticalDifference(p1, p2), 0);

const p3 = {x: 3, y: 4, z: 12};
assert.strictEqual(distance3D(p1, p3), 13);
assert.strictEqual(horizontalDistance(p1, p3), 5);
assert.strictEqual(verticalDifference(p1, p3), 12);

// XYZ Delta
const delta = deltaXYZ(p1, p3);
assert.deepStrictEqual(delta, {x: 3, y: 4, z: 12});

// Slope
const p4 = {x: 10, y: 0, z: 10};
const sl = slope(p1, p4);
assert.strictEqual(sl.horizontal, 10);
assert.strictEqual(sl.vertical, 10);
assert.strictEqual(sl.degrees, 45);
assert.strictEqual(sl.percentage, 100);

// Angle
const a = {x: 1, y: 0, z: 0};
const b = {x: 0, y: 0, z: 0};
const c = {x: 0, y: 1, z: 0};
assert.strictEqual(angle3(a, b, c), 90);

// Area
const sq = [
    {x: 0, y: 0, z: 0},
    {x: 2, y: 0, z: 0},
    {x: 2, y: 2, z: 0},
    {x: 0, y: 2, z: 0}
];
assert.strictEqual(planarArea3D(sq), 4);
assert.strictEqual(triangleArea(sq[0], sq[1], sq[2]), 2);

console.log('All measurement math tests passed!');
