code = open('frontend/src/viewer/viewer.js', encoding='utf-8').read()
idx = code.find('async function loadMesh')
print(code[idx:idx+1000].encode('ascii', 'ignore').decode('ascii'))
