code = open('frontend/src/components/viewer/AeroReconViewer.jsx', encoding='utf-8').read()
idx = code.find('return')
print(code[idx:idx+500])
