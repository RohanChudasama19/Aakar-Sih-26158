const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
pkg.scripts.test = 'vitest run';
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
