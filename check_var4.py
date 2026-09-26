import cv2, numpy as np

img = cv2.imread('demo/mars_hkairport01_quality/texture_atlas_final.png')
print("Image shape:", img.shape)

max_var = 0
best_tile = None
for i in range(200):
    for j in range(200):
        tile = img[i*6:i*6+6, j*6:j*6+6, 1]
        v = np.var(tile)
        if v > max_var:
            max_var = v
            best_tile = tile

print("Max variance:", max_var)
if best_tile is not None:
    print(best_tile)
