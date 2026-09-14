import json
import shutil
import zipfile
from pathlib import Path
import numpy as np
import trimesh
import laspy
import rasterio
from app.pipeline.runner import run_pipeline
ROOT=Path(__file__).resolve().parents[1]

def test_real_cpu_pipeline_all_stages_and_export_roundtrips(tmp_path):
    inputs=tmp_path/'inputs';inputs.mkdir()
    for src,dst in [('sample.mp4','video.mp4'),('gps.csv','gps.csv'),('flight.json','flight.json')]: shutil.copy(ROOT/'samples'/src,inputs/dst)
    events=[]
    report=run_pipeline(inputs,tmp_path/'work',{'max_frames':60,'max_width':640},lambda s,p,m:events.append((s,p)))
    out=tmp_path/'work/outputs'
    assert {s for s,p in events}==set('ABCDEF')
    assert events[-1]==('F',100)
    assert all(report['stages'][s]['status']=='completed' for s in 'ABCDEF')
    assert report['targets']['coverage']['registered_frames']>=8
    assert report['metric_state']=='GPS_ALIGNED_UNVERIFIED'
    assert report['targets']['spatial_accuracy']['passed'] is None
    assert report['targets']['processing_time']['ten_minute_benchmark_passed'] is None
    assert report['mesh']['faces']>100
    scene=trimesh.load(out/'model.glb'); assert len(scene.geometry)>0
    cloud=trimesh.load(out/'cloud.ply'); assert len(cloud.vertices)>100
    las=laspy.read(out/'cloud.las'); assert len(las.points)==len(cloud.vertices)
    assert las.header.parse_crs().to_epsg()==report['alignment']['epsg']
    with rasterio.open(out/'dsm.tif') as src:
        assert src.crs.to_epsg()==report['alignment']['epsg']
        assert np.count_nonzero(src.read(1)!=src.nodata)>100
    labels=np.load(out/'semantic_labels.npz'); assert len(labels['points'])==len(cloud.vertices)
    assert labels['labels'].max()<=4
    with zipfile.ZipFile(tmp_path/'work/artifacts.zip') as z:
        assert {'model.glb','model.obj','cloud.ply','report.json','dsm.tif','cloud.las'}<=set(z.namelist())
    assert all((out/f).stat().st_size>0 for f in ['model.glb','model.obj','cloud.ply','report.json'])
