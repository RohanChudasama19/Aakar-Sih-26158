code = open('app/main.py', encoding='utf-8').read()
idx = code.find('def representations(jid:')
print(code[max(0,idx-200):idx+300])
