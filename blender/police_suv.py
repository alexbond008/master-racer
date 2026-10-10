"""Met Police armed-response SUV (Range Rover L322 / XC90 style), near-black Paint -> public/models/cars/suv.glb
Run: blender -b --python police_suv.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import police_common as pc
from police_common import *

spec = dict(
    name='suv', L=4.95, W=2.00, wb=2.92, fo=0.98, r=0.40, rim_r=0.255, tyre_w=0.285, spokes=5, arch_gap=0.06,
    paint_kw=dict(paint=(0.012, 0.014, 0.022), paint_rough=0.22, paint_metal=0.6),
    hw=0.93, tumble=0.04, inset=0.07, lean=0.13, crown=0.014,
    plan_rf=0.35, plan_rr=0.30, plan_minf=0.80, plan_minr=0.84,
    stations=[0.0, 0.03, 0.08, 0.18, 0.35, 0.7, 1.2, 1.7, 2.0, 2.1, 2.3, 2.5, 2.7, 2.9, 3.2, 3.8, 4.4, 4.55, 4.7, 4.8, 4.88, 4.93, 4.95],
    ztop=[(0, 0.97), (0.05, 1.03), (0.2, 1.07), (0.8, 1.095), (1.6, 1.12), (2.05, 1.14), (2.5, 1.42), (2.9, 1.70),
          (3.2, 1.715), (4.4, 1.712), (4.7, 1.665), (4.88, 1.50), (4.95, 1.30)],
    zs=[(0, 0.86), (0.05, 0.94), (0.2, 0.99), (0.8, 1.015), (1.6, 1.04), (2.05, 1.06), (2.5, 1.25), (2.8, 1.29), (4.4, 1.30),
        (4.8, 1.27), (4.95, 1.15)],
    zb=[(0, 0.52), (0.03, 0.43), (0.08, 0.35), (0.2, 0.29), (0.6, 0.255), (1.2, 0.25), (4.0, 0.25), (4.5, 0.29), (4.8, 0.36),
        (4.95, 0.46)],
)

car = Car(spec)
body = car.build_loft()
car.arch_cut(body)
car.build_wheels()

car.refresh_surface(('body',))
car.add_glass(
    side_windows=[
        [(2.40, 1.31), (2.95, 1.665), (3.65, 1.67), (3.67, 1.31)],
        [(3.80, 1.31), (3.80, 1.67), (4.50, 1.66), (4.66, 1.58), (4.66, 1.31)],
    ],
    windscreen=[(-0.70, 2.16), (0.70, 2.16), (0.61, 2.88), (-0.61, 2.88)],
    rear_window=None,
)
F = car.front_mapper(); Rr = car.rear_mapper(); T = car.top_mapper()
FD, RD, TD = (0, 1, 0), (0, -1, 0), (0, 0, -1)
car.patch('glass', 'Glass', chaikin([(-0.62, 1.30), (0.62, 1.30), (0.58, 1.60), (-0.58, 1.60)], 2), Rr, RD, offset=0.006, maxlen=0.07)
car.refresh_surface(('body', 'glass'))

by0, by1 = 0.98 + 0.47, 0.98 + 2.92 - 0.47
car.side_band(by0, by1, 0.52, 0.16, rows=2, tilelen=0.28)
car.back_band(0.74, 0.46, 0.11, rows=2, tilelen=0.25)
car.side_sill(by0, by1, 0.27, 0.34)
for yy, z0 in ((2.36, 0.30), (3.72, 0.30), (4.55, 0.92)):
    car.door_line(yy, z0, 1.29)
car.handle(3.25, 1.18, 0.16); car.handle(4.2, 1.18, 0.16)
car.mirror(2.40, 0.93, 1.25, w=0.15, d=0.11, h=0.12)

# front: wide lamps, mesh grille, lower intake, plate
hs = rrect(0.43, 0.86, 0.79, 0.925, 1)
for pts in (hs, mirror_x(hs)):
    car.surround(pts, F, FD, 1.06, offset=0.006)
    car.patch('lights', 'HeadLight', rrect(*(min(a for a, b in pts) + 0.02, max(a for a, b in pts) - 0.02, 0.805, 0.91), 1), F, FD, offset=0.012, maxlen=0.022)
car.patch('chrome', 'Chrome', rrect(-0.40, 0.40, 0.725, 0.93, 1), F, FD, offset=0.006, maxlen=0.03)
car.patch('trim', 'Trim', rrect(-0.375, 0.375, 0.745, 0.91, 1), F, FD, offset=0.009, maxlen=0.05)
for x0, x1 in ((0.07, 0.30), (-0.30, -0.07)):
    car.patch('strobes', 'Light_Blue', rect(x0, x1, 0.80, 0.83), F, FD, offset=0.014, maxlen=0.022)
car.patch('trim', 'Trim', rrect(-0.62, 0.62, 0.50, 0.70, 1), F, FD, offset=0.005, maxlen=0.05)
car.patch('plates', 'Plate', rrect(-0.255, 0.255, 0.565, 0.675, 1), F, FD, offset=0.011, maxlen=0.035)
for x in (0.72, -0.72):
    car.patch('lights', 'HeadLight', ellipse(x, 0.60, 0.065, 0.045, 12), F, FD, offset=0.01, maxlen=0.022)

# rear
tl = [(0.67, 0.80), (0.86, 0.80), (0.90, 0.86), (0.90, 1.15), (0.86, 1.19), (0.69, 1.17)]
for pts in (tl, mirror_x(tl)):
    car.surround(chaikin(pts, 1), Rr, RD, 1.10, offset=0.006)
    car.patch('lights', 'TailLight', chaikin(pts, 1), Rr, RD, offset=0.011, maxlen=0.035)
car.patch('plates', 'Plate', rrect(-0.255, 0.255, 0.53, 0.64, 1), Rr, RD, offset=0.011, maxlen=0.035)
car.patch('trim', 'Trim', rect(-0.82, 0.82, 0.40, 0.44), Rr, RD, offset=0.004, maxlen=0.05)
for x in (0.40, -0.40):
    car.patch('strobes', 'Light_Blue', rect(x - 0.10, x + 0.10, 1.52, 1.56), Rr, RD, offset=0.012, maxlen=0.03)

car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.90, T, TD, lambda lx, ly: (lx, 1.25 + ly), mirror=True)
car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.70, Rr, RD, lambda lx, ly: (-lx, 0.93 + ly))
for sx in (1, -1):
    car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.92, car.side_mapper(sx), (-sx, 0, 0),
             (lambda lx, ly, sx=sx: (3.15 + sx * lx, 0.99 + ly)))

car.lightbar(3.55, 1.30, 0.30)
car.finalize()
print('tris', car.tri_count())
path = car.export()
car.verify_and_render(path)
