code = open('frontend/package.json', encoding='utf-8').read()
import json
pkg = json.loads(code)
print(pkg.get('scripts', {}))
