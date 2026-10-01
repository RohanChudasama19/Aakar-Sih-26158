code = open('app/main.py', encoding='utf-8').read()
idx = code.find('va_report = json.loads')
print(code[idx-500:idx+1500])
