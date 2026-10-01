code = open('frontend/src/pages/Workspace.jsx', encoding='utf-8').read()
idx = code.find('viewportOverlay')
print(code[max(0,idx-100):idx+500])
