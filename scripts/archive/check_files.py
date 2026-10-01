code = open('app/main.py', encoding='utf-8').read()
idx = code.find('def files(jid: str):')
print(code[idx:idx+300])
