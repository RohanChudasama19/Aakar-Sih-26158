code = open('app/main.py', encoding='utf-8').read()
import re
match = re.search(r'@app\.post\([\'"]/api/jobs[\'"]\).*?def submit_job.*?:\n(?: {4}.*\n)*', code, re.MULTILINE)
if match:
    print(match.group(0))
