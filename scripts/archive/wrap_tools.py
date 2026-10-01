code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()

import re
code = re.sub(
    r'(<div className=\{styles\.tools\}>)',
    r'<div className={styles.viewportOverlay}>\n            \1',
    code
)

code = re.sub(
    r'(<button className=\{styles\.toolBtn\} onClick=\{.*?\).*?</button>\n\s*</div>)',
    r'\1\n          </div>',
    code
)

with open('frontend/src/pages/Workspace.jsx', 'w', encoding='utf-8') as f:
    f.write(code)
print("Wrapped tools in viewportOverlay")
