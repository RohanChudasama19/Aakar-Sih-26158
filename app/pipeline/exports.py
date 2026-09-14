import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
import trimesh
import laspy
import rasterio
from rasterio.transform import from_origin
from pyproj import CRS
from .georef import transform


def export_all(mesh,points,colors,geo,out):
    out.mkdir(parents=True,exist_ok=True)
    local=transform(points,geo)
    trimesh.points.PointCloud(local,colors=colors).export(out/'cloud.ply')
    mesh.export(out/'model.glb')
    gltf=trimesh.exchange.gltf.export_gltf(mesh)
    for name,content in gltf.items():
        (out/name).write_bytes(content)
    mesh.export(out/'model.obj')
    manifest={x:'available' for x in ['PLY','OBJ','GLB','glTF']}
    if geo['valid']:
        absolute=local+geo['origin']
        header=laspy.LasHeader(point_format=3,version='1.2'); header.scales=np.array([.001,.001,.001]); header.offsets=np.min(absolute,axis=0)
        header.add_crs(CRS.from_epsg(geo['epsg']))
        las=laspy.LasData(header); las.x,las.y,las.z=absolute.T
        las.red,las.green,las.blue=(colors.astype(np.uint16)*257).T; las.write(out/'cloud.las')
        manifest['LAS']='available'
        manifest['GeoTIFF']=rasterize(absolute,colors,geo['epsg'],out)
    else:
        manifest['LAS']='unavailable: absolute coordinates unresolved'
        manifest['GeoTIFF']='unavailable: absolute coordinates unresolved'
    blender=shutil.which('blender')
    if blender:
        script=Path(__file__).resolve().parents[2]/'scripts'/'export_fbx.py'
        try:
            subprocess.run([blender,'--background','--python',str(script),'--',str(out/'model.glb'),str(out/'model.fbx')],check=True,timeout=180,capture_output=True)
            manifest['FBX']='available'
        except (subprocess.SubprocessError,OSError) as e:
            manifest['FBX']='unavailable: Blender conversion failed'
            (out/'fbx-error.txt').write_text(str(e))
    else:
        manifest['FBX']='unavailable: install Blender (included in Docker image)'
    reference={'crs':f'EPSG:{geo["epsg"]}' if geo['valid'] else None,'origin_utm_m':geo['origin'].tolist() if geo['valid'] else None,'mesh_axes':'X east, Y north, Z up' if geo['valid'] else 'relative SfM coordinates','mesh_units':'metres' if geo['valid'] else 'relative units','las_geotiff_coordinates':'absolute UTM' if geo['valid'] else None,'vertical_datum':'Input altitude datum; no geoid conversion performed','accuracy_verified':False}
    (out/'georeference.json').write_text(json.dumps(reference,indent=2))
    (out/'exports.json').write_text(json.dumps(manifest,indent=2))
    return manifest


def rasterize(points,colors,epsg,out):
    minimum=points.min(0); maximum=points.max(0)
    resolution=max(np.max(maximum[:2]-minimum[:2])/512,.05)
    width,height=np.ceil((maximum[:2]-minimum[:2])/resolution).astype(int)+1
    x=np.clip(((points[:,0]-minimum[0])/resolution).astype(int),0,width-1)
    y=np.clip(((maximum[1]-points[:,1])/resolution).astype(int),0,height-1)
    dsm=np.full((height,width),-9999.,np.float32); ortho=np.zeros((3,height,width),np.uint8)
    for i in np.argsort(points[:,2]):
        dsm[y[i],x[i]]=points[i,2]; ortho[:,y[i],x[i]]=colors[i]
    profile={'driver':'GTiff','width':int(width),'height':int(height),'crs':f'EPSG:{epsg}','transform':from_origin(minimum[0],maximum[1],resolution,resolution),'compress':'deflate'}
    with rasterio.open(out/'dsm.tif','w',**profile,count=1,dtype='float32',nodata=-9999.) as f:
        f.write(dsm,1); f.update_tags(description='Observed surface raster (DSM), NOT bare-earth DEM; holes remain nodata')
    with rasterio.open(out/'ortho.tif','w',**profile,count=3,dtype='uint8') as f:
        f.write(ortho); f.write_mask((dsm!=-9999).astype(np.uint8)*255); f.update_tags(description='Point-projected RGB ortho raster, sparse cells retain invalid mask')
    return 'available: observed DSM and point-projected RGB ortho; no bare-earth DEM'
