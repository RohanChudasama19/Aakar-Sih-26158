code = open('frontend/src/pages/Workspace.module.css', encoding='utf-8').read()
idx = code.find('.workspaceArea')
print(code[max(0,idx-100):idx+300])
