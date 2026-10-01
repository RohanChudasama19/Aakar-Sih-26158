import cv2, numpy as np

img = cv2.imread('demo/mars_hkairport01_quality/texture_atlas_final.png')
print(np.max(np.var(img[:60,:60,1].reshape(10,6,10,6), axis=(1,3))))
