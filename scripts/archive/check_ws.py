code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()
idx = code.find('Cameras Registered')
print(code[max(0,idx-200):idx+500])
