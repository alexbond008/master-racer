import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

// Real OpenStreetMap building footprints (public/data/buildings.json.gz, © OpenStreetMap contributors, ODbL), extruded into
// houses, terraces, flats, shops and civic buildings. Tiles are streamed in around the player so 76k buildings stay cheap.
const TILE = 256, LOAD_R = 640, UNLOAD_R = 900, STOREY = 3.1;
const PAL = {
  brixton: ['#a2432f', '#b5543a', '#a8935f', '#c8b27c', '#8a6e52', '#d6cdb6', '#7e4540', '#b09a70'],
  peckham: ['#a8935f', '#bfa56a', '#a2432f', '#8a6e52', '#c9bfa0', '#8c3a2c', '#aa9f80'],
  streatham: ['#ad4a33', '#c25d43', '#e0d8c4', '#d6ccb2', '#9a7656', '#a89c7c', '#b86448'],
};
const BRIGHT = { brixton: ['#e63946', '#ffb703', '#2a9d8f', '#3a86ff', '#fb5607', '#06d6a0', '#ffd166'], peckham: ['#e63946', '#ffb703', '#2a9d8f', '#3a86ff', '#fb5607', '#8338ec', '#06d6a0', '#ffd166', '#ff4fa3'], streatham: ['#d62828', '#1d4e89', '#f4f4f4', '#2b9348', '#ffb703'] };
const SLATE = ['#4b4f58', '#565a63', '#3f434b', '#5a5048'], TERRA = ['#9a5a42', '#a8654a', '#8c4f3a'];
const hash = id => { let h = (id * 2654435761) >>> 0; h ^= h >>> 15; return (h >>> 0) / 4294967296; };
const col = (hex, mul = 1) => new THREE.Color(hex).multiplyScalar(mul);

export class OsmBuildings {
  // hooks: { net, districtAt, addObb(cx,cz,th,hx,hz)->handle, removeObb(handle), occAdd(cx,cz,th,hx,hz)->keys, occRemove(keys), skip(x,z,id)->bool }
  constructor(group, data, hooks, bMat, signMat) {
    this.group = group; this.data = data; this.h = hooks; this.bMat = bMat; this.signMat = signMat;
    this.tiles = new Map(); this.loaded = new Map(); this.stats = { buildings: 0 };
    for (const k in data.tiles) this.tiles.set(k, data.tiles[k]);
  }

  update(px, pz, budgetMs = 5) {
    const t0 = performance.now(), cx = Math.floor(px / TILE), cz = Math.floor(pz / TILE), r = Math.ceil(LOAD_R / TILE) + 1;
    const want = [];
    for (let dz = -r; dz <= r; dz++) for (let dx = -r; dx <= r; dx++) {
      const tx = cx + dx, tz = cz + dz, k = tx + ',' + tz; if (!this.tiles.has(k) || this.loaded.has(k)) continue;
      const d = Math.hypot((tx + 0.5) * TILE - px, (tz + 0.5) * TILE - pz); if (d < LOAD_R) want.push([d, k]);
    }
    want.sort((a, b) => a[0] - b[0]);
    for (const [, k] of want) { this.build(k); if (performance.now() - t0 > budgetMs) break; }
    for (const [k, t] of [...this.loaded]) {
      const [tx, tz] = k.split(',').map(Number);
      if (Math.hypot((tx + 0.5) * TILE - px, (tz + 0.5) * TILE - pz) > UNLOAD_R) this.unload(k, t);
    }
  }
  preload(px, pz) { this.update(px, pz, 1e9); }

  unload(k, t) {
    for (const m of t.meshes) { this.group.remove(m); m.geometry.dispose(); }
    for (const o of t.obbs) this.h.removeObb(o);
    for (const keys of t.occ) this.h.occRemove(keys);
    this.stats.buildings -= t.count; this.loaded.delete(k);
  }

