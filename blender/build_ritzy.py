"""ritzy - Ritzy Cinema (Electric Palace/Pavilion, 1911, E C Homer & Lucas; Grade II), Brixton Oval at Coldharbour Lane.

Cues (Historic England listing text + Commons photographs of the front and at night):
 1. Classical front in painted WHITE STUCCO over brick, with RED BRICK PANELS framed by white pilasters/bands (the 'red & white' look), slate roof behind.
 2. Three-part front: two narrow PAVILIONS capped by curved (segmental/shaped) gables crowned with a ROUNDEL CARTOUCHE ('EP' / cherubs panels), either side of a wider centre.
 3. CENTRE: big SEGMENTAL-ARCHED PEDIMENT over a recessed black BILLBOARD panel with white lettering; moulded band between floors.
 4. Ground floor: red entrance doors under a flat dark CANOPY with a lit 'BAR' fascia; red neon 'RITZY' letters on the canopy and a big red 'RITZY' sign on the roof of the left pavilion.
 5. Narrow sash windows in white surrounds on the pavilions; ground floor has raised masonry lines and keystones.
 6. To the right: a lower stucco ANNEX with a round-arched doorway and vertical 'CINEMA' blade sign, then a modern dark GLAZED FOYER EXTENSION (3 storeys).
 7. Rear/side elevation of nine bays divided by pilasters, nine round-headed arches with keystones; moulded cornice; slate roof.
 8. Footprint 41 x 17 m (rotated -4.2 deg) on the corner; ~3 storeys, 12-15 m.
"""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sl_lib import *
from mathutils import Vector

THETA = -4.2
rng = random.Random(9)
b = Builder(THETA)

define('Stucco', '#ece7db', rough=0.8)
define('Stucco_Shade', '#d4cebf', rough=0.85)
define('Brick_Red', '#8c3b2a', rough=0.9)
define('Brick_Back', '#7a4a38', rough=0.95)
define('Door_Red', '#b0281d', rough=0.5)
define('Neon_Red', '#e01208', rough=0.4, emit=4.5, emit_hex='#ff1408')
define('Billboard', '#101114', rough=0.5)
define('Sign_Text', '#fdfbf0', rough=0.4, emit=5.5)
define('Canopy_Dark', '#1c1d22', rough=0.5, metal=0.2)
define('Glass_Frame', '#2a2e35', rough=0.4, metal=0.5)
define('Glass_Lit', '#ffd89a', rough=0.2, emit=2.4)
define('Sign_Blue', '#1a2a6a', rough=0.4, emit=1.2, emit_hex='#3150d0')
define('Slate_Roof', '#40444c', rough=0.6, metal=0.1)

yF, yB = -5.2, 9.1
xL, xR = -25.6, 15.2
XP1, XP2 = -20.0, -9.0          # left pavilion | centre | right pavilion boundaries
XM = -3.4                       # end of historic facade
XA = 4.2                        # end of annex; glass extension beyond
H_C = 12.2                      # cornice height
H_ANX = 8.8

def seg_pts(x0, x1, z, rise, n=12):
    hw = (x1 - x0) / 2
    xm = (x0 + x1) / 2
    R = (hw ** 2 + rise ** 2) / (2 * rise)
    zc = z + rise - R
    pts = [(x0, z), (x1, z)]
    for i in range(1, n):
        x = x1 - (x1 - x0) * i / n
        pts.append((x, zc + math.sqrt(max(R * R - (x - xm) ** 2, 0))))
    return pts

# ---------------------------------------------------------------- main historic block
b.bbox('Stucco', xL, XM, yF, yB, 0, H_C)
b.bbox('Stucco_Shade', xL - 0.1, XM + 0.1, yF - 0.35, yF + 0.1, H_C - 0.6, H_C + 0.2)      # cornice
b.bbox('Stucco_Shade', xL - 0.1, XM + 0.1, yF - 0.2, yF + 0.05, 4.7, 5.1)                  # band between floors
b.bbox('Stucco_Shade', xL - 0.05, XM + 0.05, yF - 0.12, yF + 0.05, 0.0, 0.5)               # plinth
# raised masonry lines on ground floor
for z in [0.9 + i * 0.7 for i in range(5)]:
    b.bbox('Stucco_Shade', xL, XM, yF - 0.05, yF, z, z + 0.07)
