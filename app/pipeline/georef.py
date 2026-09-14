import csv
import numpy as np
from pyproj import CRS, Transformer


def similarity(a,b):
    ac,bc=a-a.mean(0),b-b.mean(0)
    u,d,vt=np.linalg.svd(bc.T@ac/len(a))
    sign=np.ones(3); sign[-1]=np.sign(np.linalg.det(u@vt))
    r=u@np.diag(sign)@vt
    scale=np.sum(d*sign)/np.mean(np.sum(ac*ac,axis=1))
    t=b.mean(0)-scale*r@a.mean(0)
    return scale,r,t


def align(sfm, info, gps, input_dir):
    lat,lon=gps[0]['latitude'],gps[0]['longitude']
    zone=min(60,max(1,int((lon+180)//6)+1))
    epsg=(32600 if lat>=0 else 32700)+zone
    tx=Transformer.from_crs(4326,epsg,always_xy=True)
    e,n=tx.transform([x['longitude'] for x in gps],[x['latitude'] for x in gps])
    absolute=np.c_[e,n,[x['altitude_m'] for x in gps]]
    correction=input_dir/'rtk.csv'
    rtk_used=False
    if correction.exists():
        with correction.open() as f:
            rows=list(csv.DictReader(f))
        x=np.array([[float(r[k]) for k in ('frame','east_correction_m','north_correction_m','up_correction_m')] for r in rows])
        if len(x)<2 or not np.isfinite(x).all() or np.any(np.diff(x[:,0])<=0):
            raise ValueError('RTK corrections need >=2 ordered finite samples')
        if x[0,0]>gps[0]['frame'] or x[-1,0]<gps[-1]['frame']:
            raise ValueError('RTK corrections must cover the complete GPS frame range')
        for d in range(3):
            absolute[:,d]+=np.interp([r['frame'] for r in gps],x[:,0],x[:,d+1])
        rtk_used=True
    baro=input_dir/'barometer.csv'
    if baro.exists():
        with baro.open() as f:
            rows=list(csv.DictReader(f))
        x=np.array([[float(r['frame']),float(r['altitude_m'])] for r in rows])
        if len(x)<2 or not np.isfinite(x).all() or np.any(np.diff(x[:,0])<=0):
            raise ValueError('Barometer requires ordered frame,altitude_m samples')
        if x[0,0]>gps[0]['frame'] or x[-1,0]<gps[-1]['frame']:
            raise ValueError('Barometer samples must cover the complete GPS frame range')
        absolute[:,2]=np.interp([r['frame'] for r in gps],x[:,0],x[:,1])
    ids=sorted(sfm['poses'])
    frame_ids=[info['frames'][i]['frame'] for i in ids]
    if min(frame_ids)<gps[0]['frame'] or max(frame_ids)>gps[-1]['frame']:
        raise ValueError('GPS telemetry must cover all selected video frames; extrapolation is disabled')
    targets=np.array([np.interp(frame_ids,[r['frame'] for r in gps],absolute[:,d]) for d in range(3)]).T
    origin=absolute[0].copy()
    target=targets-origin
    centers=np.array([-sfm['poses'][j][:,:3].T@sfm['poses'][j][:,3] for j in ids])
    # A collinear GPS path leaves rotation about the flight axis unobservable.
    eig=np.linalg.svd(target-target.mean(0),compute_uv=False)
    if eig[0]<.5 or eig[1]/eig[0]<.015:
        return {'valid':False,'reason':'GPS trajectory is stationary or nearly collinear; absolute orientation is underconstrained. Relative model only. Add a curved path or independently surveyed orientation.','scale':1.,'rotation':np.eye(3),'translation':np.zeros(3),'origin':origin,'epsg':epsg,'rmse_m':None,'rtk_used':rtk_used}
    best=None
    rng=np.random.default_rng(42)
    for _ in range(100):
        idx=rng.choice(len(centers),min(4,len(centers)),replace=False)
        if np.linalg.matrix_rank(centers[idx]-centers[idx].mean(0),tol=1e-5)<2:
            continue
        s,r,t=similarity(centers[idx],target[idx])
        residual=np.linalg.norm(s*centers@r.T+t-target,axis=1)
        good=residual<max(2.,float(np.median(residual))*2)
        score=(int(good.sum()),-float(np.median(residual)))
        if best is None or score>best[0]:
            best=score,good
    if best is None or best[1].sum()<3:
        raise ValueError('Cannot determine robust visual-to-GPS alignment')
    s,r,t=similarity(centers[best[1]],target[best[1]])
    residual=np.linalg.norm(s*centers@r.T+t-target,axis=1)
    return {'valid':True,'scale':float(s),'rotation':r,'translation':t,'origin':origin,'epsg':epsg,'rmse_m':float(np.sqrt(np.mean(residual**2))),'gps_residuals_m':residual.tolist(),'rtk_used':rtk_used,'barometer_used':baro.exists(),'alignment_inliers':int(best[1].sum())}


def transform(points,geo):
    return geo['scale']*points@geo['rotation'].T+geo['translation']
