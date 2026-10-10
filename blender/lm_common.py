"""Shared helpers for landmark models (bpy). Run via: blender -b --python <script>.py
Everything is built from raw verts/faces per material, in WORLD frame (Blender XY metres, origin = footprint
centroid, street toward -Y). `Frame` lets a part be built in an oriented local frame."""
import bpy, bmesh, math, json, os, random, sys
from mathutils import Vector, Matrix

ROOT = os.path.expanduser('~/Projects/master-racer')
FP = json.load(open(ROOT + '/blender/landmark_footprints.json'))

def srgb(r, g, b):
    f = lambda c: ((c / 255 + 0.055) / 1.055) ** 2.4 if c / 255 > 0.04045 else c / 255 / 12.92
    return (f(r), f(g), f(b), 1.0)

_mats = {}
def mat(name, rgb, rough=0.6, metal=0.0, emit=None, strength=4.0, alpha=None):
    """rgb in sRGB 0-255. emit = sRGB colour tuple for emission."""
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = srgb(*rgb)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = srgb(*emit)
        bsdf.inputs['Emission Strength'].default_value = strength
    if alpha is not None:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    _mats[name] = m
    return m

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()

class Frame:
    def __init__(s, ox=0, oy=0, ang_deg=0, oz=0):
        s.ox, s.oy, s.oz = ox, oy, oz
        a = math.radians(ang_deg); s.c, s.s = math.cos(a), math.sin(a)
    def p(s, x, y, z=0):
        return (s.ox + x * s.c - y * s.s, s.oy + x * s.s + y * s.c, s.oz + z)

