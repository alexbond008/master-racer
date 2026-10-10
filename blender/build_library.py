# Peckham Library (Will Alsop, 2000). Cues (from Commons photos + archiweb/c20/Wikipedia text):
# 1 inverted L: five-storey vertical stem + horizontal arm cantilevered ~12 m above a plaza
# 2 arm soffit carried on thin DARK steel raking columns at random angles, soffit dark bronze/timber with downlights
# 3 pre-patinated seamed copper, pale turquoise-green, horizontal panel seams, on end faces
# 4 long faces: vertical stripes of saturated coloured glass (lime-yellow, red, orange, green, teal, blue, black, clear)
# 5 vermilion 'beret' pod (dome with brim) + a 2nd pod piercing the roof, stainless 'LIBRARY' letters 2 m high on the front roof edge
# 6 stem ground floors glazed (lit info/media centre); stair/lift core and plant on roof
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
reset()
rng = random.Random(7)
b = B().frame(-1.3, 4.1, 6.7)       # footprint rect centre + yaw from OSM polygon
W, D = 25.0, 42.6; hx, hy = W/2, D/2
H = 22.0; Z_ARM = 12.0; YS = 0.0     # stem begins at local y=0
cuA = mat('Copper_A', (118, 178, 160), 0.45, 0.35)
cuB = mat('Copper_B', (96, 160, 142), 0.5, 0.35)
cuC = mat('Copper_C', (140, 192, 172), 0.45, 0.35)
soff = mat('Soffit', (74, 50, 34), 0.7)
steel = mat('Steel', (38, 40, 46), 0.4, 0.8)
roof = mat('Roof', (60, 66, 66), 0.8)
dark = mat('Glass_Dark', (22, 30, 42), 0.1, 0.5)
beret = mat('Beret', (235, 70, 25), 0.35, 0.1, emit=(255, 80, 20), strength=0.8)
pod2 = mat('Pod_Pale', (190, 175, 150), 0.6)
steelc = mat('Stainless', (200, 205, 210), 0.3, 0.9)
signm = mat('Emit_Sign', (255, 255, 255), 0.4, emit=(235, 245, 255), strength=3.5)
winw = mat('Emit_Window', (255, 214, 140), 0.3, emit=(255, 196, 110), strength=3.5)
pal = [('lime', (205, 235, 40)), ('red', (225, 35, 40)), ('orange', (245, 120, 30)), ('green', (30, 170, 70)),
       ('teal', (20, 160, 160)), ('blue', (40, 90, 220)), ('black', (18, 18, 22)), ('yellow', (250, 220, 40)),
       ('clear', (160, 200, 230)), ('magenta', (200, 30, 110))]
gm = {n: mat('Emit_Glass_' + n, c, 0.15, 0.2, emit=c, strength=(0.6 if n == 'black' else 2.0 if n != 'clear' else 1.2)) for n, c in pal}
seq = ['lime', 'lime', 'clear', 'red', 'orange', 'clear', 'green', 'teal', 'black', 'clear', 'lime', 'yellow', 'blue', 'clear', 'red', 'magenta', 'clear', 'lime', 'teal', 'blue', 'clear', 'orange', 'green', 'black']

# ---- structural core boxes (copper skin)
b.box(cuA, -hx, hx, YS, hy, 0, H)                       # stem full height
b.box(cuA, -hx, hx, -hy, YS, Z_ARM, H)                  # arm
b.box(soff, -hx, hx, -hy, YS, Z_ARM - 0.7, Z_ARM, top=False)   # soffit slab (drawn below arm)
b.box(roof, -hx - 0.1, hx + 0.1, -hy - 0.1, hy + 0.1, H, H + 0.35)  # roof slab / parapet cap

# ---- copper panel seams on end faces (horizontal strips) -- -Y end (arm), +Y end (stem back), and stem/arm sides partially
def seams(y, ny, z0, z1, x0, x1, ph=1.15):
    z = z0; k = 0
    while z + ph <= z1 + 1e-6:
        b.wrect(cuB if k % 2 else cuC, (x0, y, z), (1, 0), (0, ny), x1 - x0, ph - 0.06, off=0.03)
        z += ph; k += 1
seams(-hy, -1, Z_ARM, H, -hx, hx)
seams(hy, 1, 0.0, H, -hx, hx)
# small square dark windows on copper ends
for zz in (14.0, 17.5, 20.5):
    for xx in (-8.0, -2.5, 3.0, 8.5):
        b.wrect(dark, (xx, -hy, zz), (1, 0), (0, -1), 1.6, 1.6, off=0.07)
for zz in (4.0, 8.5, 13.0, 17.5):
    for xx in (-7.5, -1.5, 5.0):
        b.wrect(winw if rng.random() < 0.5 else dark, (xx, hy, zz), (1, 0), (0, 1), 1.6, 1.8, off=0.07)

# ---- coloured glass long faces
def stripes(x, nx, y0, y1, z0, z1, seed):
    r = random.Random(seed); y = y0; i = r.randint(0, 5)
    while y < y1 - 0.2:
        w = min(r.uniform(0.9, 1.9), y1 - y)
        if seq[i % len(seq)] in ('lime', 'yellow') and r.random() < 0.5: w = min(w + 0.7, y1 - y)
        n = seq[i % len(seq)]
        b.wrect(gm[n], (x, y if nx > 0 else y + w, z0), (0, 1) if nx > 0 else (0, -1), (nx, 0), w - 0.05, z1 - z0, off=0.05)
        y += w; i += 1
