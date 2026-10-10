import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { rnd, windowTextures } from './buildings.js';
import { OsmBuildings } from './osmbuildings.js';
import { buildFurniture } from './furniture.js';
import { RoadNet } from './roadnet.js';

// South London built from real OpenStreetMap roads (public/data/southlondon.json, © OpenStreetMap contributors, ODbL).
export const DISTRICTS = {
  brixton: { name: 'BRIXTON', c: [0, 0], tint: '#d9a441' },
  peckham: { name: 'PECKHAM', c: [0, 0], tint: '#e0602a' },
  streatham: { name: 'STREATHAM', c: [0, 0], tint: '#4aa86b' },
};
export const WORLD = { w: 3471, h: 4448 };
let NET = null;

export function districtAt(x, z) {
  let best = null, bd = Infinity;
  for (const k in DISTRICTS) { const [cx, cz] = DISTRICTS[k].c, d = Math.hypot(x - cx, z - cz); if (d < bd) { bd = d; best = k; } }
  return best;
}
export function roadNameAt(x, z) {
  if (!NET) return '';
  const n = NET.nearest(x, z, 16);
  return n && n.d <= n.e.width / 2 + 2 ? n.e.name : '';
}

const PALETTE = {
  brixton: ['#8b3a2b', '#a04a35', '#8d7d5c', '#d9a1b0', '#5bb3b0', '#e0b14a', '#6b3f3a', '#c9c1ae'],
  peckham: ['#8d7d5c', '#a38f64', '#8b3a2b', '#6f6a63', '#7d6a55', '#b2a98d', '#7a3226'],
  streatham: ['#9a4430', '#b5573f', '#d8d0bd', '#cfc5ae', '#8c6a4e', '#9b8f72'],
};
const BRIGHT = { brixton: ['#e63946', '#ffb703', '#2a9d8f', '#3a86ff', '#fb5607', '#06d6a0', '#ffd166'], peckham: ['#e63946', '#ffb703', '#2a9d8f', '#3a86ff', '#fb5607', '#8338ec', '#06d6a0', '#ffd166', '#ff4fa3'], streatham: ['#d62828', '#1d4e89', '#f4f4f4', '#2b9348', '#ffb703'] };
const TILE = 256, PAVE = 2.0;

// ---- geometry accumulators (one set per map tile so frustum culling works)
class Acc {
  constructor() { this.p = []; this.uv = []; this.i = []; }
  vert(x, y, z, u, v) { this.p.push(x, y, z); this.uv.push(u, v); return this.p.length / 3 - 1; }
  mesh(mat) {
    if (!this.i.length) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    const n = this.p.length / 3, nrm = new Float32Array(n * 3); for (let k = 0; k < n; k++) nrm[k * 3 + 1] = 1;
    g.setAttribute('normal', new THREE.BufferAttribute(nrm, 3)); g.setIndex(this.i); g.computeBoundingSphere();
    return new THREE.Mesh(g, mat);
  }
}
// strip along a polyline between left-offsets off0 < off1 (left of travel = (tz,-tx))
function ribbon(acc, pts, off0, off1, y, uvMode, dash = 8) {
  const n = pts.length; if (n < 2) return;
  const sn = [];
  for (let i = 0; i < n - 1; i++) { const dx = pts[i + 1][0] - pts[i][0], dz = pts[i + 1][1] - pts[i][1], l = Math.hypot(dx, dz) || 1; sn.push([dz / l, -dx / l]); }
  const ids = []; let s = 0;
  for (let i = 0; i < n; i++) {
    let nx, nz;
    if (i === 0) [nx, nz] = sn[0]; else if (i === n - 1) [nx, nz] = sn[n - 2];
    else { nx = sn[i - 1][0] + sn[i][0]; nz = sn[i - 1][1] + sn[i][1]; const l = Math.hypot(nx, nz) || 1; nx /= l; nz /= l; const m = 1 / Math.max(0.55, nx * sn[i][0] + nz * sn[i][1]); nx *= m; nz *= m; }
    if (i > 0) s += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    const [px, pz] = pts[i], lx = px + nx * off1, lz = pz + nz * off1, rx = px + nx * off0, rz = pz + nz * off0;
    const w = uvMode === 'world';
    ids.push([acc.vert(lx, y, lz, w ? lx * 0.1 : 1, w ? lz * 0.1 : s / dash), acc.vert(rx, y, rz, w ? rx * 0.1 : 0, w ? rz * 0.1 : s / dash)]);
  }
  for (let i = 0; i < n - 1; i++) { const [l0, r0] = ids[i], [l1, r1] = ids[i + 1]; acc.i.push(l0, r0, l1, r0, r1, l1); }
}
function disc(acc, x, z, r, y) {
  const c = acc.vert(y * 0 + x, y, z, x * 0.1, z * 0.1), seg = 14, ids = [];
  for (let k = 0; k < seg; k++) { const a = k / seg * Math.PI * 2, px = x + Math.cos(a) * r, pz = z + Math.sin(a) * r; ids.push(acc.vert(px, y, pz, px * 0.1, pz * 0.1)); }
  for (let k = 0; k < seg; k++) acc.i.push(c, ids[(k + 1) % seg], ids[k]);
}
const noiseTex = (base, spread) => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 256; const x = cv.getContext('2d');
  x.fillStyle = base; x.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 5000; i++) { const v = Math.random() * spread | 0; x.fillStyle = `rgba(${v},${v},${v},0.35)`; x.fillRect(Math.random() * 256, Math.random() * 256, 2, 2); }
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
};

