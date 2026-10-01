code = open('frontend/src/viewer/viewer.js', encoding='utf-8').read()
idx = code.find('export async function createViewer')
print(code[idx:idx+500])
