code = open('frontend/src/pages/Workspace.module.css', encoding='utf-8').read()
idx = code.find('.modeBtn')
print(code[max(0,idx-200):idx+500])
