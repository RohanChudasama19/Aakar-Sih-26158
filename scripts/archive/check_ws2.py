code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()
idx = code.find('Dense Points')
print(code[max(0,idx-100):idx+500])
