import cv2, numpy as np

def spatial_var(img_path):
    img = cv2.imread(img_path)
    tile_size = 6
    vars = []
    for i in range(100):
        for j in range(100):
            y, x = i * tile_size, j * tile_size
            tile = img[y:y+tile_size, x:x+tile_size]
            # Spatial variance of the Green channel
            vars.append(np.var(tile[:,:,1]))
    return np.mean(vars)

print(f"Final atlas spatial variance (Green): {spatial_var('demo/mars_hkairport01_quality/texture_atlas_final.png'):.2f}")
print(f"Corrupt atlas spatial variance (Green): {spatial_var('demo/mars_hkairport01_quality/texture_atlas_preview.png'):.2f}")
