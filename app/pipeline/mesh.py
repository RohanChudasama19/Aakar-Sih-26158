import cv2
import numpy as np
import trimesh
from scipy.spatial import Delaunay, cKDTree
from PIL import Image
from .georef import transform


def build_mesh(points, colors, geo, sfm, k, directory, max_vertices=10000):
    local=transform(points,geo)
    finite=np.isfinite(local).all(1)
    local,colors=local[finite],colors[finite]
    if len(local)>max_vertices:
        ids=np.linspace(0,len(local)-1,max_vertices).astype(int); local,colors=local[ids],colors[ids]
    center=np.median(local,axis=0)
    distances=np.linalg.norm(local-center,axis=1)
    keep=distances<np.percentile(distances,98)
    local,colors=local[keep],colors[keep]
    if geo['valid']:
        xy=local[:,:2]
    else:
        _,_,basis=np.linalg.svd(local-local.mean(0),full_matrices=False)
        xy=(local-local.mean(0))@basis[:2].T
    _,unique=np.unique(np.round(xy,5),axis=0,return_index=True)
    local,colors,xy=local[unique],colors[unique],xy[unique]
    faces=Delaunay(xy).simplices
    nn=cKDTree(xy).query(xy,k=2)[0][:,1]
    limit=max(float(np.median(nn))*10, float(np.linalg.norm(np.ptp(xy,axis=0)))*.015)
    lengths=np.linalg.norm(local[faces]-local[np.roll(faces,1,axis=1)],axis=2)
    faces=faces[lengths.max(1)<limit]
    if len(faces)<10:
        raise ValueError('Not enough supported geometry for a mesh')
    mesh=trimesh.Trimesh(local,faces,vertex_colors=colors,process=False)
    return texture_mesh(mesh,geo,sfm,k,directory), {'method':'edge_filtered_2.5D_Delaunay','watertight':False,'vertices':len(local),'faces':len(faces),'note':'Reduced-fidelity surface; vertical facades, undersides and occluded regions can be incomplete.'}


def texture_mesh(mesh, geo, sfm, k, directory):
    # Face atlas prevents seam UV ambiguity. Each tile samples one original camera.
    xyz=(mesh.vertices-geo['translation'])@geo['rotation']/geo['scale']
    triangles=xyz[mesh.faces]
    centroids=triangles.mean(1)
    normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    normal/=np.linalg.norm(normal,axis=1,keepdims=True)+1e-12
    score=np.zeros(len(triangles)); selected=np.full(len(triangles),-1,int)
    projections={}
    for j,pose in sfm['poses'].items():
        image=cv2.imread(str(directory/f'{j:06d}.png'))
        h,w=image.shape[:2]
        cam=xyz@pose[:,:3].T+pose[:,3]
        p=cam@k.T; uv=p[:,:2]/np.maximum(p[:,2:3],1e-8)
        triuv=uv[mesh.faces]
        inside=((triuv[:,:,0]>=1)&(triuv[:,:,0]<w-1)&(triuv[:,:,1]>=1)&(triuv[:,:,1]<h-1)&(cam[mesh.faces,2]>0)).all(1)
        # Dynamic masks exclude both triangle vertices and center from texture choice.
        mask=cv2.imread(str(directory.parent/'masks'/f'{j:06d}.png.png'),0)
        check=np.concatenate([triuv,triuv.mean(1,keepdims=True)],axis=1).astype(int)
        inside &= (mask[np.clip(check[:,:,1],0,h-1),np.clip(check[:,:,0],0,w-1)]>0).all(1)
        view=(-pose[:,:3].T@pose[:,3])-centroids
        distance=np.linalg.norm(view,axis=1)
        angle=np.abs(np.sum(normal*view,axis=1))/(distance+1e-9)
        weight=inside*angle/(distance**2+1e-9)
        better=weight>score
        selected[better]=j; score[better]=weight[better]
        projections[j]=uv
    tile=8; grid=int(np.ceil(np.sqrt(len(triangles))))
    atlas=np.full((grid*tile,grid*tile,3),120,np.uint8)
    coords=[]
    loaded={j:cv2.imread(str(directory/f'{j:06d}.png')) for j in sfm['poses']}
    aa,bb=np.meshgrid(np.linspace(0,1,tile),np.linspace(0,1,tile))
    # The upper triangle is used; duplicate edge texels keep interpolation stable.
    b=np.minimum(bb,1-aa)
    for f,face in enumerate(mesh.faces):
        row,col=divmod(f,grid)
        if selected[f]>=0:
            tri=projections[selected[f]][face]
            uv=tri[0]+aa[:,:,None]*(tri[1]-tri[0])+b[:,:,None]*(tri[2]-tri[0])
            sampled=cv2.remap(loaded[selected[f]],uv[:,:,0].astype(np.float32),uv[:,:,1].astype(np.float32),cv2.INTER_LINEAR)
            atlas[row*tile:(row+1)*tile,col*tile:(col+1)*tile]=sampled[:,:,::-1]
        else:
            atlas[row*tile:(row+1)*tile,col*tile:(col+1)*tile]=mesh.visual.vertex_colors[face,:3].mean(0)
        x,y=col*tile,row*tile; size=grid*tile
        coords.extend([((x+.5)/size,1-(y+.5)/size),((x+tile-.5)/size,1-(y+.5)/size),((x+.5)/size,1-(y+tile-.5)/size)])
    result=trimesh.Trimesh(mesh.vertices[mesh.faces].reshape(-1,3),np.arange(len(mesh.faces)*3).reshape(-1,3),process=False)
    result.visual=trimesh.visual.texture.TextureVisuals(uv=np.asarray(coords),image=Image.fromarray(atlas))
    return result