  build(key) {
    const recs = this.tiles.get(key), net = this.h.net, bld = [], sign = [];
    const tile = { meshes: [], obbs: [], occ: [], count: 0 };
    this.loaded.set(key, tile);
    const Acc = () => ({ p: [], n: [], uv: [], c: [], i: [] });
    const A = Acc(), S = Acc();
    for (const r of recs) {
      const [id, type, lv10, h10, roofCode, colour, flags, flat] = r;
      const pts = []; { let x = 0, z = 0; for (let i = 0; i < flat.length; i += 2) { x += flat[i]; z += flat[i + 1]; pts.push([x / 10, z / 10]); } }
      let cx = 0, cz = 0; pts.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= pts.length; cz /= pts.length;
      if (this.h.skip(cx, cz, id)) continue;
      if (net.clearance(cx, cz, -1, 12) < 0) continue;            // footprint sits on a carriageway: drop it
      const d = this.h.districtAt(cx, cz), rnd = hash(id);
      // ---- orientation + oriented bounding box from the dominant edge direction
      let bestL = 0, ang = 0; const bins = new Float32Array(18);
      for (let i = 0; i < pts.length; i++) { const a = pts[i], b = pts[(i + 1) % pts.length], ex = b[0] - a[0], ez = b[1] - a[1], l = Math.hypot(ex, ez); let t = Math.atan2(ez, ex) % (Math.PI / 2); if (t < 0) t += Math.PI / 2; const bi = Math.floor(t / (Math.PI / 2) * 18) % 18; bins[bi] += l; }
      bins.forEach((v, i) => { if (v > bestL) { bestL = v; ang = (i + 0.5) / 18 * Math.PI / 2; } });
      const ux = Math.cos(ang), uz = Math.sin(ang), vx = -uz, vz = ux;
      let u0 = 1e9, u1 = -1e9, v0 = 1e9, v1 = -1e9; pts.forEach(p => { const u = p[0] * ux + p[1] * uz, v = p[0] * vx + p[1] * vz; u0 = Math.min(u0, u); u1 = Math.max(u1, u); v0 = Math.min(v0, v); v1 = Math.max(v1, v); });
      let au = (u1 - u0) / 2, av = (v1 - v0) / 2; const ocx = ((u0 + u1) / 2) * ux + ((v0 + v1) / 2) * vx, ocz = ((u0 + u1) / 2) * uz + ((v0 + v1) / 2) * vz;
      let area = 0; pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; area += p[0] * q[1] - q[0] * p[1]; }); area = Math.abs(area) / 2;
      const rectish = area / (4 * au * av) > 0.8;
      // long axis (a) / short axis (b) of the box
      let a = au, b = av, lux = ux, luz = uz; if (b > a) { a = av; b = au; lux = vx; luz = vz; }
      // ---- height
      let H = h10 / 10;
      if (!H && lv10) H = lv10 / 10 * STOREY + 0.6;
      if (!H) {
        const fl = type === 3 ? 4 + Math.floor(rnd * 3) : type === 4 ? (area > 900 ? 2 : 2 + Math.floor(rnd * 2)) : type === 5 ? 2.4 : type === 6 ? 1 : type === 7 ? 3.6 : type === 8 ? 3 : type === 2 ? 2 + Math.floor(rnd * 2) : type === 1 ? 2 : (area < 45 ? 1 : area < 260 ? 2 + Math.floor(rnd * 2) : 3 + Math.floor(rnd * 2));
        H = fl * STOREY + 0.5;
      }
      H = Math.max(2.6, H);
      // ---- roof
      let roof = roofCode;
      if (!roof) roof = ((type === 1 || type === 2 || type === 0) && area < 220 && H < 11 && rectish && b < 9) ? 2 : (type === 7 && rectish ? 2 : 1);
      if (roof >= 2 && !rectish) roof = 1;
      const pitched = roof === 2 || roof === 3 || roof === 4;
      const rise = pitched ? Math.min(4.2, Math.max(1.6, b * 0.6)) : 0, E = pitched ? Math.max(2.4, H - rise) : H;
      // ---- colours
      const wall = new THREE.Color(colour >= 0 ? colour : PAL[d][Math.floor(rnd * PAL[d].length)]);
      if (colour < 0) wall.offsetHSL((hash(id + 7) - 0.5) * 0.02, (hash(id + 11) - 0.5) * 0.08, (hash(id + 3) - 0.5) * 0.08);
      if (type === 4 || type === 8) wall.lerp(new THREE.Color('#cfc7b4'), 0.4);
      if (type === 5) wall.lerp(new THREE.Color('#8b8d90'), 0.7);
      const roofC = new THREE.Color(rnd < 0.62 ? SLATE[Math.floor(rnd * 99) % SLATE.length] : TERRA[Math.floor(rnd * 99) % TERRA.length]);
      const flatC = new THREE.Color('#4a4b50');
      // ---- walls (outward normal = (ez,-ex) because footprints are wound with positive shoelace area)
      let run = hash(id + 5) * 4, floors = Math.max(1, Math.round(E / STOREY));
      const wallsToRoad = [];
      for (let i = 0; i < pts.length; i++) {
        const p0 = pts[i], p1 = pts[(i + 1) % pts.length], ex = p1[0] - p0[0], ez = p1[1] - p0[1], len = Math.hypot(ex, ez); if (len < 0.3) continue;
        const nx = ez / len, nz = -ex / len, ox = Math.floor(hash(id * 3 + i) * 4) / 4, oy = Math.floor(hash(id * 5 + i) * 4) / 4;
        const u0w = len > 1.4 ? run / 4 + ox : 0.01, u1w = len > 1.4 ? u0w + len / 3.5 / 4 : 0.012, vTop = len > 1.4 ? oy + E / STOREY / 4 : 0.012, vBot = len > 1.4 ? oy : 0.01;
        run += len / 3.5;
        const base = A.p.length / 3;
        A.p.push(p0[0], 0, p0[1], p1[0], 0, p1[1], p1[0], E, p1[1], p0[0], E, p0[1]);
        for (let k = 0; k < 4; k++) A.n.push(nx, 0, nz);
        A.uv.push(u0w, vBot, u1w, vBot, u1w, vTop, u0w, vTop);
        for (let k = 0; k < 4; k++) A.c.push(wall.r, wall.g, wall.b);
        A.i.push(base, base + 3, base + 2, base, base + 2, base + 1);
        if (len > 2.6) wallsToRoad.push([p0, p1, nx, nz, len]);
      }
      // stone cornice / parapet band along the eaves of every wall (Victorian look)
      const cornC = wall.clone().lerp(new THREE.Color('#e8e0cc'), 0.55);
      if (E > 4.5 && (type !== 5 && type !== 6)) for (let i = 0; i < pts.length; i++) {
        const p0 = pts[i], p1 = pts[(i + 1) % pts.length], ex = p1[0] - p0[0], ez = p1[1] - p0[1], len = Math.hypot(ex, ez); if (len < 1.2) continue;
        const nx = ez / len, nz = -ex / len, o = 0.16, y0 = E - 0.55, y1 = E + 0.12, base = A.p.length / 3;
        A.p.push(p0[0] + nx * o, y0, p0[1] + nz * o, p1[0] + nx * o, y0, p1[1] + nz * o, p1[0] + nx * o, y1, p1[1] + nz * o, p0[0] + nx * o, y1, p0[1] + nz * o);
        for (let k = 0; k < 4; k++) { A.n.push(nx, 0, nz); A.uv.push(0.012, 0.012); A.c.push(cornC.r, cornC.g, cornC.b); }
        A.i.push(base, base + 3, base + 2, base, base + 2, base + 1);
      }
      // ---- roof geometry
      const roofPush = (v, nrm, colr) => { const base = A.p.length / 3; A.p.push(v[0], v[1], v[2]); A.n.push(nrm[0], nrm[1], nrm[2]); A.uv.push(0.012, 0.012); A.c.push(colr.r, colr.g, colr.b); return base; };
      if (!pitched) {
        const contour = pts.map(p => new THREE.Vector2(p[0], p[1])), tris = THREE.ShapeUtils.triangulateShape(contour, []);
        const idx = pts.map(p => roofPush([p[0], H, p[1]], [0, 1, 0], flatC));
        for (const t of tris) { // make sure the face points up
          const A0 = pts[t[0]], B0 = pts[t[1]], C0 = pts[t[2]], cr = (B0[0] - A0[0]) * (C0[1] - A0[1]) - (B0[1] - A0[1]) * (C0[0] - A0[0]);
          if (cr > 0) A.i.push(idx[t[0]], idx[t[2]], idx[t[1]]); else A.i.push(idx[t[0]], idx[t[1]], idx[t[2]]);
        }
      } else {
        // box frame: long axis (lux,luz), short axis (-luz,lux), centre (ocx,ocz)
        const sx = -luz, sz = lux, over = 0.25, aa = a + over, bb = b + over;
        const P = (l, s, y) => [ocx + lux * l + sx * s, y, ocz + luz * l + sz * s];
        const ridgeA = roof === 2 ? aa : Math.max(0, a - b * 0.9), top = E + rise;
        const quad = (p0, p1, p2, p3, c) => { // counter-clockwise seen from outside/above; normal from cross
          const ux2 = p1[0] - p0[0], uy = p1[1] - p0[1], uz2 = p1[2] - p0[2], wx = p3[0] - p0[0], wy = p3[1] - p0[1], wz = p3[2] - p0[2];
          let nx2 = uy * wz - uz2 * wy, ny = uz2 * wx - ux2 * wz, nz2 = ux2 * wy - uy * wx; const l = Math.hypot(nx2, ny, nz2) || 1; nx2 /= l; ny /= l; nz2 /= l;
          const up = ny >= 0, base = [p0, p1, p2, p3].map(v => roofPush(v, up ? [nx2, ny, nz2] : [-nx2, -ny, -nz2], c));
          if (up) A.i.push(base[0], base[1], base[2], base[0], base[2], base[3]); else A.i.push(base[0], base[3], base[2], base[0], base[2], base[1]);
        };
        // two main slopes (gabled) or four (hipped)
        quad(P(-aa, -bb, E - 0.1), P(aa, -bb, E - 0.1), P(ridgeA, 0, top), P(-ridgeA, 0, top), roofC);
        quad(P(aa, bb, E - 0.1), P(-aa, bb, E - 0.1), P(-ridgeA, 0, top), P(ridgeA, 0, top), roofC);
        if (roof === 2) { // gable-end triangles
          for (const sgn of [-1, 1]) { const g0 = P(sgn * a, -b, E), g1 = P(sgn * a, b, E), g2 = P(sgn * a, 0, top); const base = [g0, g1, g2].map(v => roofPush(v, [lux * sgn, 0, luz * sgn], wall)); A.i.push(...(sgn > 0 ? [base[0], base[2], base[1]] : [base[0], base[1], base[2]])); }
        } else if (ridgeA < aa) { // hip ends
          for (const sgn of [-1, 1]) { const q0 = P(sgn * aa, bb, E - 0.1), q1 = P(sgn * aa, -bb, E - 0.1), q2 = P(sgn * ridgeA, 0, top); const nrm = [lux * sgn * 0.6, 0.8, luz * sgn * 0.6]; const base = [q0, q1, q2].map(v => roofPush(v, nrm, roofC)); A.i.push(...(sgn > 0 ? [base[0], base[2], base[1]] : [base[0], base[1], base[2]])); }
        }
        // chimney stacks on terraces/houses
        if ((type === 1 || type === 2 || type === 0) && hash(id + 13) < 0.65) {
          const ch = col('#7a4538'), s = hash(id + 17) < 0.5 ? -1 : 1, cxp = ocx + lux * (a * 0.55 * s), czp = ocz + luz * (a * 0.55 * s), yb = E + rise * 0.55, cw = 0.55;
          for (const [dx, dz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { /* four faces */ void dx; void dz; }
          const x0 = cxp - cw / 2, x1 = cxp + cw / 2, z0 = czp - cw / 2, z1 = czp + cw / 2, y1 = top + 0.9;
          const faces = [[[x0, yb, z1], [x1, yb, z1], [x1, y1, z1], [x0, y1, z1], [0, 0, 1]], [[x1, yb, z0], [x0, yb, z0], [x0, y1, z0], [x1, y1, z0], [0, 0, -1]], [[x1, yb, z1], [x1, yb, z0], [x1, y1, z0], [x1, y1, z1], [1, 0, 0]], [[x0, yb, z0], [x0, yb, z1], [x0, y1, z1], [x0, y1, z0], [-1, 0, 0]], [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [0, 1, 0]]];
          for (const f of faces) { const bb2 = f.slice(0, 4).map(v => roofPush(v, f[4], ch)); A.i.push(bb2[0], bb2[1], bb2[2], bb2[0], bb2[2], bb2[3]); }
        }
      }
      // ---- shopfronts on walls facing a main road
      if (wallsToRoad.length && (flags & 1 || type === 4 || (type !== 1 && type !== 6 && type !== 5 && floors >= 2 && hash(id + 19) < 0.4))) {
        const fc = col(BRIGHT[d][Math.floor(hash(id + 23) * BRIGHT[d].length)], 1.05), warm = new THREE.Color(1.35, 0.95, 0.55).multiplyScalar(0.7 + hash(id + 29) * 0.35);
        for (const [p0, p1, nx, nz, len] of wallsToRoad) {
          const mx = (p0[0] + p1[0]) / 2, mz = (p0[1] + p1[1]) / 2, nr = net.nearest(mx + nx * 2, mz + nz * 2, 26, e => e.cls <= 2); if (!nr) continue;
          const dx = nr.px - mx, dz = nr.pz - mz, dl = Math.hypot(dx, dz) || 1; if ((dx * nx + dz * nz) / dl < 0.75) continue;
          const strip = (y0, y1, off, c, panes) => {
            const o = off, base = S.p.length / 3, ex = (p1[0] - p0[0]) / len, ez = (p1[1] - p0[1]) / len, m = 0.5, a0 = [p0[0] + ex * m + nx * o, p0[1] + ez * m + nz * o], a1 = [p1[0] - ex * m + nx * o, p1[1] - ez * m + nz * o];
            S.p.push(a0[0], y0, a0[1], a1[0], y0, a1[1], a1[0], y1, a1[1], a0[0], y1, a0[1]);
            const u1 = panes ? (len - 2 * m) / 2.6 : 0.01;
            for (let k = 0; k < 4; k++) { S.n.push(nx, 0, nz); S.c.push(c.r, c.g, c.b); }
            if (panes) S.uv.push(0, 0, u1, 0, u1, 1, 0, 1); else S.uv.push(0.508, 0.03, 0.51, 0.03, 0.51, 0.04, 0.508, 0.04);
            S.i.push(base, base + 3, base + 2, base, base + 2, base + 1);
          };
          strip(0.45, 3.05, 0.07, warm, true); strip(3.1, 4.0, 0.2, fc, false);
        }
      }
      // ---- collision + line-of-sight footprint (the oriented box)
      const th = Math.atan2(lux, luz);
      tile.obbs.push(this.h.addObb(ocx, ocz, th, b, a)); tile.occ.push(this.h.occAdd(ocx, ocz, th, b, a)); tile.count++;
    }
    const mesh = (acc, mat, flatShade) => {
      if (!acc.i.length) return null;
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(acc.p, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(acc.n, 3));
      g.setAttribute('uv', new THREE.Float32BufferAttribute(acc.uv, 2)); g.setAttribute('color', new THREE.Float32BufferAttribute(acc.c, 3));
      g.setIndex(acc.i); g.computeBoundingSphere(); const m = new THREE.Mesh(g, mat); void flatShade; if (mat === this.bMat) { m.castShadow = true; m.receiveShadow = true; } return m;
    };
    for (const [acc, mat] of [[A, this.bMat], [S, this.signMat]]) { const m = mesh(acc, mat); if (m) { this.group.add(m); tile.meshes.push(m); } }
    this.stats.buildings += tile.count; void bld; void sign;
  }
}
