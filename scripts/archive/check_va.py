import ast
code = open('app/main.py', encoding='utf-8').read()
idx = code.find('va_path = out / "viewer_artifacts.json"')
print(code[max(0,idx-300):idx+500])
