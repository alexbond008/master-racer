import * as THREE from 'three';

// London street furniture along the real road graph (see research/london.md section 5). Decorative, no collision.
export function buildFurniture(group, net, rnd, { inPark, occ }) {
  const tmp = new THREE.Object3D();
  const inst = (geo, mat, list, setup) => {
    if (!list.length) return null;
    const m = new THREE.InstancedMesh(geo, mat, list.length);
    list.forEach((it, i) => { tmp.position.set(0, 0, 0); tmp.rotation.set(0, 0, 0); tmp.scale.set(1, 1, 1); setup(tmp, it); tmp.updateMatrix(); m.setMatrixAt(i, tmp.matrix); });
    group.add(m); return m;
  };
  const free = (x, z) => !occ(x, z) && !inPark(x, z);
  // point beside the road: side +1 = left of travel (dir 1), `off` metres from the centreline
  const beside = (e, s, side, off) => { const p = net.pointAt(e, 1, s); return { x: p.x + p.tz * side * off, z: p.z - p.tx * side * off, th: Math.atan2(p.tx, p.tz), tx: p.tx, tz: p.tz }; };

  const lamps = [], stripes = [], beacons = [], shelters = [], flags = [], phones = [], pillars = [], signals = [];
  let alt = 0;
  for (const e of net.edges) {
    if (e.bridge || e.len < 12) continue;
    const main = e.cls <= 2, gap = main ? 30 : 42;
    // ---- lamp posts, alternating sides
    for (let s = 8 + rnd() * gap * 0.5; s < e.len - 6; s += gap) {
      const side = (alt++ % 2) ? 1 : -1, p = beside(e, s, side, e.width / 2 + 1.1);
      if (free(p.x, p.z)) lamps.push([p.x, p.z]);
    }
    if (!main) continue;
    // ---- zebra crossing (about one in four long main-road edges)
    if (e.len > 70 && ((e.id * 7) % 4 === 0)) {
      const s = e.len * (0.35 + ((e.id * 13) % 30) / 100), c = net.pointAt(e, 1, s), th = Math.atan2(c.tx, c.tz);
      for (let o = -e.width / 2 + 0.7; o <= e.width / 2 - 0.5; o += 1.0) stripes.push([c.x + c.tz * o, c.z - c.tx * o, th]);
      for (const side of [-1, 1]) { const p = beside(e, s, side, e.width / 2 + 0.9); beacons.push([p.x, p.z]); }
    }
    // ---- bus stops along the A23 spine
    if (e.a23 && e.len > 90) {
      const s = e.len * 0.5, side = e.id % 2 ? 1 : -1, p = beside(e, s, side, e.width / 2 + 2.1), f = beside(e, s - 4, side, e.width / 2 + 1.0);
      if (free(p.x, p.z)) { shelters.push([p.x, p.z, p.th]); flags.push([f.x, f.z]); }
    }
    // ---- phone box / pillar box on shopping streets
    if (rnd() < 0.18) { const p = beside(e, e.len * (0.2 + rnd() * 0.6), rnd() < 0.5 ? 1 : -1, e.width / 2 + 1.0); if (free(p.x, p.z)) (rnd() < 0.4 ? phones : pillars).push([p.x, p.z]); }
  }
  // ---- traffic signals at junctions of main roads (decorative; cars ignore them)
  net.nodes.forEach(n => {
    const mains = n.out.filter(o => o.e.cls <= 2); if (mains.length < 3) return;
    for (const o of mains.slice(0, 4)) {
      const p = net.pointAt(o.e, o.dir, 0), w = o.e.width, d = w / 2 + 3.5;
      const x = n.x + p.tx * d - p.tz * (-1) * 0 + (-p.tz) * (w / 2 + 0.8), z = n.z + p.tz * d + p.tx * (w / 2 + 0.8);
      if (free(x, z)) signals.push([x, z, (x * 7 + z * 3) % 3 | 0]);
    }
  });

  // ---- instanced meshes
  const lampPole = new THREE.CylinderGeometry(0.08, 0.12, 7, 6); lampPole.translate(0, 3.5, 0);
  inst(lampPole, new THREE.MeshStandardMaterial({ color: 0x22252a, roughness: 0.7 }), lamps, (o, l) => o.position.set(l[0], 0, l[1]));
  inst(new THREE.SphereGeometry(0.34, 8, 6), new THREE.MeshBasicMaterial({ color: new THREE.Color(4.2, 2.6, 0.8) }), lamps, (o, l) => o.position.set(l[0], 7.1, l[1]));

  const flat = new THREE.PlaneGeometry(1, 1); flat.rotateX(-Math.PI / 2);
  inst(flat, new THREE.MeshStandardMaterial({ color: 0xeeeeee, roughness: 0.7, polygonOffset: true, polygonOffsetFactor: -4 }), stripes, (o, s) => { o.position.set(s[0], 0.04, s[1]); o.rotation.y = s[2]; o.scale.set(0.5, 1, 3.2); });
  const bp = new THREE.CylinderGeometry(0.07, 0.07, 3, 6); bp.translate(0, 1.5, 0);
  inst(bp, new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: 0.6 }), beacons, (o, b) => o.position.set(b[0], 0.12, b[1]));
  inst(new THREE.SphereGeometry(0.3, 10, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 2.6, 0.2) }), beacons, (o, b) => o.position.set(b[0], 3.35, b[1]));
  const bands = []; beacons.forEach(b => [0.6, 1.4, 2.2].forEach(y => bands.push([b[0], y, b[1]])));
  inst(new THREE.CylinderGeometry(0.09, 0.09, 0.28, 8), new THREE.MeshStandardMaterial({ color: 0x111111 }), bands, (o, b) => o.position.set(b[0], b[1], b[2]));

  const sigPole = new THREE.CylinderGeometry(0.09, 0.11, 3.4, 6); sigPole.translate(0, 1.7, 0);
  inst(sigPole, new THREE.MeshStandardMaterial({ color: 0x2a2d32 }), signals, (o, a) => o.position.set(a[0], 0, a[1]));
  inst(new THREE.BoxGeometry(0.34, 1.0, 0.34), new THREE.MeshStandardMaterial({ color: 0x0e0e10 }), signals, (o, a) => o.position.set(a[0], 3.7, a[1]));
  const cols = [new THREE.Color(5, 0.2, 0.15), new THREE.Color(5, 2.4, 0.1), new THREE.Color(0.2, 5, 0.6)];
  for (let c = 0; c < 3; c++) inst(new THREE.SphereGeometry(0.13, 8, 6), new THREE.MeshBasicMaterial({ color: cols[c] }), signals.filter(a => a[2] === c), (o, a) => o.position.set(a[0], c === 0 ? 3.98 : c === 1 ? 3.7 : 3.42, a[1]));

  inst(new THREE.BoxGeometry(1.4, 2.4, 3.4), new THREE.MeshStandardMaterial({ color: 0x9fd7e8, transparent: true, opacity: 0.35, roughness: 0.1 }), shelters, (o, s) => { o.position.set(s[0], 1.3, s[1]); o.rotation.y = s[2]; });
  inst(new THREE.BoxGeometry(1.6, 0.12, 3.6), new THREE.MeshStandardMaterial({ color: 0x20242b }), shelters, (o, s) => { o.position.set(s[0], 2.55, s[1]); o.rotation.y = s[2]; });
  const fp = new THREE.CylinderGeometry(0.04, 0.04, 2.6, 6); fp.translate(0, 1.3, 0);
  inst(fp, new THREE.MeshStandardMaterial({ color: 0xcccccc }), flags, (o, f) => o.position.set(f[0], 0, f[1]));
  inst(new THREE.CylinderGeometry(0.3, 0.3, 0.05, 20), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.4, 0.15, 0.15) }), flags, (o, f) => { o.position.set(f[0], 2.4, f[1]); o.rotation.x = Math.PI / 2; });

  inst(new THREE.BoxGeometry(0.95, 2.51, 0.95), new THREE.MeshStandardMaterial({ color: 0xc41e1e, roughness: 0.5 }), phones, (o, p) => o.position.set(p[0], 1.25, p[1]));
  inst(new THREE.BoxGeometry(0.7, 2.0, 0.7), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.2, 1.1, 0.8), transparent: true, opacity: 0.35 }), phones, (o, p) => o.position.set(p[0], 1.3, p[1]));
  inst(new THREE.CylinderGeometry(0.3, 0.3, 1.5, 12), new THREE.MeshStandardMaterial({ color: 0xb01818, roughness: 0.55 }), pillars, (o, p) => o.position.set(p[0], 0.75, p[1]));

  return { lamps: lamps.length, crossings: beacons.length / 2, signals: signals.length, stops: shelters.length };
}
