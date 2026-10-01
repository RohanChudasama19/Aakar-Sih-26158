import subprocess
out = subprocess.check_output(['git', 'show', '6fd045e:app/main.py'], text=True)
idx = out.find('def get_job')
print(out[idx:idx+800])
