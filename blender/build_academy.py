"""O2 Academy Brixton (ex Astoria cinema 1929). Run: blender -b --python build_academy.py
Cues (Historic England / photos / OSM footprint):
 1 two-storey Art Deco street front in CREAM faience with GREEN faience bands + moulded panels, stepped pylons over pilasters
 2 rounded entrance foyer (OSM bump at the right-hand end of the front) capped by a verdigris COPPER dome w/ lantern
 3 huge illuminated entrance canopy / marquee (bulb-edged, white fascia lettering) + tall vertical blade sign
 4 tall arched upper-floor windows lit warm; lit glazed doors at ground floor
 5 big red-brown BRICK auditorium block (~21 m) behind with pilasters, tall arched windows, parapet, plant
 6 very tall brick FLY TOWER (~34 m) at the rear (far end of the footprint), with louvres + red aircraft lamps
Footprint: OSM polygon (Blender frame, front toward -Y).
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
from lm_common import _area

reset_scene()
B = Builder()
CREAM = mat('Faience_Cream', hexc('#e6dcc0'), 0.35)
GREEN = mat('Faience_Green', hexc('#2f6e55'), 0.3)
COPPER = mat('Copper_Verdigris', hexc('#58a08a'), 0.45, 0.4)
COPPER_D = mat('Copper_Dark', hexc('#2e5f52'), 0.5, 0.4)
BRICK = mat('Brick', hexc('#7a4034'), 0.9)
BRICK2 = mat('BrickDark', hexc('#5a2f28'), 0.9)
ROOF = mat('Roof', hexc('#3a3d42'), 0.9)
CONC = mat('Concrete', hexc('#8d8a84'), 0.9)
WIN = mat('Emit_Window', hexc('#ffc77a'), 0.4, emit=hexc('#ffb050'), strength=4.5)
WINB = mat('Emit_WindowCool', hexc('#bcd8ff'), 0.4, emit=hexc('#a8c8ff'), strength=3.5)
SIGN = mat('Emit_Sign', hexc('#fff3d8'), 0.4, emit=hexc('#fff0cf'), strength=6.0)
SIGN_R = mat('Emit_SignRed', hexc('#ff2a2a'), 0.4, emit=hexc('#ff2020'), strength=6.0)
SIGN_B = mat('Emit_SignBlue', hexc('#1a6bff'), 0.4, emit=hexc('#1560ff'), strength=6.0)
BULB = mat('Emit_Bulb', hexc('#ffe9a8'), 0.4, emit=hexc('#ffd878'), strength=8.0)
DARK = mat('Dark', hexc('#16181b'), 0.6)
METAL = mat('Metal', hexc('#4a4e54'), 0.5, 0.7)
EXIT = mat('Emit_Exit', hexc('#30ff70'), 0.4, emit=hexc('#20ff60'), strength=5.0)
RED_LAMP = mat('Emit_RedLamp', hexc('#ff1010'), 0.4, emit=hexc('#ff1010'), strength=10.0)

A = (-35.09, -3.21)
Bp = (-57.04, 46.94)
C = (-23.01, 81.21)
D = (13.26, -1.41)


def P(s, t):
    ax = (1 - s) * A[0] + s * D[0]
    ay = (1 - s) * A[1] + s * D[1]
    bx = (1 - s) * Bp[0] + s * C[0]
    by = (1 - s) * Bp[1] + s * C[1]
    return ((1 - t) * ax + t * bx, (1 - t) * ay + t * by)


def quad(s0, s1, t0, t1):
    return [P(s0, t0), P(s1, t0), P(s1, t1), P(s0, t1)]


def outward(poly, i):
    a, b = poly[i], poly[(i + 1) % len(poly)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dy / L, -dx / L), (dx / L, dy / L), L  # CCW polygons


def ccw(poly):
    return poly if _area(poly) > 0 else list(reversed(poly))


def wall_details(poly, z0, z1, spacing, pil_w=0.9, pil_out=0.35, win_rows=(), pil_mat=BRICK2, win_mat=WIN,
                 parapet=0.9, skip_len=3.0, arch=True):
    """Pilasters + window bays on every wall of a CCW polygon."""
    poly = ccw(poly)
    n = len(poly)
    for i in range(n):
        nrm, tan, L = outward(poly, i)
        if L < skip_len:
            continue
        a = poly[i]
        k = max(1, int(round(L / spacing)))
        step = L / k
        ang = math.atan2(tan[1], tan[0])
        for j in range(k + 1):
            u = j * step
            if j == 0:
                u = pil_w / 2
            if j == k:
                u = L - pil_w / 2
            cx = a[0] + tan[0] * u + nrm[0] * pil_out / 2
            cy = a[1] + tan[1] * u + nrm[1] * pil_out / 2
            B.box(cx, cy, z0, pil_w, pil_out, z1 - z0 + parapet, pil_mat, rot=ang)
        # windows between pilasters
        for j in range(k):
            u = (j + 0.5) * step
            for (wz0, wz1, ww) in win_rows:
                cx = a[0] + tan[0] * u + nrm[0] * 0.08
                cy = a[1] + tan[1] * u + nrm[1] * 0.08
                if arch:
                    B.push(ang, cx, cy)
                    B.arch_prism(-ww / 2, ww / 2, 0, wz0, wz1 - ww / 2, 0.12, win_mat)
                    B.pop()
                else:
                    B.box(cx, cy, wz0, ww, 0.12, wz1 - wz0, win_mat, rot=ang)
        # cornice band + parapet cap
        cx = (a[0] + poly[(i + 1) % n][0]) / 2 + nrm[0] * 0.25
        cy = (a[1] + poly[(i + 1) % n][1]) / 2 + nrm[1] * 0.25
        B.box(cx, cy, z1 - 0.1, L, 0.5, 0.5, pil_mat, rot=ang)
        B.box(cx - nrm[0] * 0.0, cy - nrm[1] * 0.0, z1 + parapet - 0.2, L, 0.6, 0.25, CONC, rot=ang)


# =====================================================================  AUDITORIUM + FLY TOWER (brick)
AUD = quad(0.0, 1.0, 0.10, 0.72)
FLY = quad(0.0, 1.0, 0.72, 1.0)
AUD_H = 21.0
FLY_H = 34.0
B.prism(AUD, 0, AUD_H, BRICK, bottom=False)
B.prism(FLY, 0, FLY_H, BRICK, bottom=False)
# roofs: dark slab + raised parapet frames
B.prism([(p[0], p[1]) for p in AUD], AUD_H, AUD_H + 0.15, ROOF)
wall_details(AUD, 0.0, AUD_H, 6.5, win_rows=[(6.0, 9.6, 2.0), (12.5, 16.0, 2.0)], parapet=0.9)
wall_details(FLY, 0.0, FLY_H, 7.0, win_rows=[(9.0, 12.0, 1.8), (20.0, 23.5, 1.8), (28.5, 31.0, 1.8)],
             parapet=1.1, pil_w=1.1, pil_out=0.45)
# fly-tower roof structure: stage loading lantern + steel tank + aircraft lights
ft = FLY
cx = sum(p[0] for p in ft) / 4
cy = sum(p[1] for p in ft) / 4
B.box(cx, cy, FLY_H + 0.15, 12, 9, 3.0, BRICK2, rot=0.55)
B.box(cx, cy, FLY_H + 3.15, 12.6, 9.6, 0.4, CONC, rot=0.55)
for p in ft:
    B.box(p[0], p[1], FLY_H + 0.2, 0.4, 0.4, 2.2, METAL)
    B.sphere(p[0], p[1], FLY_H + 2.6, 0.3, RED_LAMP, 8, 5)
# AUD roof plant boxes
for (s, t, w, d, h) in [(0.3, 0.3, 6, 4, 2.2), (0.7, 0.45, 5, 5, 2.8), (0.5, 0.62, 8, 3, 1.6), (0.2, 0.55, 4, 4, 2.0)]:
    x, y = P(s, t)
    B.box(x, y, AUD_H + 0.15, w, d, h, CONC, rot=0.06)
    B.box(x, y, AUD_H + 0.15 + h, w + 0.3, d + 0.3, 0.2, METAL, rot=0.06)
# auditorium roof: low pitched gable ridge along long axis (cap sections)
for (s0, s1) in ((0.08, 0.92),):
    q = quad(s0, s1, 0.16, 0.66)
    cxr = sum(p[0] for p in q) / 4
    cyr = sum(p[1] for p in q) / 4

# exit doors on auditorium side walls (lit green EXIT + door)
AUDc = ccw(AUD)
for i in range(len(AUDc)):
    nrm, tan, L = outward(AUDc, i)
    if L < 20:
        continue
    for u in (L * 0.18, L * 0.5, L * 0.83):
        x = AUDc[i][0] + tan[0] * u + nrm[0] * 0.5
        y = AUDc[i][1] + tan[1] * u + nrm[1] * 0.5
        ang = math.atan2(tan[1], tan[0])
        B.box(x, y, 0, 2.4, 0.3, 2.6, DARK, rot=ang)
        B.box(x + nrm[0] * 0.2, y + nrm[1] * 0.2, 2.9, 0.8, 0.12, 0.3, EXIT, rot=ang)

# =====================================================================  FRONT BLOCK (cream/green faience)
FRONT_LEN = 31.07
FRONT_ROT = math.atan2(1.86, 31.07)
FH = 12.5
bays = 7
bw = FRONT_LEN / bays
B.push(FRONT_ROT, A[0], A[1])
# main wall (slight overlap with auditorium)
B.box(FRONT_LEN / 2, 5.5, 0, FRONT_LEN, 11, FH, CREAM)
# plinth (dark green tile) + stringcourses
B.box(FRONT_LEN / 2, -0.12, 0, FRONT_LEN + 0.2, 0.3, 1.0, GREEN)
B.box(FRONT_LEN / 2, -0.15, 4.2, FRONT_LEN, 0.34, 0.5, GREEN)  # canopy-level band
B.box(FRONT_LEN / 2, -0.2, 6.5, FRONT_LEN, 0.4, 0.45, GREEN)  # first-floor band
B.box(FRONT_LEN / 2, -0.3, FH - 0.2, FRONT_LEN + 0.4, 0.8, 0.5, CREAM)  # cornice
B.box(FRONT_LEN / 2, -0.35, FH + 0.3, FRONT_LEN + 0.4, 0.5, 1.4, GREEN)  # green frieze/parapet
B.box(FRONT_LEN / 2, -0.4, FH + 1.7, FRONT_LEN + 0.5, 0.6, 0.2, CREAM)
for i in range(bays + 1):
    x = i * bw
    # pilasters (cream) w/ green inlay, stepped pylons above parapet
    B.box(x, -0.3, 0.4, 0.95, 0.55, FH + 1.3, CREAM)
    B.box(x, -0.55, FH + 1.7, 0.8, 0.5, 1.7, CREAM)
    B.box(x, -0.6, FH + 3.4, 0.55, 0.4, 0.8, CREAM)
    B.box(x, -0.62, 1.5, 0.3, 0.1, FH - 1, GREEN)
for i in range(bays):
    xc = (i + 0.5) * bw
    # upper arched tall windows (lit) with green surround
    B.push(0, xc, 0)
    B.arch_prism(-1.35, 1.35, -0.12, 7.2, 10.5, 0.14, GREEN)
    B.arch_prism(-1.1, 1.1, -0.2, 7.4, 10.5, 0.1, WIN if i % 2 == 0 else WINB)
    B.box(0, -0.3, 7.0, 3.0, 0.5, 0.25, CREAM)  # sill
    B.pop()
    # moulded parapet panels (cream insets in green frieze)
    B.box(xc, -0.62, FH + 0.55, bw - 1.6, 0.1, 0.8, CREAM)
    # ground floor: lit entrance doors in middle bays, posters/shopfronts elsewhere
    B.push(0, xc, 0)
    if 1 <= i <= 5:
        B.arch_prism(-1.5, 1.5, -0.15, 0.2, 2.6, 0.12, DARK)
        B.arch_prism(-1.3, 1.3, -0.25, 0.2, 2.6, 0.1, WIN)
        B.box(0, -0.3, 0.0, 3.4, 0.4, 0.2, GREEN)  # step
    else:
        B.box(0, -0.2, 1.3, 2.6, 0.12, 2.2, WINB)
        B.box(0, -0.15, 1.1, 3.1, 0.2, 2.6, DARK)
    B.pop()

# ---- marquee / canopy (big illuminated)
MX0, MX1, MP = 3.2, FRONT_LEN - 3.2, 3.6
mz = 4.9
B.box((MX0 + MX1) / 2, -MP / 2, mz, MX1 - MX0, MP, 0.28, CREAM)
B.box((MX0 + MX1) / 2, -MP / 2, mz - 0.06, MX1 - MX0 - 0.4, MP - 0.4, 0.05, BULB)  # lit underside
# fascia: green frame + big white lit panel
B.box((MX0 + MX1) / 2, -MP, mz - 0.1, MX1 - MX0 + 0.3, 0.3, 1.7, GREEN)
B.box((MX0 + MX1) / 2, -MP - 0.18, mz + 0.05, MX1 - MX0 - 0.5, 0.08, 1.3, SIGN)
B.box(MX0 - 0.1, -MP / 2, mz - 0.1, 0.3, MP, 1.7, GREEN)
B.box(MX1 + 0.1, -MP / 2, mz - 0.1, 0.3, MP, 1.7, GREEN)
# top upstand w/ bulbs
B.box((MX0 + MX1) / 2, -MP + 0.1, mz + 1.6, MX1 - MX0 + 0.3, 0.3, 0.3, GREEN)
n = int((MX1 - MX0) / 0.7)
for k in range(n + 1):
    x = MX0 + (MX1 - MX0) * k / n
    B.box(x, -MP - 0.02, mz + 1.73, 0.22, 0.22, 0.22, BULB)
    B.box(x, -MP - 0.02, mz - 0.4, 0.22, 0.22, 0.22, BULB)
for k in range(5):
    y = -MP * (k + 0.5) / 5
    B.box(MX0 - 0.05, y, mz + 1.6, 0.25, 0.22, 0.22, BULB)
    B.box(MX1 + 0.05, y, mz + 1.6, 0.25, 0.22, 0.22, BULB)
# sign lettering on the fascia (red letters on lit white) : text mesh stands off the panel
B.text('O2 ACADEMY BRIXTON', (MX0 + MX1) / 2, -MP - 0.35, mz + 0.7, 0.95, SIGN_R, extrude=0.12)
# hanger rods
for x in (MX0 + 1.5, MX1 - 1.5):
    B.box(x, -MP + 0.3, mz + 0.28, 0.1, 0.1, 2.0, METAL)

# ---- vertical blade sign at the foyer corner of the front block
VX, VP = FRONT_LEN - 0.6, 1.4
B.box(VX, -VP / 2, 6.0, 2.0, 0.5, 11.3, GREEN)
B.box(VX, -VP / 2 - 0.2, 6.2, 1.6, 0.2, 10.4, SIGN)
for i, ch in enumerate('ACADEMY'):
    B.text(ch, VX, -VP / 2 - 0.38, 14.6 - i * 1.28, 1.15, SIGN_R, extrude=0.1)
B.box(VX, -VP / 2 - 0.2, 16.5, 1.6, 0.3, 0.2, BULB)
B.sphere(VX, -VP / 2 - 0.35, 17.3, 0.62, SIGN_B, 12, 8)
B.text('O2', VX, -VP / 2 - 0.95, 17.3, 0.55, SIGN, extrude=0.05)
B.pop()

# =====================================================================  FOYER ROTUNDA + COPPER DOME
FOYER = [(-4.02, -1.35), (2.53, -14.64), (3.32, -14.62), (4.68, -13.14), (6.81, -14.19), (9.21, -14.34),
         (11.46, -13.56), (13.25, -11.97), (14.3, -9.83), (14.45, -7.43), (13.74, -5.12), (12.15, -3.33),
         (13.26, -1.41)]
FZ = 10.5
B.prism(FOYER, 0, FZ, CREAM)
B.prism(FOYER, 0, 1.0, GREEN)
fp = ccw(FOYER)
# lit arched windows + green bands on foyer drum
for i in range(len(fp)):
    nrm, tan, L = outward(fp, i)
    if L < 1.2:
        continue
    m = ((fp[i][0] + fp[(i + 1) % len(fp)][0]) / 2, (fp[i][1] + fp[(i + 1) % len(fp)][1]) / 2)
    ang = math.atan2(tan[1], tan[0])
    wide = min(L * 0.55, 2.2)
    B.push(ang, m[0] + nrm[0] * 0.05, m[1] + nrm[1] * 0.05)
    B.arch_prism(-wide / 2 - 0.25, wide / 2 + 0.25, 0, 5.2, 8.3 if wide > 1.4 else 7.6, 0.12, GREEN)
    B.arch_prism(-wide / 2, wide / 2, -0.08, 5.4, 8.3 if wide > 1.4 else 7.6, 0.12, WIN)
    B.pop()
    # ground-floor lit doors on the big front facing edges
    if nrm[1] < -0.55 and L > 1.5:
        B.push(ang, m[0] + nrm[0] * 0.05, m[1] + nrm[1] * 0.05)
        B.arch_prism(-wide / 2, wide / 2, -0.1, 0.2, 3.3, 0.12, WIN)
        B.pop()
# bands/cornice around the drum (offset polygon via scaled copy about centre)
FCX, FCY = 5.6, -8.0
def scaled(poly, k):
    return [(FCX + (p[0] - FCX) * k, FCY + (p[1] - FCY) * k) for p in poly]
B.prism(scaled(FOYER, 1.035), 4.0, 4.45, GREEN, top=True)
B.prism(scaled(FOYER, 1.045), FZ - 0.9, FZ + 0.35, CREAM, top=True)
B.prism(scaled(FOYER, 1.055), FZ - 0.1, FZ + 0.35, GREEN, top=True)
# copper dome: ellipse sx,sy ~ polygon extents, slightly flattened, with ribs
DX, DY = 5.7, -8.0
dsx, dsy, dhz = 8.1, 6.0, 6.3
B.frustum(DX, DY, FZ + 0.35, FZ + 1.1, 1.0, 0.99, COPPER_D, segs=40, cap_top=False, sx=dsx, sy=dsy)
B.dome(DX, DY, FZ + 1.1, 0.985, COPPER, segs=40, rings=10, hz=dhz / 1.0, sx=dsx, sy=dsy)
# raised ribs (narrow darker ridges) every 15 degrees
rib_pts = 9
for k in range(24):
    a = 2 * math.pi * k / 24
    prev = None
    for j in range(rib_pts + 1):
        t = (math.pi / 2) * 0.97 * j / rib_pts
        r = math.cos(t) * 1.005
        x = DX + math.cos(a) * r * dsx
        y = DY + math.sin(a) * r * dsy
        z = FZ + 1.1 + math.sin(t) * dhz * 1.005
        if prev is not None:
            B.face([prev[0], (x, y, z), (x, y, z + 0.08), (prev[0][0], prev[0][1], prev[0][2] + 0.08)], COPPER_D)
        prev = ((x, y, z),)
# lantern + finial on dome
LZ = FZ + 1.1 + dhz - 0.1
B.frustum(DX, DY, LZ, LZ + 1.4, 1.1, 1.0, COPPER_D, segs=12)
for k in range(8):
    a = 2 * math.pi * (k + 0.5) / 8
    B.box(DX + math.cos(a) * 1.02, DY + math.sin(a) * 1.02, LZ + 0.25, 0.3, 0.1, 0.9, WIN, rot=a + math.pi / 2)
B.frustum(DX, DY, LZ + 1.4, LZ + 2.1, 1.3, 0.2, COPPER, segs=12)
B.frustum(DX, DY, LZ + 2.1, LZ + 3.0, 0.07, 0.04, METAL, segs=6)
B.sphere(DX, DY, LZ + 3.05, 0.15, METAL, 6, 4)
# bulb-lined canopy over the foyer entrance (small, curved front)
B.box(8.2, -15.3, 3.7, 6.0, 1.6, 0.25, CREAM)
B.box(8.2, -15.3, 3.62, 5.6, 1.3, 0.05, BULB)
B.box(8.2, -16.05, 3.6, 6.2, 0.2, 0.9, GREEN)
B.box(8.2, -16.17, 3.75, 5.6, 0.06, 0.55, SIGN)
B.text('BRIXTON', 8.2, -16.25, 4.02, 0.5, SIGN_B, extrude=0.06)

cams = [
    ('front34', (-95, -110, 55), (-20, 20, 12), 40),
    ('rear34', (60, 150, 60), (-25, 30, 12), 40),
    ('side', (-170, 20, 28), (-22, 30, 14), 40),
    ('top', (-20, -30, 190), (-22, 32, 0), 38),
    ('frontclose', (-12, -60, 20), (-8, -6, 11), 34),
]
finish(B, 'academy', footprint=(71.5, 95.8),
       notes="O2 Academy Brixton: cream/green faience Art Deco front block (12.5 m + pylons), lit marquee + vertical blade sign, rounded foyer with copper dome (~10.5+7 m), red-brick auditorium 21 m, brick fly tower 34 m. Footprint = OSM polygon; origin = footprint centroid; front -Y. Marquee projects ~3.6 m beyond the footprint front.",
       cams=cams, bevel=0.03, skip_bevel=('Emit_Window', 'Emit_WindowCool', 'Emit_Sign', 'Emit_SignRed', 'Emit_SignBlue', 'Emit_Bulb', 'Emit_Exit', 'Emit_RedLamp'),
       res=(1100, 750))
