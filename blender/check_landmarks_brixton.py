"""Re-import each exported GLB and print bbox (Blender Z-up after import) + material names. blender -b --python check_landmarks_brixton.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbx_common import *
for k in ['academy', 'townhall', 'windmill', 'stmatthews', 'brixton_village', 'brixton_station']:
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT_DIR, f'{k}.glb'))
    mn, mx = bbox_world()
    mats = sorted({m.name for o in bpy.context.scene.objects if o.type == 'MESH' for m in o.data.materials})
    print('REIMPORT', k, 'tris', tri_count(), 'min', tuple(round(v, 1) for v in mn), 'max', tuple(round(v, 1) for v in mx), 'nmat', len(mats))
