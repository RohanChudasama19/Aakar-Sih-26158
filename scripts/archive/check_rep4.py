code = open('app/main.py', encoding='utf-8').read()
idx = code.find('def get_job_representations')
print(code[idx:idx+300])
