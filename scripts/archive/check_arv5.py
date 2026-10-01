code = open('frontend/src/components/viewer/AAKARViewer.jsx', encoding='utf-8').read()
idx = code.rfind('return')
print(code[idx:idx+500])
