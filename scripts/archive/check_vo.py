code = open('frontend/src/pages/Workspace.module.css', encoding='utf-8').read()
idx = code.find('.viewportOverlay')
print(code[max(0,idx-50):idx+300])
