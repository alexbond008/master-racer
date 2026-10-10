"""Re-import <id>.glb and render preview PNGs + print bbox.
Usage: blender -b --python small_cars_preview.py -- <id> [views,comma,separated]
"""
import bpy, sys, math, os
from mathutils import Vector

ROOT = os.path.expanduser('~/Projects/master-racer')
argv = sys.argv[sys.argv.index('--') + 1:]
cid = argv[0]
views = argv[1].split(',') if len(argv) > 1 else ['front34', 'rear34', 'side', 'top']
res = int(argv[2]) if len(argv) > 2 else 1100

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'public/models/cars/%s.glb' % cid))

mn = Vector((1e9,) * 3)
mx = Vector((-1e9,) * 3)
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
names = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    names.append(ob.name)
    tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        mn = Vector((min(mn[i], w[i]) for i in range(3)))
        mx = Vector((max(mx[i], w[i]) for i in range(3)))
print('OBJECTS', sorted(names))
print('TRIS', tris)
print('BBOX min', tuple(round(v, 3) for v in mn), 'max', tuple(round(v, 3) for v in mx))
print('SIZE W=%.3f L=%.3f H=%.3f' % (mx.x - mn.x, mx.y - mn.y, mx.z - mn.z))
for ob in bpy.context.scene.objects:
    if ob.name.startswith('wheel'):
        print(ob.name, tuple(round(v, 3) for v in ob.matrix_world.translation))

L = mx.y - mn.y
ctr = Vector(((mx.x + mn.x) / 2, (mx.y + mn.y) / 2, 0.55))

# floor
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.002))
fl = bpy.context.active_object
m = bpy.data.materials.new('floor')
m.use_nodes = True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.32, 0.33, 0.35, 1)
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
fl.data.materials.append(m)

# world
w = bpy.data.worlds.new('w')
bpy.context.scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1)
bg.inputs['Strength'].default_value = 1.0

def light(kind, loc, energy, rot=None, size=None):
    d = bpy.data.lights.new(kind, kind)
    d.energy = energy
    if size and kind in ('AREA',):
        d.size = size
    o = bpy.data.objects.new(kind, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    return o

light('SUN', (0, 0, 8), 3.5, rot=(math.radians(50), math.radians(10), math.radians(35)))
light('SUN', (0, 0, 8), 1.2, rot=(math.radians(60), 0, math.radians(215)))

sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 0.62)
try:
    sc.eevee.taa_render_samples = 24
except Exception:
    pass
sc.view_settings.view_transform = 'Standard'

cam_d = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.lens = 45

D = max(L * 1.55, 4.5)
if 'topopen' in views:
    import bmesh
    for ob in list(bpy.context.scene.objects):
        if ob.name == 'interior':
            bm = bmesh.new(); bm.from_mesh(ob.data)
            dele = [f for f in bm.faces if f.calc_center_median().z > 1.22 and abs(f.normal.z) > 0.2 and f.calc_center_median().z > 1.0 + 0.0 and len(f.verts) > 0 and max(v.co.z for v in f.verts) - min(v.co.z for v in f.verts) < 0.2 and f.calc_area() > 0.0 and f.calc_center_median().z > 1.22]
            bmesh.ops.delete(bm, geom=dele, context='FACES')
            bm.to_mesh(ob.data); bm.free()
        if ob.name in ('body',):
            bm = bmesh.new(); bm.from_mesh(ob.data)
            dele = [f for f in bm.faces if f.calc_center_median().z > 0.95 and f.normal.z > 0.25]
            bmesh.ops.delete(bm, geom=dele, context='FACES')
            bm.to_mesh(ob.data); bm.free()
poses = {
    'low34': (Vector((0.80, -0.55, 0.16)), Vector((0, ctr.y, 1.0))),
    'topopen': (Vector((0.0, -0.08, 1.0)), ctr),
    'front34': (Vector((0.62, -0.78, 0.30)), ctr),
    'rear34': (Vector((-0.62, 0.78, 0.30)), ctr),
    'front34r': (Vector((-0.62, -0.78, 0.30)), ctr),
    'rear34l': (Vector((0.62, 0.78, 0.30)), ctr),
    'side': (Vector((1.0, 0.0, 0.08)), ctr),
    'front': (Vector((0.0, -1.0, 0.12)), ctr),
    'rear': (Vector((0.0, 1.0, 0.12)), ctr),
    'top': (Vector((0.0, -0.08, 1.0)), ctr),
}
for v in views:
    d, tgt = poses[v]
    dist = D * (1.55 if v in ('side',) else 1.1 if v in ('front','rear') else 1.0)
    cam.location = tgt + d.normalized() * dist
    direction = tgt - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = 70 if v in ('side', 'top', 'front', 'rear') else 50
    if v == 'low34':
        cam_d.lens = 40
    if v in ('top', 'topopen'):
        cam_d.lens = 50
        cam.location = tgt + d.normalized() * L * 2.1
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(ROOT, 'blender/previews/%s_%s.png' % (cid, v))
    bpy.ops.render.render(write_still=True)
    print('rendered', v)
