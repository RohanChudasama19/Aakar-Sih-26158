import cv2, numpy as np

img = cv2.imread('demo/mars_hkairport01_quality/texture_atlas_fixed.png')
print("Fixed atlas shape:", img.shape)
vars = []
for i in range(100):
    for j in range(100):
        tile = img[i*6:i*6+6, j*6:j*6+6, 1]
        vars.append(np.var(tile))
print("Fixed atlas mean variance:", np.mean(vars))
print("Max variance:", np.max(vars))
