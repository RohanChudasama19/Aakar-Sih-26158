import sys
import bpy
args=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=args[0])
bpy.ops.export_scene.fbx(filepath=args[1],path_mode='COPY',embed_textures=True,axis_forward='-Y',axis_up='Z')
