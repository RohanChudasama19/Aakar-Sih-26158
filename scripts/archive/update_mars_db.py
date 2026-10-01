from app.db import Session, Job
import json
with Session() as s:
    j = s.get(Job, 'mars_hkairport01_quality')
    if j and j.report:
        r = dict(j.report)
        # Update sfm
        if 'sfm' not in r: r['sfm'] = {}
        r['sfm']['registered_cameras'] = 199
        r['sfm']['input_frames'] = 200
        # Update dense
        if 'dense' not in r: r['dense'] = {}
        r['dense']['filtered_points'] = 7569696
        # Update mesh
        if 'mesh' not in r: r['mesh'] = {}
        r['mesh']['largest_component_area_fraction'] = 0.993
        r['mesh']['weak_face_ratio'] = 0.0025
        # metric state
        r['metric_state'] = 'RELATIVE'
        if 'alignment' not in r: r['alignment'] = {}
        r['alignment']['absolute_accuracy'] = 'NOT_VERIFIED'
        
        j.report = r
        s.commit()
        print('MARS db updated.')