class B:
    """Mesh builder. Collects faces per material name."""
    def __init__(s):
        s.d = {}      # mat -> (verts, faces)
        s.f = Frame()
    def frame(s, ox=0, oy=0, ang=0, oz=0):
        s.f = Frame(ox, oy, ang, oz); return s
    def _g(s, m):
        if m not in s.d: s.d[m] = ([], [])
        return s.d[m]
    def poly(s, m, pts_local):
        """one ngon face, pts in local frame (x,y,z); winding as given"""
        v, f = s._g(m)
        i = len(v)
        for p in pts_local: v.append(s.f.p(*p))
        f.append(tuple(range(i, i + len(pts_local))))
    def quad(s, m, a, b, c, d): s.poly(m, [a, b, c, d])
    def box(s, m, x0, x1, y0, y1, z0, z1, top=True, bottom=True):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        P = lambda x, y, z: (x, y, z)
        s.quad(m, P(x0,y0,z0), P(x1,y0,z0), P(x1,y0,z1), P(x0,y0,z1))   # -y
        s.quad(m, P(x1,y1,z0), P(x0,y1,z0), P(x0,y1,z1), P(x1,y1,z1))   # +y
        s.quad(m, P(x0,y1,z0), P(x0,y0,z0), P(x0,y0,z1), P(x0,y1,z1))   # -x
        s.quad(m, P(x1,y0,z0), P(x1,y1,z0), P(x1,y1,z1), P(x1,y0,z1))   # +x
        if top: s.quad(m, P(x0,y0,z1), P(x1,y0,z1), P(x1,y1,z1), P(x0,y1,z1))
        if bottom: s.quad(m, P(x0,y1,z0), P(x1,y1,z0), P(x1,y0,z0), P(x0,y0,z0))
    def prism(s, m, pts, z0, z1, top=True, bottom=True):
        """extrude 2D polygon (local xy); any winding"""
        a = sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
        if a < 0: pts = pts[::-1]
        n = len(pts)
        for i in range(n):
            p, q = pts[i], pts[(i+1)%n]
            s.quad(m, (p[0],p[1],z0), (q[0],q[1],z0), (q[0],q[1],z1), (p[0],p[1],z1))
        if top: s.poly(m, [(p[0],p[1],z1) for p in pts])
        if bottom: s.poly(m, [(p[0],p[1],z0) for p in pts[::-1]])
    def cyl(s, m, cx, cy, z0, z1, r, n=10, r1=None, cap=True):
        r1 = r if r1 is None else r1
        for i in range(n):
            a0, a1 = 2*math.pi*i/n, 2*math.pi*(i+1)/n
            s.quad(m, (cx+r*math.cos(a0),cy+r*math.sin(a0),z0), (cx+r*math.cos(a1),cy+r*math.sin(a1),z0),
                      (cx+r1*math.cos(a1),cy+r1*math.sin(a1),z1), (cx+r1*math.cos(a0),cy+r1*math.sin(a0),z1))
        if cap:
            s.poly(m, [(cx+r1*math.cos(2*math.pi*i/n),cy+r1*math.sin(2*math.pi*i/n),z1) for i in range(n)])
            s.poly(m, [(cx+r*math.cos(-2*math.pi*i/n),cy+r*math.sin(-2*math.pi*i/n),z0) for i in range(n)])
    def pyramid(s, m, x0, x1, y0, y1, z0, z1, ax=None, ay=None):
        ax = (x0+x1)/2 if ax is None else ax; ay = (y0+y1)/2 if ay is None else ay
        A=(x0,y0,z0);Bq=(x1,y0,z0);C=(x1,y1,z0);D=(x0,y1,z0);T=(ax,ay,z1)
        s.poly(m,[A,Bq,T]); s.poly(m,[Bq,C,T]); s.poly(m,[C,D,T]); s.poly(m,[D,A,T])
        s.poly(m,[D,C,Bq,A])
    def gable(s, m, x0, x1, y0, y1, z0, z1, along='y', overhang=0.0):
        """pitched roof. ridge runs along 'y' (gable ends at y0,y1 sides -> triangles on y faces) or 'x'"""
        if along == 'y':
            xm = (x0+x1)/2
            s.poly(m,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)][::-1])
            s.poly(m,[(x0,y0,z0),(xm,y0,z1),(xm,y1,z1),(x0,y1,z0)][::-1]); 
            s.poly(m,[(x1,y0,z0),(x1,y1,z0),(xm,y1,z1),(xm,y0,z1)])
            s.poly(m,[(x0,y0,z0),(x1,y0,z0),(xm,y0,z1)])
            s.poly(m,[(x1,y1,z0),(x0,y1,z0),(xm,y1,z1)])
        else:
            ym = (y0+y1)/2
            s.poly(m,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)][::-1])
            s.poly(m,[(x0,y0,z0),(x1,y0,z0),(x1,ym,z1),(x0,ym,z1)])
            s.poly(m,[(x1,y1,z0),(x0,y1,z0),(x0,ym,z1),(x1,ym,z1)])
            s.poly(m,[(x0,y1,z0),(x0,y0,z0),(x0,ym,z1)])
            s.poly(m,[(x1,y0,z0),(x1,y1,z0),(x1,ym,z1)])
    def beam(s, m, p0, p1, w=0.2, h=None, n=None):
        """square (or round if n) member between two LOCAL points"""
        h = w if h is None else h
        p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; L = d.length
        if L < 1e-6: return
        d.normalize()
        up = Vector((0,0,1)) if abs(d.z) < 0.99 else Vector((1,0,0))
        u = d.cross(up).normalized(); v = d.cross(u).normalized()
        if n:
            ring0 = [p0 + (u*math.cos(2*math.pi*i/n) + v*math.sin(2*math.pi*i/n))*w for i in range(n)]
            ring1 = [q + d*L for q in ring0]
            for i in range(n):
                j = (i+1)%n
                s.poly(m,[tuple(ring0[i]),tuple(ring0[j]),tuple(ring1[j]),tuple(ring1[i])])
            s.poly(m,[tuple(q) for q in ring1]); s.poly(m,[tuple(q) for q in ring0[::-1]])
            return
        c = [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
        r0 = [p0 + u*a + v*b for a,b in c]; r1 = [q + d*L for q in r0]
        for i in range(4):
            j = (i+1)%4
            s.poly(m,[tuple(r0[i]),tuple(r0[j]),tuple(r1[j]),tuple(r1[i])])
        s.poly(m,[tuple(q) for q in r1]); s.poly(m,[tuple(q) for q in r0[::-1]])
    def ellipsoid(s, m, cx, cy, cz, rx, ry, rz, nu=12, nv=8, zmin=-1.0):
        """UV ellipsoid (lat/long), zmin in [-1,1] clips bottom (dome if 0)"""
        import math as M
        v0 = M.asin(max(-1,min(1,zmin)))
        rows = []
        for j in range(nv+1):
            lat = v0 + (M.pi/2 - v0) * j/nv
            ring = [(cx+rx*M.cos(lat)*M.cos(2*M.pi*i/nu), cy+ry*M.cos(lat)*M.sin(2*M.pi*i/nu), cz+rz*M.sin(lat)) for i in range(nu)]
            rows.append(ring)
        for j in range(nv):
            for i in range(nu):
                k = (i+1)%nu
                a,b,c,d = rows[j][i], rows[j][k], rows[j+1][k], rows[j+1][i]
                s.poly(m,[a,b,c,d])
        if zmin > -0.99:
            s.poly(m,[r for r in rows[0][::-1]])
    # --- wall helpers: a rectangle on a wall, local frame. p = bottom-left point on wall, u = unit along wall (2D),
    #     n = outward unit normal (2D). w,h size. off = push out distance
    def wrect(s, m, p, u, n, w, h, off=0.03):
        x, y, z = p
        a = (x+n[0]*off, y+n[1]*off, z); b = (a[0]+u[0]*w, a[1]+u[1]*w, z)
        c = (b[0], b[1], z+h); d = (a[0], a[1], z+h)
        # make winding give normal n
        e1 = Vector(b) - Vector(a); e2 = Vector(d) - Vector(a)
        if e1.cross(e2).dot(Vector((n[0], n[1], 0))) < 0: s.quad(m, a, d, c, b)
        else: s.quad(m, a, b, c, d)
    def warch(s, m, p, u, n, w, h, rise=None, seg=6, off=0.03):
        """round/segmental-headed window: rectangle h-rise tall + arch cap. p bottom-left. one ngon."""
        rise = w/2 if rise is None else rise
        x, y, z = p
        pts = [(0, 0), (w, 0), (w, h-rise)]
        for i in range(1, seg):
            t = math.pi * i / seg  # from right (0) to left (pi)
            # ellipse centered (w/2, h-rise)
            pts.append((w/2 + (w/2)*math.cos(t), h-rise + rise*math.sin(t)))
        pts += [(0, h-rise)]
        P = [(x+n[0]*off+u[0]*a, y+n[1]*off+u[1]*a, z+b) for a, b in pts]
        e1 = Vector(P[1]) - Vector(P[0]); e2 = Vector(P[-1]) - Vector(P[0])
        if e1.cross(e2).dot(Vector((n[0], n[1], 0))) < 0: P = P[::-1]
        s.poly(m, P)
    def build(s, name):
        objs = []
        for m, (v, f) in s.d.items():
            me = bpy.data.meshes.new(name + '_' + m.name)
            me.from_pydata(v, [], f)
            me.update()
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(name + '_' + m.name, me)
            bpy.context.scene.collection.objects.link(ob)
            ob.data.materials.append(m)
            objs.append(ob)
        return objs

def text_mesh(txt, size, m, loc, rot=(math.radians(90),0,0), extrude=0.05, align='CENTER', name='txt', font=None):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object; t.name = name
    t.data.body = txt; t.data.size = size; t.data.extrude = extrude; t.data.align_x = align
    if font: t.data.font = font
    bpy.ops.object.convert(target='MESH')
    t = bpy.context.object
    t.data.materials.append(m)
    return t

def tri_count(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles(); n += len(o.data.loop_triangles)
    return n

def bbox(objs):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            for i in range(3): mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

def export(key, notes, objs_pred=None):
    out = ROOT + '/public/models/landmarks/' + key + '.glb'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for o in list(bpy.data.objects):
        if o.name.startswith('PV_'): bpy.data.objects.remove(o, do_unlink=True)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in objs:   # smooth-off crisp by default
        o.select_set(False)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_lights=False)
    mn, mx = bbox(objs)
    info = {"footprint": [round(mx.x-mn.x, 1), round(mx.y-mn.y, 1)], "height": round(mx.z, 1), "notes": notes}
    json.dump(info, open(ROOT + '/public/models/landmarks/' + key + '.json', 'w'), indent=1)
    print('EXPORT', key, 'tris', tri_count(objs), 'bbox', tuple(round(x,1) for x in mn), tuple(round(x,1) for x in mx))
    return out

def setup_preview(key, centre, radius, height, ground=True, ground_size=300):
    """dusk-ish world, lights, and render 4 views to previews/"""
    sc = bpy.context.scene
    try: sc.render.engine = 'BLENDER_EEVEE'
    except Exception: sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 1000, 640
    try: sc.eevee.taa_render_samples = 24
    except Exception: pass
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.045, 0.06, 0.11, 1); bg.inputs[1].default_value = 1.2
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=ground_size, location=(0,0,-0.02)); g = bpy.context.object; g.name = 'PV_ground'
        g.data.materials.append(mat('PV_asphalt', (46,46,52), 0.9))
    sun = bpy.data.lights.new('PV_sun', 'SUN'); sun.energy = 2.2; sun.color = (1.0, 0.72, 0.5)
    so = bpy.data.objects.new('PV_sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(65), 0, math.radians(35))
    fl = bpy.data.lights.new('PV_fill', 'SUN'); fl.energy = 0.8; fl.color = (0.55, 0.65, 1.0)
    fo = bpy.data.objects.new('PV_fill', fl); sc.collection.objects.link(fo); fo.rotation_euler = (math.radians(55), 0, math.radians(-150))
    cam = bpy.data.cameras.new('PV_cam'); cam.lens = 35; cam.clip_end = 2000
    co = bpy.data.objects.new('PV_cam', cam); sc.collection.objects.link(co); sc.camera = co
    cx, cy = centre
    views = {'front34': (-35, -1, 0.55), 'rear34': (145, -1, 0.55), 'side': (90, -1, 0.25), 'top': (-20, -1, 1.6), 'front': (0, -1, 0.3)}
    def shoot(name, azim_deg, dist_mul, elev_mul):
        a = math.radians(azim_deg - 90)  # azim 0 = from -Y
        d = radius * dist_mul
        pos = Vector((cx + math.cos(a)*d, cy + math.sin(a)*d, height*0.5 + radius*elev_mul))
        co.location = pos
        tgt = Vector((cx, cy, height*0.45))
        co.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = ROOT + '/blender/previews/%s_%s.png' % (key, name)
        bpy.ops.render.render(write_still=True)
    return shoot

def to_local(poly, ox, oy, ang_deg):
    a = math.radians(-ang_deg); c, s = math.cos(a), math.sin(a)
    return [((x-ox)*c - (y-oy)*s, (x-ox)*s + (y-oy)*c) for x, y in poly]

def edges(poly):
    """yield (p0, u, n, L) for each edge, n = outward normal (polygon made CCW)"""
    a = sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
    P = poly if a > 0 else poly[::-1]
    for i in range(len(P)):
        p, q = P[i], P[(i+1)%len(P)]
        dx, dy = q[0]-p[0], q[1]-p[1]; L = math.hypot(dx, dy)
        if L < 1e-6: continue
        u = (dx/L, dy/L); n = (u[1], -u[0])
        yield p, u, n, L

def inside(poly, x, y, margin=0.0):
    c = False; n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i+1)%n]
        if (y0 > y) != (y1 > y) and x < (x1-x0)*(y-y0)/(y1-y0) + x0: c = not c
    if not c: return False
    if margin:
        for p, u, nn, L in edges(poly):
            d = (x-p[0])*nn[0] + (y-p[1])*nn[1]
            if d > -margin: return False
    return True
