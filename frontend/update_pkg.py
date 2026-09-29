import json
with open('package.json', 'r', encoding='utf-8') as f:
    pkg = json.load(f)
pkg['scripts']['test'] = 'vitest run'
with open('package.json', 'w', encoding='utf-8') as f:
    json.dump(pkg, f, indent=2)
