code = open('app/main.py', encoding='utf-8').read()
idx = code.find('dense_available = dense_display')
print(code[idx:idx+1500])
