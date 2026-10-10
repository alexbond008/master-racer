import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { rnd, pick, windowTextures, box, slabBox } from './buildings.js';
import { townHall, academy, plazaChurch, estate, windmill, library, bussey, clockCorner, churches, theatre, barrelArena } from './landmarks.js';
import { buildFurniture } from './furniture.js';

// Procedural South London: Brixton (NW), Peckham (NE), Streatham (S).
export const CELL = 64, ROAD = 18, BLOCK = 46, N = 24, SIZE = CELL * N;
const SIDEWALK = 3;

export const DISTRICTS = {
  brixton:   { name: 'BRIXTON',   c: [380, 470],  tint: '#d9a441' },
  peckham:   { name: 'PECKHAM',   c: [1150, 420], tint: '#e0602a' },
  streatham: { name: 'STREATHAM', c: [700, 1230], tint: '#4aa86b' },
};

export function districtAt(x, z) {
  let best = null, bd = Infinity;
  for (const k in DISTRICTS) {
    const [cx, cz] = DISTRICTS[k].c, d = Math.hypot(x - cx, z - cz);
    if (d < bd) { bd = d; best = k; }
  }
  return best;
}

const PALETTE = {
  brixton:   ['#8b3a2b', '#a04a35', '#8d7d5c', '#d9a1b0', '#5bb3b0', '#e0b14a', '#6b3f3a', '#c9c1ae'],
  peckham:   ['#8d7d5c', '#a38f64', '#8b3a2b', '#6f6a63', '#7d6a55', '#b2a98d', '#7a3226'],
  streatham: ['#9a4430', '#b5573f', '#d8d0bd', '#cfc5ae', '#8c6a4e', '#9b8f72'],
};
const FLOORS = { brixton: [3, 5], peckham: [3, 4], streatham: [2, 3] };
const BRIGHT = { brixton: ['#e63946', '#ffb703', '#2a9d8f', '#3a86ff', '#fb5607', '#06d6a0', '#ffd166'], peckham: ['#e63946', '#ffb703', '#2a9d8f', '#3a86ff', '#fb5607', '#8338ec', '#06d6a0', '#ffd166', '#ff4fa3'], streatham: ['#d62828', '#1d4e89', '#f4f4f4', '#2b9348', '#ffb703'] };
const FASCIA_P = { brixton: 0.75, peckham: 1, streatham: 0.85 };

// real road names, assigned per district (research/london.md). Spine = A23, Rye Lane = Peckham's N-S street.
const NAMES = {
  brixton: ['COLDHARBOUR LANE', 'ACRE LANE', 'STOCKWELL ROAD', 'ELECTRIC AVENUE', 'ATLANTIC ROAD', 'EFFRA ROAD', 'RAILTON ROAD', 'LOUGHBOROUGH ROAD', 'FERNDALE ROAD', 'GRESHAM ROAD', 'STATION ROAD', 'BRIXTON WATER LANE'],
  peckham: ['PECKHAM HIGH STREET', 'QUEENS ROAD', 'BELLENDEN ROAD', 'PECKHAM HILL STREET', 'BLACKPOOL ROAD', 'CONSORT ROAD', 'HANOVER PARK', 'CHOUMERT ROAD', 'COPELAND ROAD', 'MEETING HOUSE LANE', 'PECKHAM RYE', 'BACON\'S LANE'],
  streatham: ['LEIGHAM COURT ROAD', 'MITCHAM LANE', 'GREYHOUND LANE', 'PENDENNIS ROAD', 'DREWSTEAD ROAD', 'GLENELDON ROAD', 'BARROW ROAD', 'NATAL ROAD', 'ESTREHAM ROAD', 'COMMONSIDE EAST', 'STREATHAM PLACE', 'TOOTING BEC ROAD'],
};
export function roadNameAt(x, z) {
  const ri = Math.round(x / CELL), rj = Math.round(z / CELL);
  const onV = Math.abs(x - ri * CELL) < ROAD / 2, onH = Math.abs(z - rj * CELL) < ROAD / 2;
  if (!onV && !onH) return '';
  const d = districtAt(x, z);
  const spine = z < 640 ? 'BRIXTON ROAD' : z < 960 ? 'BRIXTON HILL' : z < 1180 ? 'STREATHAM HILL' : 'STREATHAM HIGH ROAD';
  const vName = ri === 8 ? spine : ri === 17 && z < 900 ? 'RYE LANE' : NAMES[d][(ri * 5) % 12];
  const hName = rj === 9 && x < 900 ? 'COLDHARBOUR LANE' : rj === 6 && x > 900 ? 'PECKHAM HIGH STREET' : NAMES[d][(rj * 7 + 3) % 12];
  return onV ? vName : hName; // at junctions the N-S road wins
}

