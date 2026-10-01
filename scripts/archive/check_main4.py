code = open('app/main.py', encoding='utf-8').read()
idx = code.find('file_info("mesh/model.glb")')
print(code[idx:idx+1500])
