code = open('app/main.py', encoding='utf-8').read()
idx = code.find('def artifact(jid: str, filename: str):')
print(code[idx:idx+300])
