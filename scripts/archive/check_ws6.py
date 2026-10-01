code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()
import re
print(re.findall(r'styles\.([a-zA-Z0-9_-]+)', code))
