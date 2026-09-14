"""Deterministic textured scene rendered from known perspective cameras.
The generated GPS is synthetic truth, NOT a real flight or accuracy benchmark.
"""
import csv
import json
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
import cv2
import numpy as np
from pyproj import Transformer


def generate(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(26158)
    w,h,fps,count=640,480,10,60
    k=np.array([[550.,0,w/2],[0,550.,h/2],[0,0,1]])
    def texture(base):
        t=np.full((512,512,3),base,np.uint8)
        for _ in range(2000):
            x,y=rng.integers(0,512,2); c=rng.integers(30,235,3).tolist()
            cv2.circle(t,(int(x),int(y)),int(rng.integers(1,6)),c,-1)
        return t
    ground=texture((98,119,123)); roof=texture((130,143,153)); wall=texture((120,140,170))
    surfaces=[(np.array([[-16,-14,0],[16,-14,0],[16,14,0],[-16,14,0]],float),ground)]
    for x,y,sx,sy,z in [(-4,0,3,4,3),(3,2,4,3,4),(0,-5,3,2,1.5)]:
        a,b,c,d=np.array([[x,y,0],[x+sx,y,0],[x+sx,y+sy,0],[x,y+sy,0]],float)
        up=np.array([0,0,z])
        surfaces.extend([(np.array([a+up,b+up,c+up,d+up]),roof),(np.array([a,b,b+up,a+up]),wall),(np.array([b,c,c+up,b+up]),wall),(np.array([c,d,d+up,c+up]),wall),(np.array([d,a,a+up,d+up]),wall)])
    writer=cv2.VideoWriter(str(out/'sample.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h))
    if not writer.isOpened():
        raise RuntimeError('MP4 writer unavailable')
    tx=Transformer.from_crs(32643,4326,always_xy=True)
    origin=np.array([230000.,2540000.,50.])
    start=datetime(2026,1,1,tzinfo=timezone.utc)
    gps=[]; truth=[]
    source=np.float32([[0,0],[511,0],[511,511],[0,511]])
    for i in range(count):
        t=i/(count-1)
        cam=np.array([-5+10*t,-9+2*np.sin(t*np.pi),13+1.2*np.sin(2*t*np.pi)])
        # Camera moves through a curved, single-pass path and looks into the scene.
        forward=np.array([0.,0.,1.])-cam; forward/=np.linalg.norm(forward)
        right=np.cross(forward,np.array([0.,0.,1.])); right/=np.linalg.norm(right)
        down=np.cross(forward,right); r=np.array([right,down,forward])
        frame=np.full((h,w,3),(177,182,190),np.uint8)
        for verts,tex in sorted(surfaces,key=lambda s:np.linalg.norm(s[0].mean(0)-cam),reverse=True):
            camera=(verts-cam)@r.T
            if np.any(camera[:,2]<=0):
                continue
            pix=camera@k.T; dest=(pix[:,:2]/pix[:,2:3]).astype(np.float32)
            H=cv2.getPerspectiveTransform(source,dest)
            warped=cv2.warpPerspective(tex,H,(w,h))
            mask=cv2.warpPerspective(np.full((512,512),255,np.uint8),H,(w,h))
            frame[mask>0]=warped[mask>0]
        writer.write(frame)
        lon,lat=tx.transform(origin[0]+cam[0],origin[1]+cam[1])
        gps.append([(start+timedelta(seconds=i/fps)).isoformat().replace('+00:00','Z'),i,lat,lon,origin[2]+cam[2],90,-60,0,1.7,18])
        truth.append({'frame':i,'camera_enu':cam.tolist(),'rotation':r.tolist()})
    writer.release()
    with (out/'gps.csv').open('w',newline='') as file:
        wr=csv.writer(file); wr.writerow(['timestamp_utc','frame','latitude','longitude','altitude_m','compass_heading_deg','gimbal_pitch_deg','gimbal_yaw_deg','speed_mps','satellites']); wr.writerows(gps)
    lon,lat=tx.transform(origin[0],origin[1])
    meta={'mission_name':'Synthetic campus · smoke test','drone_model':'Synthetic perspective camera','camera_sensor':'Pinhole, zero distortion','video_file':'sample.mp4','video_resolution':[w,h],'video_fps':fps,'video_duration_sec':count/fps,'home_point':{'latitude':lat,'longitude':lon,'altitude_m':origin[2]},'start_time_utc':gps[0][0],'end_time_utc':(start+timedelta(seconds=count/fps)).isoformat(),'camera_intrinsics':{'focal_length_mm':5.5,'sensor_width_mm':6.4,'sensor_height_mm':4.8,'image_width_px':w,'image_height_px':h},'synthetic':True}
    (out/'flight.json').write_text(json.dumps(meta,indent=2))
    (out/'ground_truth.json').write_text(json.dumps({'note':'Synthetic camera truth only; not independently surveyed real-world checkpoints','origin_utm':origin.tolist(),'cameras':truth},indent=2))
    (out/'rtk-example.csv').write_text('frame,east_correction_m,north_correction_m,up_correction_m\n0,0,0,0\n59,0,0,0\n')
    (out/'barometer-example.csv').write_text('frame,altitude_m\n'+'\n'.join(f'{x[1]},{x[4]}' for x in gps)+'\n')
    print(out/'sample.mp4')

if __name__=='__main__':
    generate(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'samples')
