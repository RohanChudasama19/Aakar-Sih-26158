import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1 :]
bpy.ops.wm.read_factory_settings(use_empty=True)
res = bpy.ops.import_scene.fbx(filepath=args[0])
if "FINISHED" not in res:
    sys.exit(1)
if len(bpy.context.scene.objects) == 0:
    sys.exit(1)
print("FBX verified.")
