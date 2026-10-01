import argparse
import os
from pathlib import Path
from rosbags.highlevel import AnyReader

def extract_frames(bag_path, out_dir, topic="/left_camera/image/compressed", 
                   sample_fps=None, start_time=None, end_time=None, 
                   max_frames=None, output_size=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with AnyReader([Path(bag_path)]) as reader:
        count = 0
        last_t = -1
        
        for conn, timestamp, rawdata in reader.messages():
            if conn.topic != topic:
                continue
                
            t_sec = timestamp / 1e9
            
            if start_time and t_sec < start_time: continue
            if end_time and t_sec > end_time: break
            
            if sample_fps:
                if last_t > 0 and (t_sec - last_t) < (1.0 / sample_fps):
                    continue
                    
            msg = reader.deserialize(rawdata, conn.msgtype)
            
            if output_size is None:
                with open(out_dir / f"frame_{count:05d}.jpg", "wb") as f:
                    f.write(msg.data)
            else:
                import cv2
                import numpy as np
                img = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
                img = cv2.resize(img, output_size)
                cv2.imwrite(str(out_dir / f"frame_{count:05d}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
                
            last_t = t_sec
            count += 1
            if max_frames and count >= max_frames:
                break
                
    print(f"Extracted {count} frames.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bag", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--topic", default="/left_camera/image/compressed")
    parser.add_argument("--sample-fps", type=float)
    parser.add_argument("--start-time", type=float)
    parser.add_argument("--end-time", type=float)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--output-size", type=str, help="WIDTHxHEIGHT")
    args = parser.parse_args()
    
    size = None
    if args.output_size:
        w, h = map(int, args.output_size.split("x"))
        size = (w, h)
        
    extract_frames(args.bag, args.out, args.topic, 
                   args.sample_fps, args.start_time, args.end_time, 
                   args.max_frames, size)