# slate roof behind the crowns
b.hip('Slate_Roof', xL + 0.5, XM - 0.5, -1.5, yB - 0.4, H_C, 3.6, top_frac=0.0)
b.bbox('Stucco_Shade', xL - 0.1, XM + 0.1, yB - 0.3, yB + 0.1, H_C - 0.6, H_C + 0.2)

# red brick panels framed by white pilasters on the two pavilions and the centre flanks
def pavilion(x0, x1):
    xm = (x0 + x1) / 2
    # pilasters
    for x in (x0 + 0.3, x1 - 0.3):
        b.bbox('Stucco_Shade', x - 0.3, x + 0.3, yF - 0.18, yF, 5.1, H_C - 0.6)
    b.bbox('Brick_Red', x0 + 0.65, x1 - 0.65, yF - 0.06, yF, 5.2, H_C - 0.7)
    # tall narrow sash window with white surround (lit)
    b.bbox('Stucco', xm - 0.85, xm + 0.85, yF - 0.14, yF - 0.04, 6.1, 10.2)
    b.bbox('Glass_Lit' if rng.random() < 0.7 else 'Glass_Frame', xm - 0.6, xm + 0.6, yF - 0.2, yF - 0.14, 6.3, 10.0)
    b.bbox('Stucco_Shade', xm - 0.05, xm + 0.05, yF - 0.22, yF - 0.14, 6.3, 10.0)
    b.bbox('Stucco_Shade', xm - 0.95, xm + 0.95, yF - 0.28, yF - 0.04, 10.2, 10.5)
    # curved shaped gable crown + roundel cartouche
    b.profile_x('Stucco', seg_pts(x0 - 0.1, x1 + 0.1, H_C + 0.15, 2.6), yF - 0.3, yF + 1.0)
    b.profile_x('Stucco_Shade', seg_pts(x0 + 0.5, x1 - 0.5, H_C + 0.3, 1.8), yF - 0.38, yF - 0.28)
    pts = [(xm + 0.95 * math.cos(2 * math.pi * i / 18), H_C + 1.55 + 0.95 * math.sin(2 * math.pi * i / 18)) for i in range(18)]
    b.profile_x('Stucco', pts, yF - 0.5, yF - 0.36)
    pts = [(xm + 0.62 * math.cos(2 * math.pi * i / 18), H_C + 1.55 + 0.62 * math.sin(2 * math.pi * i / 18)) for i in range(18)]
    b.profile_x('Stucco_Shade', pts, yF - 0.56, yF - 0.5)
    # ground-floor doorway/window with keystone
    b.arch('Stucco_Shade', xm, yF, 0.5, 2.6, 3.9, depth=0.14, pointed=False, face='-Y')
    b.arch('Glass_Lit', xm, yF - 0.1, 0.6, 2.2, 3.5, depth=0.08, pointed=False, face='-Y')
    b.bbox('Stucco', xm - 0.25, xm + 0.25, yF - 0.2, yF, 4.0, 4.5)

pavilion(xL, XP1)
pavilion(XP2, XM)

