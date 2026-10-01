code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()
idx = code.find('tools')
print(code[idx:idx+300])
