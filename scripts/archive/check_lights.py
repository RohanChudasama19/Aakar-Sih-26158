code = open('frontend/src/viewer/viewer.js', encoding='utf-8').read()
idx = code.find('// Lights')
print(code[max(0,idx-200):idx+500])