export function buildWorld(scene) {
  const group = new THREE.Group(); scene.add(group);
  const tex = windowTextures();
  const bMat = new THREE.MeshStandardMaterial({ map: tex.map, emissiveMap: tex.emissive, emissive: 0xffffff, emissiveIntensity: 0.9, vertexColors: true, roughness: 0.85 });
  const concreteMat = new THREE.MeshStandardMaterial({ color: 0x8d8f91, roughness: 0.95, vertexColors: true });
  const slabMat = new THREE.MeshStandardMaterial({ color: 0x58585c, roughness: 0.95 });
  const grassMat = new THREE.MeshStandardMaterial({ color: 0x2f5a2c, roughness: 1 });

  // ---------- ground (asphalt)
  const nc = document.createElement('canvas'); nc.width = nc.height = 256;
  const nx = nc.getContext('2d'); nx.fillStyle = '#26262a'; nx.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 5000; i++) { const v = 20 + Math.random() * 30 | 0; nx.fillStyle = `rgb(${v},${v},${v + 2})`; nx.fillRect(Math.random() * 256, Math.random() * 256, 2, 2); }
  const asphaltTex = new THREE.CanvasTexture(nc); asphaltTex.wrapS = asphaltTex.wrapT = THREE.RepeatWrapping; asphaltTex.repeat.set(220, 220); asphaltTex.colorSpace = THREE.SRGBColorSpace; asphaltTex.anisotropy = 8;
  const groundMat = new THREE.MeshStandardMaterial({ map: asphaltTex, roughness: 0.82, metalness: 0.0 });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(SIZE + 1200, SIZE + 1200), groundMat);
  ground.rotation.x = -Math.PI / 2; ground.position.set(SIZE / 2, 0, SIZE / 2); ground.receiveShadow = true;
  group.add(ground);

  // ---------- blocks
  const blocks = new Array(N * N);
  const buildList = [], concreteList = [], slabList = [], grassList = [];
  const trees = [];      // {x,z,r}
  const lampPos = [];
  const landmarks = [];
  const ctx = { bMat, update: [] };
  const signList = [];
  const LM = { '6,8': [townHall, 'LAMBETH TOWN HALL'], '4,6': [academy, 'BRIXTON ACADEMY'], '6,7': [plazaChurch, 'WINDRUSH SQUARE'], '3,8': [estate, 'BARRIER BLOCK'], '6,12': [windmill, 'BRIXTON WINDMILL'], '17,6': [library, 'PECKHAM LIBRARY'], '18,7': [bussey, 'BUSSEY BUILDING'], '10,18': [churches, 'STREATHAM GREEN'], '9,20': [theatre, 'STREATHAM HILL THEATRE'] };

  // special block assignments (bx,bz)
  const BRIXTON_ARCHES = [7, 7], PECKHAM_CARPARK = [18, 6], STREATHAM_RINK = [14, 19];
  const PARKS = new Set(['5,4', '6,4', '12,19', '13,19', '12,20', '13,20', '19,9', '19,10', '10,12']);

  for (let bz = 0; bz < N; bz++) for (let bx = 0; bx < N; bx++) {
    const x0 = bx * CELL + (CELL - BLOCK) / 2 + ROAD / 2 - (CELL - ROAD) / 2 + 0; // block occupies [bx*64+9, bx*64+55]
    const bxMin = bx * CELL + ROAD / 2, bzMin = bz * CELL + ROAD / 2;
    const rect = { x0: bxMin, x1: bxMin + BLOCK, z0: bzMin, z1: bzMin + BLOCK };
    void x0;
    const cx = (rect.x0 + rect.x1) / 2, cz = (rect.z0 + rect.z1) / 2;
    const d = districtAt(cx, cz);
    const blk = { rect, district: d, type: 'build', solid: null, trees: [] };
    blocks[bz * N + bx] = blk;

    slabList.push(slabBox(cx, cz, BLOCK, BLOCK, 0.18)); // sidewalk slab

    // lamps at block corners (sidewalk)
    for (const [lx, lz] of [[rect.x0 + 1, rect.z0 + 1], [rect.x1 - 1, rect.z0 + 1], [rect.x0 + 1, rect.z1 - 1], [rect.x1 - 1, rect.z1 - 1]]) lampPos.push([lx, lz]);

    const key = bx + ',' + bz;
    if (PARKS.has(key)) {
      blk.type = 'park';
      grassList.push(slabBox(cx, cz, BLOCK - 2, BLOCK - 2, 0.08, 0.18));
      const count = 14;
      for (let i = 0; i < count; i++) {
        const t = { x: rect.x0 + 5 + rnd() * (BLOCK - 10), z: rect.z0 + 5 + rnd() * (BLOCK - 10), r: 1.0 + rnd() * 0.5, h: 5 + rnd() * 4 };
        blk.trees.push(t); trees.push(t);
      }
      continue;
    }

    const inner = { x0: rect.x0 + SIDEWALK, x1: rect.x1 - SIDEWALK, z0: rect.z0 + SIDEWALK, z1: rect.z1 - SIDEWALK };
    blk.solid = inner;

    if (bx === BRIXTON_ARCHES[0] && bz === BRIXTON_ARCHES[1]) { blk.type = 'arches'; landmarks.push({ name: 'BRIXTON ARCHES', x: cx, z: cz }); archesBlock(group, inner, ctx); continue; }
    if (bx === PECKHAM_CARPARK[0] && bz === PECKHAM_CARPARK[1]) { blk.type = 'carpark'; landmarks.push({ name: 'PECKHAM LEVELS', x: cx, z: cz }); carparkBlock(group, inner); continue; }
    if (bx === STREATHAM_RINK[0] && bz === STREATHAM_RINK[1]) { blk.type = 'rink'; landmarks.push({ name: 'STREATHAM ICE ARENA', x: cx, z: cz }); barrelArena(group, inner, ctx); blk.solid = inner; continue; }

    const lm = LM[key];
    if (lm) {
      const info = lm[0](group, inner, ctx) || {};
      blk.type = info.park ? 'park' : 'landmark';
      blk.solid = info.solid !== undefined ? info.solid : inner; blk.extra = info.extra || [];
      if (info.trees) blk.trees = info.trees;
      landmarks.push({ name: lm[1], x: cx, z: cz });
      continue;
    }

    // Peckham estates: some blocks become concrete slab towers
    if (d === 'peckham' && rnd() < 0.18) {
      blk.type = 'estate';
      const fl = 7 + Math.floor(rnd() * 5);
      box(concreteList, cx - 8, cz, 10, 36, fl * 3.0, pick(['#8f8f8c', '#7e8082', '#9b9a94']), 0, false);
      box(concreteList, cx + 9, cz, 10, 36, (fl - 2) * 3.0, '#8a8a88', 0, false);
      for (let k = 0; k < 6; k++) box(concreteList, cx - 8 + (k % 2 ? 6 : -6) * 0 + 5.2, cz - 15 + k * 6, 0.4, 0.4, fl * 3.0, '#6b6b6b', 0, false);
      continue;
    }

    // terraced ring
    const pal = PALETTE[d], [fmin, fmax] = FLOORS[d];
    const run = (a0, a1, fixed, horizontal, sign) => {
      let a = a0;
      while (a < a1 - 0.5) {
        const w = Math.min(a1 - a, 7 + Math.floor(rnd() * 3) * 3.5 / 1.2);
        const depth = 9 + rnd() * 2;
        const h = (fmin + Math.floor(rnd() * (fmax - fmin + 1))) * 3.2;
        const col = pick(pal);
        if (horizontal) box(buildList, a + w / 2, fixed + sign * depth / 2, w, depth, h, col);
        else box(buildList, fixed + sign * depth / 2, a + w / 2, depth, w, h, col);
        // shopfront: glowing window band + bright fascia sign on the street face
        if (rnd() < FASCIA_P[d]) {
          const fc = new THREE.Color(pick(BRIGHT[d])).multiplyScalar(1.7), warm = new THREE.Color(1.5, 1.05, 0.55);
          if (horizontal) { box(signList, a + w / 2, fixed - sign * 0.2, w - 0.5, 0.4, 0.9, fc, 3.1, false); box(signList, a + w / 2, fixed - sign * 0.06, w - 1.2, 0.12, 2.0, warm, 0.8, false); }
          else { box(signList, fixed - sign * 0.2, a + w / 2, 0.4, w - 0.5, 0.9, fc, 3.1, false); box(signList, fixed - sign * 0.06, a + w / 2, 0.12, w - 1.2, 2.0, warm, 0.8, false); }
        }
        a += w;
      }
    };
    run(inner.x0, inner.x1, inner.z0, true, 1);
    run(inner.x0, inner.x1, inner.z1, true, -1);
    run(inner.z0 + 10, inner.z1 - 10, inner.x0, false, 1);
    run(inner.z0 + 10, inner.z1 - 10, inner.x1, false, -1);
    if (key === '16,5') { clockCorner(group, inner, ctx); landmarks.push({ name: 'CLOCK TOWER', x: cx, z: cz }); }
  }

  const mk = (list, mat) => {
    if (!list.length) return;
    const g = mergeGeometries(list, false);
    if (!g.attributes.color) { const n = g.attributes.position.count; g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).fill(1), 3)); }
    group.add(new THREE.Mesh(g, mat));
    list.forEach(g2 => g2.dispose());
  };
  mk(buildList, bMat); mk(concreteList, concreteMat); mk(signList, new THREE.MeshBasicMaterial({ vertexColors: true }));
  mk(slabList, slabMat); mk(grassList, grassMat);

  // ---------- road markings (instanced)
  const markGeo = new THREE.PlaneGeometry(1, 1); markGeo.rotateX(-Math.PI / 2);
  const dashes = [];
  for (let i = 0; i <= N; i++) for (let j = 0; j < N; j++) {
    const start = j * CELL + ROAD / 2;
    for (let k = 0; k < 5; k++) {
      const t = start + (BLOCK / 5) * (k + 0.5);
      dashes.push([i * CELL, t, 0.22, 3.4]);      // vertical road: along z
      dashes.push([t, i * CELL, 3.4, 0.22]);      // horizontal road: along x
    }
  }
  const mm = new THREE.InstancedMesh(markGeo, new THREE.MeshStandardMaterial({ color: 0xe8e2c8, roughness: 0.6 }), dashes.length);
  const tmp = new THREE.Object3D();
  dashes.forEach(([x, z, sx, sz], i) => { tmp.position.set(x, 0.03, z); tmp.scale.set(sx, 1, sz); tmp.updateMatrix(); mm.setMatrixAt(i, tmp.matrix); });
  group.add(mm);

  // ---------- lamps
  const lampCount = lampPos.length;
  const poleGeo = new THREE.CylinderGeometry(0.08, 0.12, 7, 6); poleGeo.translate(0, 3.5, 0);
  const poles = new THREE.InstancedMesh(poleGeo, new THREE.MeshStandardMaterial({ color: 0x22252a, roughness: 0.7 }), lampCount);
  const heads = new THREE.InstancedMesh(new THREE.SphereGeometry(0.34, 8, 6), new THREE.MeshBasicMaterial({ color: new THREE.Color(4.2, 2.6, 0.8) }), lampCount);
  lampPos.forEach(([x, z], i) => {
    tmp.position.set(x, 0, z); tmp.scale.set(1, 1, 1); tmp.updateMatrix(); poles.setMatrixAt(i, tmp.matrix);
    tmp.position.set(x, 7.1, z); tmp.updateMatrix(); heads.setMatrixAt(i, tmp.matrix);
  });
  group.add(poles, heads);

  // ---------- trees
  if (trees.length) {
    const fol = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: 0x1f4a22, roughness: 1, flatShading: true }), trees.length);
    const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.2, 0.3, 1, 6), new THREE.MeshStandardMaterial({ color: 0x3a2a1a }), trees.length);
    trees.forEach((t, i) => {
      tmp.position.set(t.x, t.h * 0.35, t.z); tmp.scale.set(t.h * 0.34, t.h * 0.45, t.h * 0.34); tmp.rotation.set(0, rnd() * 6, 0); tmp.updateMatrix(); fol.setMatrixAt(i, tmp.matrix);
      tmp.position.set(t.x, t.h * 0.18, t.z); tmp.scale.set(1, t.h * 0.36, 1); tmp.rotation.set(0, 0, 0); tmp.updateMatrix(); trunk.setMatrixAt(i, tmp.matrix);
    });
    group.add(fol, trunk);
  }

  buildFurniture(group, rnd);

  // ---------- district gantry signs
  for (const k in DISTRICTS) addSign(group, DISTRICTS[k], k);

  // ---------- collision
  const R = 0.95;
  function collide(p) {
    const ccx = Math.floor(p.x / CELL), ccz = Math.floor(p.z / CELL);
    const sn = Math.sin(p.th), cs = Math.cos(p.th);
    const half = p.def.L / 2 - R;
    const rad = p.def.W / 2 + 0.05;
    const ox = p.x, oz = p.z;
    for (const off of [-half, half]) {
      // temporarily treat each circle separately by shifting car pos
      const px = p.x, pz = p.z;
      p.x = px + sn * off; p.z = pz + cs * off;
      const ax = p.x, az = p.z;
      for (let dz = -1; dz <= 1; dz++) for (let dx = -1; dx <= 1; dx++) {
        const b = blocks[(ccz + dz) * N + (ccx + dx)];
        if (!b || ccz + dz < 0 || ccz + dz >= N || ccx + dx < 0 || ccx + dx >= N) continue;
        if (b.solid) p.resolveRect(b.solid, rad);
        if (b.extra) for (const e of b.extra) p.resolveRect(e, rad);
        for (const t of b.trees) {
          const ddx = p.x - t.x, ddz = p.z - t.z, dist = Math.hypot(ddx, ddz), rr = rad + t.r * 0.5;
          if (dist < rr && dist > 1e-3) {
            const nxv = ddx / dist, nzv = ddz / dist; p.x = t.x + nxv * rr; p.z = t.z + nzv * rr;
            const vn = p.vx * nxv + p.vz * nzv; if (vn < 0) { p.vx -= 1.3 * vn * nxv; p.vz -= 1.3 * vn * nzv; p.vx *= 0.9; p.vz *= 0.9; p.lastImpact = Math.max(p.lastImpact, -vn); }
          }
        }
      }
      for (const r of dynamicRects) p.resolveRect(r, rad);
      // map the correction back to car centre
      const cxn = p.x - ax, czn = p.z - az;
      p.x = px + cxn; p.z = pz + czn;
    }
    void ox; void oz;
    // map edge walls
    const lo = -ROAD / 2 + 2, hi = SIZE + ROAD / 2 - 2;
    if (p.x < lo) { p.x = lo; if (p.vx < 0) { p.lastImpact = Math.max(p.lastImpact, -p.vx); p.vx *= -0.3; } }
    if (p.x > hi) { p.x = hi; if (p.vx > 0) { p.lastImpact = Math.max(p.lastImpact, p.vx); p.vx *= -0.3; } }
    if (p.z < lo) { p.z = lo; if (p.vz < 0) { p.lastImpact = Math.max(p.lastImpact, -p.vz); p.vz *= -0.3; } }
    if (p.z > hi) { p.z = hi; if (p.vz > 0) { p.lastImpact = Math.max(p.lastImpact, p.vz); p.vz *= -0.3; } }
  }

  // line of sight between two points: blocked if any sample lies inside a building footprint
  function lineClear(ax, az, bx, bz, pad = 1.2) {
    const dx = bx - ax, dz = bz - az, len = Math.hypot(dx, dz), steps = Math.ceil(len / 3);
    for (let i = 1; i < steps; i++) {
      const t = i / steps, x = ax + dx * t, z = az + dz * t;
      const cx = Math.floor(x / CELL), cz = Math.floor(z / CELL);
      if (cx < 0 || cz < 0 || cx >= N || cz >= N) continue;
      const s2 = blocks[cz * N + cx].solid;
      if (s2 && x > s2.x0 - pad && x < s2.x1 + pad && z > s2.z0 - pad && z < s2.z1 + pad) return false;
    }
    return true;
  }
  const dynamicRects = [];

  // grass slows you a bit
  function surfaceGrip(x, z) {
    const bx = Math.floor(x / CELL), bz = Math.floor(z / CELL);
    const b = blocks[bz * N + bx];
    if (b && b.type === 'park' && x > b.rect.x0 + 1 && x < b.rect.x1 - 1 && z > b.rect.z0 + 1 && z < b.rect.z1 - 1) return 0.62;
    return 1;
  }

  // ---------- route graph over intersections (i,j) 0..N
  const nodePos = (i, j) => [i * CELL, j * CELL];
  const nearestNode = (x, z) => [Math.max(0, Math.min(N, Math.round(x / CELL))), Math.max(0, Math.min(N, Math.round(z / CELL)))];
  function route(a, b) {
    // BFS on grid, then prefer fewer turns by trying both L-shapes and a mid-zigzag; pick shortest then first.
    const [ai, aj] = a, [bi, bj] = b, path = [[ai, aj]];
    let i = ai, j = aj;
    // go along the longer axis first, alternating in chunks of 3 blocks to look like city driving
    while (i !== bi || j !== bj) {
      const di = bi - i, dj = bj - j;
      if (Math.abs(di) >= Math.abs(dj) && di !== 0) i += Math.sign(di) * Math.min(Math.abs(di), 3);
      else if (dj !== 0) j += Math.sign(dj) * Math.min(Math.abs(dj), 3);
      else i += Math.sign(di) * Math.min(Math.abs(di), 3);
      path.push([i, j]);
    }
    return path.map(([x, y]) => nodePos(x, y));
  }

  return { update: dt => ctx.update.forEach(f => f(dt)), roadNameAt, group, blocks, collide, surfaceGrip, lineClear, dynamicRects,  groundMat, route, nodePos, nearestNode, landmarks, districtAt, trees };
}

