images = [f'{i*15:06d}.png' for i in range(105)]
with open('list.txt', 'w') as f:
    f.write('\n'.join(images))
