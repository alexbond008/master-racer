import * as THREE from 'three';
import { CELL, ROAD, BLOCK, N } from './world.js';

// London street furniture, all instanced (see research/london.md section 5). Decorative only; no collision.
export const BUS_ROADS = [{ i: 8, a: 3, b: 21 }, { i: 17, a: 4, b: 12 }]; // vertical roads that get red bus lanes (A23 spine, Rye Lane)

export function buildFurniture(group, rnd) {
  const tmp = new THREE.Object3D();
  const inst = (geo, mat, list, setup) => {
    if (!list.length) return null;
    const m = new THREE.InstancedMesh(geo, mat, list.length);
    list.forEach((it, i) => { setup(tmp, it); tmp.updateMatrix(); m.setMatrixAt(i, tmp.matrix); });
    group.add(m); return m;
  };
  const flat = new THREE.PlaneGeometry(1, 1); flat.rotateX(-Math.PI / 2);
  const isBus = (i, j) => BUS_ROADS.some(b => b.i === i && j >= b.a && j < b.b);

  // ---- zebra crossings + Belisha beacons (mid-block, ~1 in 7 segments)
  const stripes = [], beacons = [];
  for (let axis = 0; axis < 2; axis++) for (let i = 1; i < N; i++) for (let j = 0; j < N; j++) {
    if ((i * 5 + j * 3 + axis * 2) % 7 !== 0) continue;
    const along = j * CELL + CELL / 2;                     // mid-block position along the road
    const stripeCount = 18;
    for (let k = 0; k < stripeCount; k++) {
      const off = -ROAD / 2 + 0.75 + k * ((ROAD - 1.5) / (stripeCount - 1));
      if (axis === 0) stripes.push([i * CELL + off, along, 0.5, 3.2]); else stripes.push([along, i * CELL + off, 3.2, 0.5]);
    }
    for (const s of [-1, 1]) beacons.push(axis === 0 ? [i * CELL + s * (ROAD / 2 + 0.8), along] : [along, i * CELL + s * (ROAD / 2 + 0.8)]);
  }
  inst(flat, new THREE.MeshStandardMaterial({ color: 0xeeeeee, roughness: 0.7 }), stripes, (o, s) => { o.position.set(s[0], 0.035, s[1]); o.scale.set(s[2], 1, s[3]); o.rotation.set(0, 0, 0); });
  const poleG = new THREE.CylinderGeometry(0.07, 0.07, 3, 6); poleG.translate(0, 1.5, 0);
  inst(poleG, new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: 0.6 }), beacons, (o, b) => { o.position.set(b[0], 0.2, b[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  inst(new THREE.SphereGeometry(0.3, 10, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 2.6, 0.2) }), beacons, (o, b) => { o.position.set(b[0], 3.35, b[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  const bandG = new THREE.CylinderGeometry(0.09, 0.09, 0.28, 8); // black bands on the pole
  const bands = []; beacons.forEach(b => [0.6, 1.4, 2.2].forEach(y => bands.push([b[0], y, b[1]])));
  inst(bandG, new THREE.MeshStandardMaterial({ color: 0x111111 }), bands, (o, b) => { o.position.set(b[0], b[1], b[2]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });

  // ---- double yellow lines along kerbs + red bus lanes
  const cv = document.createElement('canvas'); cv.width = 64; cv.height = 4; const cx = cv.getContext('2d');
  cx.clearRect(0, 0, 64, 4); cx.fillStyle = '#e8c21a'; cx.fillRect(10, 0, 18, 4); cx.fillRect(36, 0, 18, 4);
  const dyTex = new THREE.CanvasTexture(cv); dyTex.colorSpace = THREE.SRGBColorSpace;
  const dy = [], red = [];
  for (let axis = 0; axis < 2; axis++) for (let i = 0; i <= N; i++) for (let j = 0; j < N; j++) {
    const start = j * CELL + ROAD / 2 + BLOCK / 2;
    for (const s of [-1, 1]) {
      const entry = axis === 0 ? [i * CELL + s * (ROAD / 2 - 0.45), start] : [start, i * CELL + s * (ROAD / 2 - 0.45)];
      if (axis === 0 && isBus(i, j)) red.push([i * CELL + s * 7.4, start, 3.2, BLOCK]);
      else dy.push([...entry, axis]);
    }
  }
  const dyMat = new THREE.MeshBasicMaterial({ map: dyTex, transparent: true, color: new THREE.Color(0.9, 0.9, 0.9), depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 });
  // texture stripes run across u, so z-running lines use it as is and x-running lines are rotated 90deg
  inst(flat, dyMat, dy, (o, d) => { o.position.set(d[0], 0.04, d[1]); o.scale.set(0.55, 1, BLOCK); o.rotation.set(0, d[2] === 0 ? 0 : Math.PI / 2, 0); });
  inst(flat, new THREE.MeshStandardMaterial({ color: 0x9c2326, roughness: 0.85 }), red, (o, r) => { o.position.set(r[0], 0.045, r[1]); o.scale.set(r[2], 1, r[3]); o.rotation.set(0, 0, 0); });

  // ---- traffic lights at every other junction (decorative; cars ignore them)
  const heads = [], arms = [];
  for (let i = 1; i < N; i++) for (let j = 1; j < N; j++) {
    if ((i + j) % 2) continue;
    for (const [sx, sz] of [[1, 1], [-1, -1]]) arms.push([i * CELL + sx * (ROAD / 2 + 1.2), j * CELL + sz * (ROAD / 2 + 1.2), (i * 3 + j) % 3]);
  }
  const lightPole = new THREE.CylinderGeometry(0.09, 0.11, 3.4, 6); lightPole.translate(0, 1.7, 0);
  inst(lightPole, new THREE.MeshStandardMaterial({ color: 0x2a2d32 }), arms, (o, a) => { o.position.set(a[0], 0, a[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  inst(new THREE.BoxGeometry(0.34, 1.0, 0.28), new THREE.MeshStandardMaterial({ color: 0x0e0e10 }), arms, (o, a) => { o.position.set(a[0], 3.7, a[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  const lampG = new THREE.SphereGeometry(0.11, 8, 6);
  const cols = [new THREE.Color(5, 0.2, 0.15), new THREE.Color(5, 2.4, 0.1), new THREE.Color(0.2, 5, 0.6)];
  for (let c = 0; c < 3; c++) {
    const list = arms.filter(a => a[2] === c);
    inst(lampG, new THREE.MeshBasicMaterial({ color: cols[c] }), list, (o, a) => { o.position.set(a[0], c === 0 ? 3.98 : c === 1 ? 3.7 : 3.42, a[1] + (a[1] % 128 > 64 ? -0.15 : 0.15)); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  }

  // ---- bus stops (glass shelter + red roundel flag) on the bus roads, ~every 4th block, alternating kerbs
  const shelters = [], flags = [];
  for (const b of BUS_ROADS) for (let j = b.a; j < b.b; j += 4) {
    const s = j % 8 < 4 ? 1 : -1, x = b.i * CELL + s * (ROAD / 2 + 1.6), z = j * CELL + CELL / 2 + 10;
    shelters.push([x + s * 0.6, z]); flags.push([x - s * 0.2, z - 3]);
  }
  inst(new THREE.BoxGeometry(1.4, 2.4, 3.4), new THREE.MeshStandardMaterial({ color: 0x9fd7e8, transparent: true, opacity: 0.35, roughness: 0.1 }), shelters, (o, s) => { o.position.set(s[0], 1.3, s[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  inst(new THREE.BoxGeometry(1.6, 0.12, 3.6), new THREE.MeshStandardMaterial({ color: 0x20242b }), shelters, (o, s) => { o.position.set(s[0], 2.55, s[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  const fp = new THREE.CylinderGeometry(0.04, 0.04, 2.6, 6); fp.translate(0, 1.3, 0);
  inst(fp, new THREE.MeshStandardMaterial({ color: 0xcccccc }), flags, (o, f) => { o.position.set(f[0], 0, f[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  inst(new THREE.CylinderGeometry(0.3, 0.3, 0.05, 20), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.4, 0.15, 0.15) }), flags, (o, f) => { o.position.set(f[0], 2.4, f[1]); o.rotation.set(Math.PI / 2, 0, 0); o.scale.set(1, 1, 1); });

  // ---- K6 phone boxes + pillar boxes on shopping-street sidewalks
  const phones = [], pillars = [];
  for (let n = 0; n < 70; n++) {
    const i = 1 + Math.floor(rnd() * (N - 1)), j = Math.floor(rnd() * N), side = rnd() < 0.5 ? 1 : -1;
    const x = i * CELL + side * (ROAD / 2 + 0.9), z = j * CELL + 14 + rnd() * (BLOCK - 28);
    (n % 3 ? pillars : phones).push([x, z]);
  }
  inst(new THREE.BoxGeometry(0.95, 2.51, 0.95), new THREE.MeshStandardMaterial({ color: 0xc41e1e, roughness: 0.5 }), phones, (o, p) => { o.position.set(p[0], 1.25, p[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  inst(new THREE.BoxGeometry(0.7, 2.0, 0.7), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.2, 1.1, 0.8), transparent: true, opacity: 0.35 }), phones, (o, p) => { o.position.set(p[0], 1.3, p[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });
  inst(new THREE.CylinderGeometry(0.3, 0.3, 1.5, 12), new THREE.MeshStandardMaterial({ color: 0xb01818, roughness: 0.55 }), pillars, (o, p) => { o.position.set(p[0], 0.75, p[1]); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); });

  return { zebra: stripes.length / 18, lights: arms.length, stops: shelters.length };
}