function addSign(group, dist, key) {
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 128;
  const x = cv.getContext('2d');
  x.fillStyle = '#0d2a6b'; x.fillRect(0, 0, 512, 128);
  x.strokeStyle = '#fff'; x.lineWidth = 6; x.strokeRect(6, 6, 500, 116);
  x.fillStyle = '#fff'; x.font = 'bold 62px "Arial Narrow", Arial, sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(dist.name, 256, 68);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.MeshBasicMaterial({ map: t });
  const [cx, cz] = dist.c;
  const ix = Math.round(cx / CELL) * CELL, iz = Math.round(cz / CELL) * CELL;
  const gantry = new THREE.Group();
  for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 9, 8), new THREE.MeshStandardMaterial({ color: 0x555a60 })); p.position.set(s * 8, 4.5, 0); gantry.add(p); }
  const bar = new THREE.Mesh(new THREE.BoxGeometry(16.5, 0.4, 0.4), new THREE.MeshStandardMaterial({ color: 0x555a60 })); bar.position.y = 9; gantry.add(bar);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(12, 3), mat); sign.position.set(0, 7.2, 0.25); gantry.add(sign);
  const sign2 = sign.clone(); sign2.rotation.y = Math.PI; sign2.position.z = -0.25; gantry.add(sign2);
  gantry.position.set(ix, 0, iz + 24);
  group.add(gantry);
}

