import bpy, sys
from mathutils import Vector
for k in ['library','levels','bussey','peckham_station','clock']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath='/Users/aleksandergornik/Projects/master-racer/public/models/landmarks/%s.glb' % k)
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3); tris = 0; mats=set()
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
        for m in o.data.materials: mats.add(m.name)
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            for i in range(3): mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    print('VERIFY', k, 'tris', tris, 'bbox', [round(x,1) for x in mn], [round(x,1) for x in mx], 'size', [round(mx[i]-mn[i],1) for i in range(3)], 'mats', len(mats))
