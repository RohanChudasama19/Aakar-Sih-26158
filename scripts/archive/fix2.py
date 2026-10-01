import re

with open('app/pipeline/dense_backend.py', 'r') as f:
    content = f.read()

# Fix the broken line
pattern = r'\(stereo_dir / "patch-match.cfg"\).write_text\("\\n""\.join\(cfg_lines\)\)'
replacement = r'(stereo_dir / "patch-match.cfg").write_text("\\n".join(cfg_lines))'
content = re.sub(pattern, replacement, content)

# Check if there's any other broken line
pattern2 = r'\(stereo_dir / "patch-match\.cfg"\)\.write_text\("([^"]*)\\n([^"]*)"\.join\(cfg_lines\)\)'
content = re.sub(pattern2, replacement, content)

with open('app/pipeline/dense_backend.py', 'w') as f:
    f.write(content)