# centre bay: brick flanks, billboard panel, big segmental pediment
b.bbox('Brick_Red', XP1 + 0.6, XP1 + 1.8, yF - 0.06, yF, 5.2, H_C - 0.7)
b.bbox('Brick_Red', XP2 - 1.8, XP2 - 0.6, yF - 0.06, yF, 5.2, H_C - 0.7)
cm = (XP1 + XP2) / 2
b.bbox('Stucco_Shade', XP1 + 1.9, XP2 - 1.9, yF - 0.25, yF - 0.02, 5.3, 10.9)   # frame
b.bbox('Billboard', XP1 + 2.2, XP2 - 2.2, yF - 0.32, yF - 0.22, 5.7, 10.5)
b.text('Sign_Text', 'THE RITZY CINEMA', cm, yF - 0.35, 8.8, 0.62, extrude=0.05)
b.text('Sign_Text', 'BRIXTON OVAL', cm, yF - 0.35, 7.7, 0.62, extrude=0.05)
b.text('Sign_Text', 'NOW SHOWING', cm, yF - 0.35, 6.3, 0.5, extrude=0.05)
b.profile_x('Stucco', seg_pts(XP1 + 0.3, XP2 - 0.3, H_C + 0.15, 3.0), yF - 0.3, yF + 1.0)
b.profile_x('Stucco_Shade', seg_pts(XP1 + 1.0, XP2 - 1.0, H_C + 0.3, 2.3), yF - 0.38, yF - 0.28)
b.profile_x('Stucco', seg_pts(XP1 + 2.2, XP2 - 2.2, H_C + 0.4, 1.5), yF - 0.46, yF - 0.36)
pts = [(cm + 0.8 * math.cos(2 * math.pi * i / 18), H_C + 2.3 + 0.8 * math.sin(2 * math.pi * i / 18)) for i in range(18)]
b.profile_x('Stucco_Shade', pts, yF - 0.56, yF - 0.44)
# the two small cherub panels ('EP') as raised plaques either side of billboard
for x in (XP1 + 1.2, XP2 - 1.2):
    b.bbox('Stucco_Shade', x - 0.4, x + 0.4, yF - 0.14, yF - 0.04, 9.4, 10.6)

# ---- canopy, doors, neon
b.bbox('Canopy_Dark', XP1 - 1.6, XP2 + 1.4, yF - 1.5, yF, 4.0, 4.9)
b.bbox('Glass_Lit', XP1 - 1.5, XP2 + 1.3, yF - 1.52, yF - 1.5, 4.05, 4.2)   # light strip
b.text('Neon_Red', 'RITZY', cm, yF - 1.55, 4.2, 0.62, extrude=0.06)
b.bbox('Sign_Text', XP2 + 0.2, XP2 + 1.2, yF - 1.55, yF - 1.5, 4.25, 4.75)   # 'BAR' plate
b.text('Billboard', 'BAR', XP2 + 0.7, yF - 1.56, 4.35, 0.32, extrude=0.03)
# red double doors
for k in range(4):
    x = XP1 + 1.8 + k * 2.2
    b.bbox('Door_Red', x - 0.9, x + 0.9, yF - 0.1, yF, 0.2, 3.7)
    b.bbox('Glass_Lit', x - 0.7, x + 0.7, yF - 0.14, yF - 0.1, 1.0, 3.4)
    b.bbox('Stucco_Shade', x - 0.03, x + 0.03, yF - 0.18, yF - 0.1, 1.0, 3.4)
# roof-top red neon RITZY on the left pavilion
b.bbox('Canopy_Dark', xL + 0.5, XP1 - 0.5, yF - 0.05, yF + 0.6, H_C + 2.7, H_C + 3.0)
b.text('Neon_Red', 'RITZY', (xL + XP1) / 2, yF + 0.05, H_C + 3.0, 1.5, extrude=0.1)

# ---------------------------------------------------------------- annex (round-arched door, CINEMA blade sign)
b.bbox('Stucco', XM, XA, yF, yB, 0, H_ANX)
b.bbox('Stucco_Shade', XM - 0.05, XA + 0.05, yF - 0.3, yF + 0.1, H_ANX - 0.5, H_ANX + 0.2)
b.bbox('Stucco_Shade', XM - 0.05, XA + 0.05, yF - 0.15, yF + 0.05, 4.7, 5.1)
b.bbox('Brick_Red', XM + 0.7, XM + 1.4, yF - 0.06, yF, 5.2, H_ANX - 0.6)
b.bbox('Brick_Red', XA - 1.4, XA - 0.7, yF - 0.06, yF, 5.2, H_ANX - 0.6)
am = (XM + XA) / 2
b.arch('Stucco_Shade', am, yF, 0.0, 3.6, 4.8, depth=0.25, pointed=False, face='-Y')
b.arch('Door_Red', am, yF - 0.15, 0.0, 3.0, 4.2, depth=0.12, pointed=False, face='-Y')
b.arch('Glass_Lit', am, yF - 0.22, 0.6, 2.4, 3.4, depth=0.08, pointed=False, face='-Y')
b.bbox('Stucco', am - 0.3, am + 0.3, yF - 0.3, yF, 4.6, 5.2)
b.arch('Stucco_Shade', am, yF, 5.6, 1.8, 2.4, depth=0.12, pointed=False, face='-Y')
b.arch('Glass_Lit', am, yF - 0.08, 5.8, 1.4, 2.0, depth=0.08, pointed=False, face='-Y')
# vertical CINEMA blade sign
b.bbox('Sign_Blue', XM + 0.15, XM + 0.95, yF - 1.0, yF - 0.2, 4.4, 10.8)
b.text('Sign_Text', 'C\nI\nN\nE\nM\nA', XM + 0.55, yF - 1.02, 4.8, 0.78, extrude=0.06, spacing=1.15)