// ---- landmarks
function archesBlock(group, r, ctx) {
  const w = r.x1 - r.x0, d = r.z1 - r.z0;
  const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 256;
  const x = cv.getContext('2d');
  x.fillStyle = '#6e3a2a'; x.fillRect(0, 0, 1024, 256);
  for (let y = 0; y < 256; y += 16) for (let xx = 0; xx < 1024; xx += 32) { x.fillStyle = (y / 16) % 2 ? '#5b2f22' : '#7a4332'; x.fillRect(xx + ((y / 16) % 2 ? 16 : 0), y, 30, 14); }
  for (let i = 0; i < 8; i++) {
    const ax = 20 + i * 126;
    x.fillStyle = '#0c0805'; x.beginPath(); x.moveTo(ax, 256); x.lineTo(ax, 110); x.arc(ax + 43, 110, 43, Math.PI, 0); x.lineTo(ax + 86, 256); x.fill();
    x.fillStyle = i % 3 === 0 ? '#ffb347' : (i % 3 === 1 ? '#ff4fa3' : '#31e0ff'); x.fillRect(ax + 10, 150, 66, 100);
  }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  const wall = new THREE.MeshStandardMaterial({ map: t, emissiveMap: t, emissive: 0xffffff, emissiveIntensity: 0.55, roughness: 0.9 });
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, 7, 12), wall);
  body.position.set(cx, 3.5, r.z0 + 6); group.add(body);
  const body2 = body.clone(); body2.position.z = r.z1 - 6; group.add(body2);
  const deck = new THREE.Mesh(new THREE.BoxGeometry(w, 1, d), new THREE.MeshStandardMaterial({ color: 0x3b3b3f })); deck.position.set(cx, 7.5, cz); group.add(deck);
  // fill the middle so it's collidable-looking solid
  const mid = new THREE.Mesh(new THREE.BoxGeometry(w, 7, d - 24), new THREE.MeshStandardMaterial({ color: 0x3f2a22 })); mid.position.set(cx, 3.5, cz); group.add(mid);
  // a commuter train crossing the viaduct deck (loops forever)
  const train = new THREE.Group(), carMat = new THREE.MeshStandardMaterial({ color: 0x1d2a52, metalness: 0.4, roughness: 0.45 }), winMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 2, 1.4) });
  for (let c = 0; c < 4; c++) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(13.5, 3.1, 2.7), carMat); b.position.set(c * 14.2, 1.6, 0); train.add(b);
    const win = new THREE.Mesh(new THREE.BoxGeometry(12, 0.8, 2.78), winMat); win.position.set(c * 14.2, 2.1, 0); train.add(win);
  }
  train.position.set(r.x0 - 80, 8, cz); group.add(train);
  const rail = new THREE.Mesh(new THREE.BoxGeometry(w + 300, 0.15, 0.15), new THREE.MeshStandardMaterial({ color: 0x777777 })); for (const dz of [-0.7, 0.7]) { const rr = rail.clone(); rr.position.set(cx, 8.1, cz + dz); group.add(rr); }
  let tx = r.x0 - 80; ctx.update.push(dt => { tx += 26 * dt; if (tx > r.x1 + 80) tx = r.x0 - 110; train.position.x = tx; });
  // railway sign light
  const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.4), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.3, 4, 0.5) })); lamp.position.set(cx, 8.6, cz); group.add(lamp);
}

