import cv2
import time
from pathlib import Path
import numpy as np

video_path = r'colorado_dataset\video.mp4'
cap = cv2.VideoCapture(video_path)
count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
limit = 180
min_gap = max(1, int(count / (limit * 5)))

start = time.time()
i = 0
decoded = 0
retained = 0
orb = cv2.ORB_create(nfeatures=500)

while True:
    if i % min_gap != 0:
        ok = cap.grab()
        if not ok: break
    else:
        ok, frame = cap.read()
        if not ok: break
        decoded += 1
        scale = min(1.0, 960.0 / frame.shape[1])
        gray = cv2.cvtColor(cv2.resize(frame, None, fx=scale, fy=scale), cv2.COLOR_BGR2GRAY)
        
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
        kps = orb.detect(gray, None)
        
        if sharpness > 40:
            retained += 1
            if retained % 20 == 0:
                print(f"Retained {retained}/180, Time: {time.time() - start:.1f}s")
            if retained >= limit:
                break
    i += 1

elapsed = time.time() - start
print(f'Combined pass took {elapsed:.1f} sec')
print(f'Decoded: {decoded}, Retained: {retained}')