export function buildWorld(scene, data, extra = {}) {
  const T0 = performance.now(), lap = n => console.log('[world]', n, Math.round(performance.now() - T0), 'ms');
  const net = new RoadNet(data); NET = net; lap('roadnet');
  WORLD.w = data.bounds[0]; WORLD.h = data.bounds[1];
  for (const k in DISTRICTS) DISTRICTS[k].c = data.places.districts[k];
  const group = new THREE.Group(); scene.add(group);
  const ctx = { bMat: null, update: [] };

  // ---------- materials (weather drives the ground materials)
  const tex = windowTextures();
  const bMat = new THREE.MeshStandardMaterial({ map: tex.map, emissiveMap: tex.emissive, emissive: 0xffffff, emissiveIntensity: 0.9, vertexColors: true, roughness: 0.85 });
  ctx.bMat = bMat;
  const concreteMat = new THREE.MeshStandardMaterial({ color: 0x8d8f91, roughness: 0.95, vertexColors: true });
  const asphalt = new THREE.MeshStandardMaterial({ map: noiseTex('#2a2a2e', 50), roughness: 0.82 });
  const pavement = new THREE.MeshStandardMaterial({ map: noiseTex('#5c5c60', 40), roughness: 0.9 });
  const backMat = new THREE.MeshStandardMaterial({ map: noiseTex('#222421', 20), roughness: 1 });
  const grassMat = new THREE.MeshStandardMaterial({ map: noiseTex('#2f5a2c', 40), roughness: 1 });
  const redMat = new THREE.MeshStandardMaterial({ color: 0x9c2326, roughness: 0.85, polygonOffset: true, polygonOffsetFactor: -2 });
  const dashTex = (() => { const cv = document.createElement('canvas'); cv.width = 8; cv.height = 64; const x = cv.getContext('2d'); x.fillStyle = '#ece6cc'; x.fillRect(0, 0, 8, 24); const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const markMat = new THREE.MeshBasicMaterial({ map: dashTex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3, color: new THREE.Color(0.85, 0.85, 0.8) });
  const paneTex = (() => { // shopfront glazing: bright panes in dark frames with a door, repeats every 2.6 m
    const cv = document.createElement('canvas'); cv.width = 128; cv.height = 64; const x = cv.getContext('2d');
    x.fillStyle = '#1a1612'; x.fillRect(0, 0, 128, 64);
    const g = x.createLinearGradient(0, 0, 0, 64); g.addColorStop(0, '#ffe2a8'); g.addColorStop(1, '#ffb866');
    x.fillStyle = g; x.fillRect(4, 4, 86, 56); x.fillStyle = '#ffd08a'; x.fillRect(96, 4, 28, 56); x.fillStyle = '#3a2c20'; x.fillRect(104, 40, 12, 3); x.fillRect(46, 4, 3, 56); x.fillStyle = '#ffffff'; x.fillRect(58, 61, 14, 3); // plain white patch the fascia strips sample
    const t = new THREE.CanvasTexture(cv); t.wrapS = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  const signMat = new THREE.MeshBasicMaterial({ vertexColors: true, map: paneTex });
  const groundMats = [asphalt, pavement, backMat, grassMat];

  const back = new THREE.Mesh(new THREE.PlaneGeometry(WORLD.w + 2400, WORLD.h + 2400), backMat);
  back.rotation.x = -Math.PI / 2; back.position.set(WORLD.w / 2, -0.02, WORLD.h / 2); group.add(back);

  // ---------- tiles
  const tiles = new Map();
  const tile = (x, z) => {
    const k = Math.floor(x / TILE) + ',' + Math.floor(z / TILE); let t = tiles.get(k);
    if (!t) tiles.set(k, t = { road: new Acc(), pave: new Acc(), mark: new Acc(), red: new Acc(), bld: [], con: [], sign: [] });
    return t;
  };
  const slice = (e, s0, s1) => {
    const pts = [], a = net.pointAt(e, 1, s0), b = net.pointAt(e, 1, s1); pts.push([a.x, a.z]);
    for (let i = 1; i < e.pts.length - 1; i++) if (e.cum[i] > s0 + 0.5 && e.cum[i] < s1 - 0.5) pts.push(e.pts[i]);
    pts.push([b.x, b.z]); return pts;
  };
  const nodeW = n => net.nodes[n].out.reduce((m, o) => Math.max(m, o.e.width), 0);

  // ---------- roads, pavements, markings
  for (const e of net.edges) {
    const mid = net.pointAt(e, 1, e.len / 2), t = tile(mid.x, mid.z), w = e.width;
    ribbon(t.road, e.pts, -w / 2, w / 2, 0.02, 'world');
    if (!e.bridge) {
      const trim = n => (net.nodes[n].deg >= 3 ? nodeW(n) / 2 + 2.4 : 0.4);
      const s0 = trim(e.a), s1 = e.len - trim(e.b);
      if (s1 - s0 > 3) { const pts = slice(e, s0, s1); ribbon(t.pave, pts, w / 2, w / 2 + PAVE, 0.12, 'world'); ribbon(t.pave, pts, -w / 2 - PAVE, -w / 2, 0.12, 'world'); }
    }
    if (e.cls <= 2 && !e.oneway && e.len > 6) ribbon(t.mark, slice(e, 2, e.len - 2), -0.12, 0.12, 0.035, 'dash');
    if (e.a23 && e.len > 24) { const pts = slice(e, 7, e.len - 7); ribbon(t.red, pts, w / 2 - 3.2, w / 2 - 0.2, 0.03, 'world'); ribbon(t.red, pts, -w / 2 + 0.2, -w / 2 + 3.2, 0.03, 'world'); }
  }
  net.nodes.forEach((n, i) => { if (n.deg >= 2) disc(tile(n.x, n.z).road, n.x, n.z, nodeW(i) / 2 * 1.04, 0.02); });

  lap('roads');
  // ---------- parks
  const parks = data.parks.map(p => {
    const pts = []; for (let i = 0; i < p.pts.length; i += 2) pts.push([p.pts[i], p.pts[i + 1]]);
    let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9; pts.forEach(([x, z]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z); });
    return { name: p.name, pts, x0, x1, z0, z1 };
  });
  const inPoly = (pts, x, z) => { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const [xi, zi] = pts[i], [xj, zj] = pts[j]; if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) c = !c; } return c; };
  const parkGrid = new Map();
  parks.forEach((pk, i) => { for (let cz = Math.floor(pk.z0 / 64); cz <= Math.floor(pk.z1 / 64); cz++) for (let cx = Math.floor(pk.x0 / 64); cx <= Math.floor(pk.x1 / 64); cx++) { const k = cx + ',' + cz; let l = parkGrid.get(k); if (!l) parkGrid.set(k, l = []); l.push(i); } });
  const inPark = (x, z) => { const l = parkGrid.get(Math.floor(x / 64) + ',' + Math.floor(z / 64)); if (!l) return false; for (const i of l) { const pk = parks[i]; if (x >= pk.x0 && x <= pk.x1 && z >= pk.z0 && z <= pk.z1 && inPoly(pk.pts, x, z)) return true; } return false; };
  const parkGeos = [];
  for (const pk of parks) {
    const shape = new THREE.Shape(pk.pts.map(([x, z]) => new THREE.Vector2(x, -z)));
    const g = new THREE.ShapeGeometry(shape); g.rotateX(-Math.PI / 2); g.translate(0, 0.1, 0);
    const uv = g.attributes.uv, pos = g.attributes.position; for (let k = 0; k < uv.count; k++) uv.setXY(k, pos.getX(k) * 0.1, pos.getZ(k) * 0.1);
    parkGeos.push(g);
  }
  if (parkGeos.length) group.add(new THREE.Mesh(mergeGeometries(parkGeos, false), grassMat));
  const trees = [];
  for (const pk of parks) {
    let area = 0; pk.pts.forEach((p, i) => { const q = pk.pts[(i + 1) % pk.pts.length]; area += p[0] * q[1] - q[0] * p[1]; }); area = Math.abs(area) / 2;
    const want = Math.min(90, Math.floor(area / 420));
    for (let k = 0, tries = 0; k < want && tries < want * 6; tries++) {
      const x = pk.x0 + rnd() * (pk.x1 - pk.x0), z = pk.z0 + rnd() * (pk.z1 - pk.z0);
      if (!inPoly(pk.pts, x, z) || net.clearance(x, z, -1, 10) < 3.5) continue;
      trees.push({ x, z, r: 1.0 + rnd() * 0.5, h: 5 + rnd() * 4 }); k++;
    }
  }

  // ---------- spatial structures: occupancy (line of sight), collision grid
  const OCC = new Map();                                       // 3 m cells -> number of footprints covering it
  const KEY = (x, z) => (Math.floor(x / 3) + 2) * 4096 + (Math.floor(z / 3) + 2);
  const occ = (x, z) => OCC.has(KEY(x, z));
  const occAdd = (cx, cz, th, hx, hz) => { const c = Math.cos(th), s = Math.sin(th), keys = []; for (let a = -hx; a <= hx + 0.01; a += 1.5) for (let b = -hz; b <= hz + 0.01; b += 1.5) { const k = KEY(cx + a * c + b * s, cz - a * s + b * c); OCC.set(k, (OCC.get(k) || 0) + 1); keys.push(k); } return keys; };
  const occRemove = keys => { for (const k of keys) { const n = (OCC.get(k) || 1) - 1; if (n <= 0) OCC.delete(k); else OCC.set(k, n); } };
  const colGrid = new Map(), CG = 32;
  const cgAdd = (o, r) => {
    const ox = o.cx ?? o.x, oz = o.cz ?? o.z, cells = [];
    for (let cz = Math.floor((oz - r) / CG); cz <= Math.floor((oz + r) / CG); cz++) for (let cx = Math.floor((ox - r) / CG); cx <= Math.floor((ox + r) / CG); cx++) { const k = cx + ',' + cz; let l = colGrid.get(k); if (!l) colGrid.set(k, l = []); l.push(o); cells.push(k); }
    return { o, cells };
  };
  const cgRemove = h => { for (const k of h.cells) { const l = colGrid.get(k); if (!l) continue; const i = l.indexOf(h.o); if (i >= 0) l.splice(i, 1); if (!l.length) colGrid.delete(k); } };
  const addObb = (cx, cz, th, hx, hz) => cgAdd({ cx, cz, c: Math.cos(th), s: Math.sin(th), hx, hz }, Math.hypot(hx, hz) + 1);
  // ---------- Blender landmark models, placed on their real OSM footprints
  const landmarks = [], skipPolys = [];
  const inPolyW = (pts, x, z) => { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const [xi, zi] = pts[i], [xj, zj] = pts[j]; if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) c = !c; } return c; };
  const lmDefs = extra.lmdefs || {}, lmModels = extra.lmModels || {};
  for (const key in lmDefs) {
    const def = lmDefs[key]; landmarks.push({ name: def.name, x: def.c[0], z: def.c[1] });
    const src = lmModels[key]; if (!src) continue;
    const g = src.clone(true); g.position.set(def.c[0], 0, def.c[1]); g.rotation.y = def.theta; group.add(g);
    g.traverse(o => { if (o.isMesh && o.material && o.material.emissive && o.material.emissiveIntensity > 0 && o.material.emissive.r + o.material.emissive.g + o.material.emissive.b > 0.01 && !o.material.userData.toned) { o.material = o.material.clone(); o.material.userData.toned = true; o.material.emissiveIntensity *= 0.32; } });
    skipPolys.push(def.poly);
    const c = Math.cos(def.theta), s = Math.sin(def.theta); let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
    for (const [x, z] of def.poly) { const vx = x - def.c[0], vz = z - def.c[1], lx = vx * c - vz * s, lz = vx * s + vz * c; x0 = Math.min(x0, lx); x1 = Math.max(x1, lx); z0 = Math.min(z0, lz); z1 = Math.max(z1, lz); }
    const mx = (x0 + x1) / 2, mz = (z0 + z1) / 2, wx = def.c[0] + mx * c + mz * s, wz = def.c[1] - mx * s + mz * c;
    addObb(wx, wz, def.theta, (x1 - x0) / 2, (z1 - z0) / 2); occAdd(wx, wz, def.theta, (x1 - x0) / 2, (z1 - z0) / 2);
    if (src.userData.update) ctx.update.push(src.userData.update);
  }
  lap('landmarks');

  // ---------- real building footprints, streamed in by distance
  const osm = extra.bdata ? new OsmBuildings(group, extra.bdata, {
    net, districtAt, addObb, removeObb: cgRemove, occAdd, occRemove,
    skip: (x, z) => skipPolys.some(p => inPolyW(p, x, z)),
  }, bMat, signMat) : null;

  // ---------- build tile meshes
  const mk = (list, mat) => { if (!list.length) return; const g = mergeGeometries(list, false); group.add(new THREE.Mesh(g, mat)); list.forEach(x => x.dispose()); };
  for (const t of tiles.values()) {
    for (const [acc, mat] of [[t.road, asphalt], [t.pave, pavement], [t.mark, markMat], [t.red, redMat]]) { const m = acc.mesh(mat); if (m) group.add(m); }
  }

  // ---------- trees (instanced) + collision
  if (trees.length) {
    const tmp = new THREE.Object3D();
    const fol = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: 0x1f4a22, roughness: 1, flatShading: true }), trees.length);
    const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.2, 0.3, 1, 6), new THREE.MeshStandardMaterial({ color: 0x3a2a1a }), trees.length);
    trees.forEach((t, i) => {
      tmp.position.set(t.x, t.h * 0.35 + 0.1, t.z); tmp.scale.set(t.h * 0.34, t.h * 0.45, t.h * 0.34); tmp.rotation.set(0, rnd() * 6, 0); tmp.updateMatrix(); fol.setMatrixAt(i, tmp.matrix);
      tmp.position.set(t.x, t.h * 0.18 + 0.1, t.z); tmp.scale.set(1, t.h * 0.36, 1); tmp.rotation.set(0, 0, 0); tmp.updateMatrix(); trunk.setMatrixAt(i, tmp.matrix);
      cgAdd({ x: t.x, z: t.z, r: t.r * 0.5, tree: true }, 2);
    });
    group.add(fol, trunk);
  }

  lap('meshes');
  // ---------- street furniture (lamps, crossings, signals, bus stops...)
  buildFurniture(group, net, rnd, { inPark, occ, addTree: (x, z, r) => cgAdd({ x, z, r, tree: true }, 2) });

  lap('furniture');
  // ---------- district gantries over the nearest main road
  for (const k in DISTRICTS) {
    const d = DISTRICTS[k], n = net.nearest(d.c[0], d.c[1], 400, e => e.cls <= 1); if (!n) continue;
    const cv = document.createElement('canvas'); cv.width = 512; cv.height = 128; const x = cv.getContext('2d');
    x.fillStyle = '#0d2a6b'; x.fillRect(0, 0, 512, 128); x.strokeStyle = '#fff'; x.lineWidth = 6; x.strokeRect(6, 6, 500, 116);
    x.fillStyle = '#fff'; x.font = 'bold 62px "Arial Narrow", Arial, sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(d.name, 256, 68);
    const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
    const steel = new THREE.MeshStandardMaterial({ color: 0x555a60 }), half = n.e.width / 2 + 1.5;
    const g = new THREE.Group();
    for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 9, 8), steel); p.position.set(s * half, 4.5, 0); g.add(p); }
    const bar = new THREE.Mesh(new THREE.BoxGeometry(half * 2 + 0.5, 0.4, 0.4), steel); bar.position.y = 9; g.add(bar);
    const sign = new THREE.Mesh(new THREE.PlaneGeometry(Math.min(12, half * 1.6), 3), new THREE.MeshBasicMaterial({ map: t })); sign.position.set(0, 7.2, 0.25); g.add(sign);
    const sign2 = sign.clone(); sign2.rotation.y = Math.PI; sign2.position.z = -0.25; g.add(sign2);
    g.position.set(n.px, 0, n.pz); g.rotation.y = Math.atan2(n.tx, n.tz); group.add(g);
  }

  // ---------- collision / line of sight / surfaces
  const dynamicRects = [], dynamicObbs = [];
  const R = 0.95;
  function collide(p) {
    const sn = Math.sin(p.th), cs = Math.cos(p.th), half = p.def.L / 2 - R, rad = p.def.W / 2 + 0.05;
    for (const off of [-half, half]) {
      const px = p.x, pz = p.z; p.x = px + sn * off; p.z = pz + cs * off;
      const ax = p.x, az = p.z;
      const l = colGrid.get(Math.floor(p.x / CG) + ',' + Math.floor(p.z / CG));
      if (l) for (const o of l) {
        if (o.tree) {
          const ddx = p.x - o.x, ddz = p.z - o.z, dist = Math.hypot(ddx, ddz), rr = rad + o.r;
          if (dist < rr && dist > 1e-3) { const nxv = ddx / dist, nzv = ddz / dist; p.x = o.x + nxv * rr; p.z = o.z + nzv * rr; const vn = p.vx * nxv + p.vz * nzv; if (vn < 0) { p.vx -= 1.3 * vn * nxv; p.vz -= 1.3 * vn * nzv; p.vx *= 0.9; p.vz *= 0.9; p.lastImpact = Math.max(p.lastImpact, -vn); } }
        } else p.resolveOBB(o, rad);
      }
      for (const r of dynamicRects) p.resolveRect(r, rad);
      for (const o of dynamicObbs) p.resolveOBB(o, rad);
      const cxn = p.x - ax, czn = p.z - az; p.x = px + cxn; p.z = pz + czn;
    }
    const lo = 2, hiX = WORLD.w - 2, hiZ = WORLD.h - 2;
    if (p.x < lo) { p.x = lo; if (p.vx < 0) { p.lastImpact = Math.max(p.lastImpact, -p.vx); p.vx *= -0.3; } }
    if (p.x > hiX) { p.x = hiX; if (p.vx > 0) { p.lastImpact = Math.max(p.lastImpact, p.vx); p.vx *= -0.3; } }
    if (p.z < lo) { p.z = lo; if (p.vz < 0) { p.lastImpact = Math.max(p.lastImpact, -p.vz); p.vz *= -0.3; } }
    if (p.z > hiZ) { p.z = hiZ; if (p.vz > 0) { p.lastImpact = Math.max(p.lastImpact, p.vz); p.vz *= -0.3; } }
  }
  function lineClear(ax, az, bx, bz) {
    const dx = bx - ax, dz = bz - az, len = Math.hypot(dx, dz), steps = Math.ceil(len / 3);
    for (let i = 1; i < steps; i++) { const t = i / steps; if (occ(ax + dx * t, az + dz * t)) return false; }
    return true;
  }
  const surfaceGrip = (x, z) => (inPark(x, z) ? 0.62 : 1);

  // ---------- routing helpers (A* on the real road graph)
  function routeToPoint(x0, z0, x1, z1) {
    const a = net.nearestNode(x0, z0), b = net.nearestNode(x1, z1), r = net.route(a, b);
    if (!r) return null;
    const nodes = [[net.nodes[a].x, net.nodes[a].z]]; r.forEach(st => { const n = net.nodes[net.endNode(st)]; nodes.push([n.x, n.z]); });
    return { steps: r, nodes, poly: net.routePolyline(r) };
  }
  const sp = net.nearest(data.places.spawn[0], data.places.spawn[1], 200, e => e.cls <= 1) || net.nearest(data.places.spawn[0], data.places.spawn[1], 200);
  const spP = net.lanePoint(sp.e, 1, Math.max(2, Math.min(sp.e.len - 2, sp.s)), net.laneOffset(sp.e));
  const spawn = { x: spP.x, z: spP.z, th: Math.atan2(spP.tx, spP.tz) };

  return {
    net, data, places: data.places, spawn, parks, trees, landmarks, groundMats, group, collide, lineClear, surfaceGrip, dynamicRects, dynamicObbs, routeToPoint,
    update: (dt, px, pz) => { ctx.update.forEach(f => f(dt)); if (osm && px !== undefined) osm.update(px, pz); }, preload: (px, pz) => osm && osm.preload(px, pz), osm,
    roadNameAt, districtAt, occ,
  };
}