stripes(hx, 1, YS, hy, 0.0, H, 11)        # stem, +X side
stripes(hx, 1, -hy, YS, Z_ARM, H, 12)     # arm, +X side
stripes(-hx, -1, YS, hy, 0.0, H, 13)      # stem, -X side
stripes(-hx, -1, -hy, YS, Z_ARM, H, 14)   # arm, -X side
# floor-line mullion bands + hopper vents
for x, nx in ((hx, 1), (-hx, -1)):
    for k in range(1, 5):
        z = k * 4.4
        yy0 = -hy if z > Z_ARM else YS
        if z >= Z_ARM - 0.1 or True:
            ya = YS if z < Z_ARM else -hy
            b.box(steel, x + 0.0, x + nx * 0.14, ya, hy, z - 0.12, z + 0.12, top=True, bottom=True)
# stem ground-floor (z<12) base glazing zone on its front face (y=YS facing -Y, under the arm): lit info centre
for i in range(8):
    x0 = -hx + 0.8 + i * 3.0
    b.wrect(winw if i % 3 else dark, (x0, YS, 0.4), (1, 0), (0, -1), 2.6, 5.2, off=0.06)
    b.wrect(winw if i % 2 else dark, (x0, YS, 6.4), (1, 0), (0, -1), 2.6, 4.6, off=0.06)
    b.box(steel, x0 - 0.2, x0 - 0.05, YS - 0.1, YS - 0.03, 0.0, Z_ARM)
# ---- raking steel columns under the arm
r = random.Random(3)
for yt in (-19.5, -13.5, -7.5, -2.0):
    for xt in (-10.0, -4.5, 1.0, 6.5, 11.0):
        if yt in (-13.5, -7.5) and xt in (-10.0, 11.0): continue
        top = (xt + r.uniform(-0.5, 0.5), yt, Z_ARM - 0.7)
        bot = (xt + r.uniform(-3.5, 3.5), yt + r.uniform(-4.0, 3.5), 0.0)
        b.beam(steel, bot, top, w=0.16, n=6)
# downlights under soffit
for yy in (-18, -12, -6, -1.5):
    for xx in (-8, -2.7, 2.7, 8):
        b.wrect(winw, (xx - 0.25, yy, Z_ARM - 0.72), (1, 0), (0, 1), 0.5, 0.5, off=0.0) if False else \
            b.quad(winw, (xx-0.3, yy-0.3, Z_ARM-0.72), (xx-0.3, yy+0.3, Z_ARM-0.72), (xx+0.3, yy+0.3, Z_ARM-0.72), (xx+0.3, yy-0.3, Z_ARM-0.72))
# ---- roof: pods, core, plant
b.ellipsoid(beret, 0.5, -8.5, H + 0.2, 4.6, 3.6, 2.4, nu=16, nv=6, zmin=0.0)       # dome
b.cyl(beret, 0.5, -8.5, H + 0.2, H + 0.5, 6.2, n=20)                              # brim disc
b.ellipsoid(pod2, 6.0, -2.0, H + 0.2, 3.2, 3.0, 2.6, nu=12, nv=5, zmin=0.0)
b.ellipsoid(pod2, -6.5, 5.0, H + 0.2, 2.6, 2.4, 2.0, nu=12, nv=5, zmin=0.0)
b.box(cuC, 4.5, 10.5, 12.0, 18.0, H + 0.35, H + 4.0)                              # lift/stair core
b.box(steel, 4.5, 10.5, 12.0, 18.0, H + 4.0, H + 4.25)
for k in range(4): b.wrect(winw, (5.2 + k * 1.4, 12.0, H + 1.2), (1, 0), (0, -1), 0.8, 1.8, off=0.05)
b.box(roof, -9, -3, 8, 13, H + 0.35, H + 1.8)
# parapet
for (x0, x1, y0, y1) in ((-hx, hx, hy - 0.2, hy), (-hx, hx, -hy, -hy + 0.2), (-hx, -hx + 0.2, -hy, hy), (hx - 0.2, hx, -hy, hy)):
    b.box(steel, x0, x1, y0, y1, H + 0.35, H + 0.9)
objs = b.build('library')
# LIBRARY letters, stainless, glowing slightly, standing on the front roof edge facing -Y
px, py, pz = Frame(-1.3, 4.1, 6.7).p(-3.0, -hy - 0.15, H + 0.9)
t = text_mesh('LIBRARY', 2.1, signm, (px, py, pz), rot=(math.radians(90), 0, math.radians(6.7)), extrude=0.25, name='library_letters')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
# crisp bevel? skip (cost). smooth-shade the pods only
for o in objs:
    if 'Beret' in o.name or 'Pod' in o.name:
        for p in o.data.polygons: p.use_smooth = True
print('TRIS', tri_count(objs))
export('library', 'Peckham Library (Alsop 2000): inverted-L, stem + arm cantilevered 12 m on raking steel columns, patinated copper ends, '
       'coloured-glass long faces, vermilion beret pod, LIBRARY letters. Front (arm end) faces -Y; rotated 6.7 deg to OSM footprint.')
if '--preview' in sys.argv or True:
    shoot = setup_preview('library', (0, 0), 60, H)
    for nm, az, dm, el in (('front34', -35, 1.0, 0.35), ('rear34', 145, 1.0, 0.35), ('side', 90, 0.9, 0.12), ('top', -25, 1.0, 1.0)):
        shoot(nm, az, dm, el)