function carparkBlock(group, r) {
  const w = r.x1 - r.x0, d = r.z1 - r.z0, cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  const slab = new THREE.MeshStandardMaterial({ color: 0x9a9a96, roughness: 0.95 });
  const pil = new THREE.MeshStandardMaterial({ color: 0x77777a, roughness: 0.95 });
  const strip = new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 3.2, 3.6) });
  for (let l = 0; l < 10; l++) {
    const y = l * 3.2;
    const s = new THREE.Mesh(new THREE.BoxGeometry(w, 0.5, d), slab); s.position.set(cx, y + 0.25, cz); group.add(s);
    const p = new THREE.Mesh(new THREE.BoxGeometry(w, 0.9, 0.25), pil); p.position.set(cx, y + 3.2 - 0.45 + 0.5, r.z0 + 0.12); group.add(p);
    const p2 = p.clone(); p2.position.z = r.z1 - 0.12; group.add(p2);
    const lt = new THREE.Mesh(new THREE.BoxGeometry(w * 0.8, 0.08, 0.15), strip); lt.position.set(cx, y + 2.9, cz); group.add(lt);
  }
  for (let ix = 0; ix < 5; ix++) for (let iz = 0; iz < 5; iz++) {
    const c = new THREE.Mesh(new THREE.BoxGeometry(0.7, 32.2, 0.7), pil);
    c.position.set(r.x0 + 1 + ix * ((w - 2) / 4), 16.1, r.z0 + 1 + iz * ((d - 2) / 4)); group.add(c);
  }
}

function rinkBlock(list, r) {
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  box(list, cx, cz, r.x1 - r.x0 - 2, r.z1 - r.z0 - 2, 10, '#c9c4b4', 0, true);
  box(list, cx, r.z0 + 3, 20, 5, 4, '#2b6fd6', 10, false);
}
