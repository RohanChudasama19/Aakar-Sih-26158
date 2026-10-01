code = open('app/main.py', encoding='utf-8').read()
import re
endpoints = re.findall(r'@app\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]', code)
for method, path in endpoints:
    print(f"{method.upper()} {path}")
