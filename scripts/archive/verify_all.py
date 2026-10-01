import hashlib
from pathlib import Path

def sha256(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(65536), b''): h.update(c)
    return h.hexdigest()

# Verify MARS artifacts
demo = Path('demo/mars_hkairport01_quality')
print('=== MARS ARTIFACT FREEZE ===')
for fn,expected in [
    ('dense_cloud.ply','d36f8c41cf7e63d06fb57c00e0182129c7970c54109cc860e6e1af69b277d20d'),
    ('mesh.ply','2eb26af707771445b9d940e896044f181917c23596f6f0bf506c349ebe50cbbd'),
    ('mesh.glb','c69eac810289a09273aec8c0aa0b4eb4307b72f7a5b92c420058e3f87bb183a0'),
]:
    p = demo / fn
    h = sha256(str(p))
    ok = 'VERIFIED' if h == expected else 'MISMATCH'
    print(f'{fn}: {ok}  sha256={h[:16]}...')

# Verify Colorado artifacts
print()
print('=== COLORADO DEGRADED DEMO ARTIFACTS ===')
degraded = Path('demo/degraded_fast_quality')
for fn,expected in [
    ('mesh_repaired.ply','551cdafb66a27a6d6cdc970a47a3fad7f69c63d24c6d70d7cb715063c213a7c3'),
    ('mesh_textured.glb','5f13ce184c9b91ceba24c7b28a3c4b4a2d83ece4253db3ec9ef130f643c8fe8f'),
]:
    p = degraded / fn
    if p.exists():
        h = sha256(str(p))
        ok = 'VERIFIED' if h == expected else 'MISMATCH'
        print(f'{fn}: {ok}  sha256={h[:16]}...')
    else:
        print(f'{fn}: MISSING')
