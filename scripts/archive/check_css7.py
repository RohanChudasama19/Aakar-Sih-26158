code = open('frontend/src/pages/Workspace.module.css', encoding='utf-8').read()
import re
print(re.findall(r'\.([a-zA-Z0-9_-]+)', code))
