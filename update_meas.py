import re
from pathlib import Path

p = Path("web/measurements.js")
js = p.read_text(encoding="utf-8")

new_funcs = '''
export function surfaceArea3D(triangles) {
    let total = 0;
    for (let i = 0; i < triangles.length; i++) {
        total += triangleArea(triangles[i][0], triangles[i][1], triangles[i][2]);
    }
    return total;
}
'''

if "surfaceArea3D" not in js:
    js += new_funcs
    p.write_text(js, encoding="utf-8")