# ---------------------------------------------------------------- modern glazed foyer extension
GX0, GX1 = XA, xR
b.bbox('Glass_Frame', GX0, GX1, -4.7, yB, 0, 12.6)
# chamfer-ish corner: just clip with a sloped panel on the SE
b.bbox('Glass_Frame', GX0, GX1, -4.75, -4.7, 0, 12.6)
for fl in range(3):
    z0 = 0.4 + fl * 4.1
    cnt = 6
    for i in range(cnt):
        x = GX0 + 0.5 + i * ((GX1 - GX0 - 1.0) / cnt)
        wpane = (GX1 - GX0 - 1.0) / cnt - 0.25
        m = 'Glass_Lit' if rng.random() < 0.55 else 'Glass_Dark'
        b.bbox(m, x, x + wpane, -4.8, -4.75, z0, z0 + 3.6)
for x in [GX0 + 0.35 + i * ((GX1 - GX0 - 1.0) / 6) for i in range(7)]:
    b.bbox('Stucco_Shade', x - 0.07, x + 0.07, -4.9, -4.7, 0, 12.6)
for z in (4.1, 8.2, 12.3):
    b.bbox('Stucco_Shade', GX0, GX1, -4.88, -4.7, z, z + 0.25)
b.text('Neon_Red', 'RITZY', (GX0 + GX1) / 2, -4.95, 9.6, 1.1, extrude=0.08)
b.bbox('Canopy_Dark', GX0, GX1, -4.9, -4.7, 12.6, 13.3)

# ---------------------------------------------------------------- rear/side: nine round-headed arches with keystones (blind)
bays = 9
wspan = (XM - xL)
for i in range(bays):
    cx = xL + wspan * (i + 0.5) / bays
    b.arch('Brick_Back', cx, yB, 1.0, 2.2, 8.6, depth=0.12, pointed=False, face='+Y')
    b.arch('Stucco_Shade', cx, yB + 0.1, 1.0, 1.6, 8.0, depth=0.06, pointed=False, face='+Y')
    b.bbox('Stucco', cx - 0.2, cx + 0.2, yB, yB + 0.2, 9.0, 9.7)
for i in range(bays + 1):
    x = xL + wspan * i / bays
    b.bbox('Stucco_Shade', x - 0.25, x + 0.25, yB, yB + 0.3, 0, H_C - 0.6)
b.bbox('Stucco_Shade', xL, XM, yB, yB + 0.4, H_C - 0.9, H_C - 0.5)
# annex/extension rear
b.bbox('Brick_Back', XM, xR, yB, yB + 0.05, 0, 12.6)

b.finish('ritzy', footprint=FOOT['ritzy']['footprint_bbox_m'],
         notes='Ritzy Cinema, Brixton Oval (1911, Grade II). White stucco front with red brick panels, two shaped-gable pavilions with roundels + big segmental pediment over a black '
               'billboard, dark canopy with red neon RITZY, red doors, stucco annex with CINEMA blade sign, modern glazed foyer extension at the east end.',
         cams={
             'front34': (Vector((-0.55, -1.0, 0.25)), 1.0),
             'front34b': (Vector((0.6, -1.0, 0.25)), 1.0),
             'rear34': (Vector((0.6, 1.0, 0.4)), 1.0),
             'front': (Vector((0.0, -1.0, 0.1)), 1.0, wpt(THETA, -12, -5, 6), 22),
             'side': (Vector((1.0, -0.1, 0.2)), 1.0),
             'top': (Vector((0.12, -0.5, 1.4)), 1.0),
         })
