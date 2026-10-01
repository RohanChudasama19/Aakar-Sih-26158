code = open('app/main.py', encoding='utf-8').read().splitlines()
for i in range(200, 215):
    print(f"{i}: {code[i]}")
