import cv2, numpy as np

img = cv2.imread("demo/mars_hkairport01_quality/texture_atlas_final.png")
tile_size = 6
variances = []

for i in range(100):
    for j in range(100):
        y, x = i * tile_size, j * tile_size
        tile = img[y:y+tile_size, x:x+tile_size]
        # Calculate variance of pixels inside this 6x6 tile
        variances.append(np.var(tile))

mean_var = np.mean(variances)
print(f"Mean variance inside 6x6 tiles: {mean_var:.2f}")

img_corrupted = cv2.imread("demo/mars_hkairport01_quality/texture_atlas_preview.png")
var_corr = []
for i in range(100):
    for j in range(100):
        y, x = i * tile_size, j * tile_size
        tile = img_corrupted[y:y+tile_size, x:x+tile_size]
        var_corr.append(np.var(tile))

mean_var_corr = np.mean(var_corr)
print(f"Mean variance inside 6x6 tiles (corrupted): {mean_var_corr:.2f}")
