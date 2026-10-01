code = open('frontend/src/viewer/viewer.js', encoding='utf-8').read()
idx = code.find('resize')
print(code[max(0,idx-100):idx+200].encode('ascii', 'ignore').decode('ascii'))
