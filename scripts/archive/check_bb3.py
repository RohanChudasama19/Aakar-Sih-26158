code = open('frontend/src/viewer/viewer.js', encoding='utf-8').read()
idx = code.find('Box3')
if idx == -1: idx = code.find('computeBoundingBox')
print(code[max(0,idx-200):idx+500].encode('ascii', 'ignore').decode('ascii'))
