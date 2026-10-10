import json, math
d=json.load(open('landmark_footprints.json'))
def fit(poly):
    best=None
    for i in range(len(poly)):
        a=poly[i]; b=poly[(i+1)%len(poly)]
        th=math.atan2(b[1]-a[1],b[0]-a[0])
        c,s=math.cos(-th),math.sin(-th)
        pts=[(x*c-y*s,x*s+y*c) for x,y in poly]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        area=(max(xs)-min(xs))*(max(ys)-min(ys))
        if best is None or area<best[0]: best=(area,th,min(xs),max(xs),min(ys),max(ys))
    area,th,x0,x1,y0,y1=best
    # normalise angle to (-45,45]
    deg=math.degrees(th)
    while deg>45: deg-=90
    while deg<=-45: deg+=90
    th=math.radians(deg)
    c,s=math.cos(-th),math.sin(-th)
    pts=[(x*c-y*s,x*s+y*c) for x,y in poly]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    cx=(max(xs)+min(xs))/2; cy=(max(ys)+min(ys))/2
    # centre in world
    wx=cx*math.cos(th)-cy*math.sin(th); wy=cx*math.sin(th)+cy*math.cos(th)
    return deg, max(xs)-min(xs), max(ys)-min(ys), (wx,wy), area
for k in ['library','levels','bussey','peckham_station','clock']:
    p=d[k]['polygon_blender_xy']
    deg,w,h,c,a=fit(p)
    print(k, 'yaw=%.1f w=%.1f d=%.1f centre=(%.1f,%.1f) rectarea=%.0f'%(deg,w,h,c[0],c[1],a))
