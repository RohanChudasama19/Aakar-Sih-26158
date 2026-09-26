import cv2, numpy as np
# load the first MARS image
img = cv2.imread('data/mars_hkairport01_quality/work/dense_mars/tex_images/000001.png')
if img is None:
    print("No image 000001.png")
    # try frame_000001.jpg
    import glob
    files = glob.glob('data/mars_hkairport01_quality/work/dense_mars/tex_images/*.png')
    if files:
        img = cv2.imread(files[0])

if img is not None:
    tile = 6
    aa, bb = np.meshgrid(np.linspace(0, 1, tile), np.linspace(0, 1, tile))
    b = np.minimum(bb, 1 - aa)
    tri = np.array([[100, 100], [200, 100], [150, 200]]) # A large triangle
    uv = tri[0] + aa[:, :, None] * (tri[1] - tri[0]) + b[:, :, None] * (tri[2] - tri[0])
    
    sampled = cv2.remap(
        img,
        uv[:, :, 0].astype(np.float32),
        uv[:, :, 1].astype(np.float32),
        cv2.INTER_LINEAR,
    )
    print("Sampled shape:", sampled.shape)
    print("Sampled variance:", np.var(sampled[:,:,1]))
    print(sampled[:,:,1])
