import cv2
cap = cv2.VideoCapture("colorado_dataset/video.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
duration = frames / fps if fps > 0 else 0
print(f"Duration: {duration} seconds ( {duration/60:.2f} minutes )")
print(f"FPS: {fps}")
print(f"Frames: {frames}")
print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
