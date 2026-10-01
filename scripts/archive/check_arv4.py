code = open('frontend/src/components/viewer/AAKARViewer.jsx', encoding='utf-8').read()
idx = code.find('return')
print(code[idx:idx+500])
