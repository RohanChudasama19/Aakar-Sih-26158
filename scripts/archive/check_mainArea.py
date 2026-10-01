code = open('frontend/src/pages/Workspace.module.css', encoding='utf-8').read()
idx = code.find('.mainArea')
print(code[idx:idx+300])
