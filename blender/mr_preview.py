"""Re-import a GLB and render verification previews.
blender -b --python mr_preview.py -- <id> [views...]   views: f34 r34 side top front rear
"""
import bpy, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
vid = argv[0]
views = argv[1:] or ['f34', 'r34', 'side', 'top']
ROOT = os.path.expanduser('~/Projects/master-racer')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'{ROOT}/public/models/cars/{vid}.glb')

mn = Vector((1e9,) * 3)
mx = Vector((-1e9,) * 3)
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        for v in me.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
print('IMPORTED', vid, 'tris', tris, 'size X/Y/Z', [round(mx[i] - mn[i], 3) for i in range(3)], 'min', [round(v, 3) for v in mn],
      'max', [round(v, 3) for v in mx])
print('OBJECTS', sorted(o.name for o in bpy.context.scene.objects))
print('MATS', sorted(m.name for m in bpy.data.materials))

c = (mn + mx) / 2
size = (mx - mn).length
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x, scn.render.resolution_y = 900, 560
scn.render.image_settings.file_format = 'PNG'
try:
    scn.eevee.taa_render_samples = 24
except Exception:
    pass
# world: dusk-ish sky for readable previews
w = bpy.data.worlds.new('w'); w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.35, 0.40, 0.52, 1); bg.inputs['Strength'].default_value = 1.6
scn.world = w
# ground
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.001))
gm = bpy.data.materials.new('g'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.22, 0.22, 0.23, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
bpy.context.object.data.materials.append(gm)
for loc, e, rot in (((6, -8, 10), 3.0, (0.8, 0.3, 0.5)), ((-8, 6, 6), 1.5, (1.0, 0, -2.2))):
    ld = bpy.data.lights.new('s', 'SUN'); ld.energy = e
    lo = bpy.data.objects.new('s', ld); bpy.context.scene.collection.objects.link(lo); lo.rotation_euler = rot

cam_d = bpy.data.cameras.new('c'); cam_d.lens = 40
cam = bpy.data.objects.new('c', cam_d); bpy.context.scene.collection.objects.link(cam); scn.camera = cam
D = size * 1.55
V = {
    'f34': Vector((1, -1.15, 0.55)), 'r34': Vector((-1, 1.15, 0.55)), 'side': Vector((1, 0, 0.12)),
    'top': Vector((0.45, -0.6, 1.5)), 'front': Vector((0, -1, 0.25)), 'rear': Vector((0, 1, 0.25)),
    'f34r': Vector((-1, -1.15, 0.5)), 'r34l': Vector((1, 1.15, 0.5)), 'low': Vector((1.0, -0.8, 0.12)),
}
for v in views:
    if v.startswith('c:'):
        tx, ty, tz, dx, dy, dz, dist = [float(t) for t in v[2:].split(',')]
        tgt = Vector((tx, ty, tz)); d = Vector((dx, dy, dz)).normalized()
        cam.location = tgt + d * dist
        q = (tgt - cam.location).to_track_quat('-Z', 'Y')
        v = 'zoom' + str(abs(hash(v)) % 1000)
        cam.rotation_euler = q.to_euler()
        scn.render.filepath = f'{ROOT}/blender/previews/{vid}_{v}.png'
        bpy.ops.render.render(write_still=True)
        print('rendered', scn.render.filepath)
        continue
    d = V[v].normalized()
    cam.location = c + d * D
    q = (c - cam.location).to_track_quat('-Z', 'Y')
    cam.rotation_euler = q.to_euler()
    scn.render.filepath = f'{ROOT}/blender/previews/{vid}_{v}.png'
    bpy.ops.render.render(write_still=True)
    print('rendered', scn.render.filepath)
