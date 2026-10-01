with open('app/pipeline/dense_backend.py', 'r') as f:
    lines = f.readlines()

with open('app/pipeline/dense_backend.py', 'w') as f:
    for line in lines:
        if 'progress(45,' in line and 'cmd_undistort = [' in line:
            line = line.replace(')                cmd_undistort', ')\n                cmd_undistort')
        if '(stereo_dir / "patch-match.cfg").write_text' in line:
            line = '                        (stereo_dir / "patch-match.cfg").write_text("\\n".join(cfg_lines))\n'
        f.write(line)
