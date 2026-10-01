# Task 1: Update MARS DB record with provenance
from app.db import Session, Job
import time

with Session() as s:
    j = s.get(Job, 'mars_hkairport01_quality')
    if j:
        r = dict(j.report) if j.report else {}
        r['_provenance'] = 'IMPORTED_FRAME_BASED_RECONSTRUCTION'
        r['_import_note'] = (
            'Executed via standalone COLMAP CLI phases (SfM+PatchMatch+Fusion+Poisson+Texture). '
            'NOT through the AAKAR production upload/worker lifecycle. '
            'Seeded into application database post-hoc for demonstration.'
        )
        r['_import_time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        j.report = r
        s.commit()
        print('Provenance set. ID:', j.id)
        print('_provenance:', j.report.get('_provenance'))
    else:
        print('Job not found!')
