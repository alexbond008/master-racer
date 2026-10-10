"""Met Police BMW 5-series (E39/E60-style) saloon pursuit car -> public/models/cars/interceptor.glb
Run: blender -b --python police_interceptor.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import police_common as pc
from police_common import *

spec = dict(
    name='interceptor', L=4.85, W=1.85, wb=2.89, fo=0.90, r=0.33, rim_r=0.215, tyre_w=0.235, spokes=5, arch_gap=0.035,
    hw=0.855, tumble=0.04, inset=0.09, lean=0.24, crown=0.02,
    plan_rf=0.46, plan_rr=0.40, plan_minf=0.64, plan_minr=0.72,
    stations=[0.0, 0.03, 0.08, 0.16, 0.3, 0.5, 0.8, 1.2, 1.6, 1.9, 2.05, 2.2, 2.4, 2.6, 2.8, 3.0, 3.3, 3.55, 3.75, 3.95, 4.1, 4.2, 4.4, 4.6, 4.72, 4.79, 4.83, 4.85],
    ztop=[(0, 0.625), (0.05, 0.69), (0.2, 0.765), (0.6, 0.82), (1.2, 0.86), (1.8, 0.895), (2.05, 0.925), (2.4, 1.15),
          (2.75, 1.37), (3.0, 1.385), (3.55, 1.375), (3.85, 1.25), (4.1, 1.015), (4.2, 0.985), (4.5, 0.985), (4.72, 0.96), (4.85, 0.85)],
    zs=[(0, 0.53), (0.05, 0.60), (0.2, 0.67), (0.6, 0.73), (1.2, 0.77), (1.8, 0.805), (2.05, 0.84), (2.3, 0.93), (2.6, 0.965),
        (3.5, 0.985), (3.9, 0.975), (4.1, 0.93), (4.2, 0.895), (4.5, 0.895), (4.72, 0.87), (4.85, 0.77)],
    zb=[(0, 0.34), (0.03, 0.29), (0.08, 0.235), (0.2, 0.195), (0.6, 0.165), (1.2, 0.152), (3.5, 0.152), (4.2, 0.19), (4.6, 0.24),
        (4.85, 0.34)],
)

car = Car(spec)
body = car.build_loft()
car.arch_cut(body)
car.build_wheels()

car.refresh_surface(('body',))
car.add_glass(
    side_windows=[
        [(2.28, 0.99), (2.70, 1.30), (3.26, 1.305), (3.28, 0.99)],
        [(3.42, 0.99), (3.42, 1.305), (3.78, 1.28), (4.02, 1.05), (4.04, 0.99)],
    ],
    windscreen=[(-0.67, 2.10), (0.67, 2.10), (0.57, 2.72), (-0.57, 2.72)],
    rear_window=[(-0.53, 3.60), (0.53, 3.60), (0.60, 4.10), (-0.60, 4.10)],
)
car.refresh_surface(('body', 'glass'))
F = car.front_mapper(); Rr = car.rear_mapper(); T = car.top_mapper()
FD, RD, TD = (0, 1, 0), (0, -1, 0), (0, 0, -1)

by0, by1 = 0.90 + 0.41, 0.90 + 2.89 - 0.41
car.side_band(by0, by1, 0.40, 0.14, rows=2, tilelen=0.25)
car.back_band(0.70, 0.38, 0.11, rows=2, tilelen=0.22)
car.side_sill(by0, by1, 0.17, 0.235)
for yy, z0 in ((1.95, 0.25), (3.30, 0.25), (3.95, 0.74)):
    car.door_line(yy, z0, 0.975)
car.handle(2.95, 0.90); car.handle(3.62, 0.90)
car.mirror(2.22, 0.86, 0.95)

# front: quad headlights, kidney grilles, intake, plate
hs = rrect(0.30, 0.665, 0.535, 0.665, 1)
for pts in (hs, mirror_x(hs)):
    car.surround(pts, F, FD, 1.06, offset=0.006)
for cx in (0.385, 0.52, -0.385, -0.52):
    car.patch('lights', 'HeadLight', ellipse(cx, 0.60, 0.052, 0.052, 14), F, FD, offset=0.012, maxlen=0.022)
for sx in (1, -1):
    kid = [(0.025, 0.505), (0.225, 0.505), (0.245, 0.575), (0.215, 0.645), (0.025, 0.645)]
    kid = [(sx * a, b) for a, b in kid]
    if sx < 0:
        kid = kid[::-1]
    kk = chaikin(kid, 1)
    car.surround(kk, F, FD, 1.16, offset=0.003) if False else None
    cx_ = sum(p[0] for p in kk) / len(kk); cy_ = sum(p[1] for p in kk) / len(kk)
    car.patch('chrome', 'Chrome', [(cx_ + (a - cx_) * 1.12, cy_ + (b - cy_) * 1.12) for a, b in kk], F, FD, offset=0.006, maxlen=0.03)
    car.patch('trim', 'Trim', kk, F, FD, offset=0.009, maxlen=0.05)
    car.patch('strobes', 'Light_Blue', rect(min(sx * 0.06, sx * 0.20), max(sx * 0.06, sx * 0.20), 0.60, 0.625), F, FD, offset=0.014, maxlen=0.022)
car.patch('trim', 'Trim', rrect(-0.66, 0.66, 0.235, 0.335, 1), F, FD, offset=0.004, maxlen=0.05)
car.patch('plates', 'Plate', rrect(-0.255, 0.255, 0.37, 0.48, 1), F, FD, offset=0.011, maxlen=0.035)
for x in (0.55, -0.55):
    car.patch('lights', 'HeadLight', ellipse(x, 0.285, 0.05, 0.035, 12), F, FD, offset=0.007, maxlen=0.022)

# rear
tl = [(0.47, 0.67), (0.76, 0.67), (0.81, 0.70), (0.81, 0.79), (0.76, 0.82), (0.50, 0.80)]
for pts in (tl, mirror_x(tl)):
    car.surround(chaikin(pts, 1), Rr, RD, 1.10)
    car.patch('lights', 'TailLight', chaikin(pts, 1), Rr, RD, offset=0.005, maxlen=0.022)
car.patch('plates', 'Plate', rrect(-0.255, 0.255, 0.46, 0.57, 1), Rr, RD, offset=0.011, maxlen=0.035)
car.patch('trim', 'Trim', rect(-0.78, 0.78, 0.335, 0.375), Rr, RD, offset=0.004, maxlen=0.05)
for x in (0.38, -0.38):
    car.patch('strobes', 'Light_Blue', rect(x - 0.09, x + 0.09, 3.62, 3.67), T, TD, offset=0.009)

car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.70, T, TD, lambda lx, ly: (lx, 1.12 + ly), mirror=True)
car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.62, Rr, RD, lambda lx, ly: (-lx, 0.755 + ly))
for sx in (1, -1):
    car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.72, car.side_mapper(sx), (-sx, 0, 0),
             (lambda lx, ly, sx=sx: (2.45 + sx * lx, 0.845 + ly)))

car.lightbar(3.10, 1.20, 0.29)
car.finalize()
print('tris', car.tri_count())
path = car.export()
car.verify_and_render(path)
