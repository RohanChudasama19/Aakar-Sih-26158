import numpy as np
tile = 6
aa, bb = np.meshgrid(np.linspace(0, 1, tile), np.linspace(0, 1, tile))
b = np.minimum(bb, 1 - aa)

# Suppose a triangle projects to image pixels: (100, 100), (120, 100), (110, 120)
tri = np.array([[100, 100], [120, 100], [110, 120]])
uv = tri[0] + aa[:, :, None] * (tri[1] - tri[0]) + b[:, :, None] * (tri[2] - tri[0])

print(uv.shape)
print("uv X channel:")
print(np.round(uv[:,:,0],1))
print("uv Y channel:")
print(np.round(uv[:,:,1],1))
