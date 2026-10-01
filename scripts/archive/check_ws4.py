code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()
import re
# Find all occurrences of mission.report or mission.
matches = re.findall(r'mission\.[a-zA-Z0-9_\.\?]+', code)
print(sorted(set(matches)))
