// Road graph built from OpenStreetMap data (see public/data/southlondon.json; © OpenStreetMap contributors, ODbL).
// Edge = polyline between two junction nodes. Cars drive on the LEFT.
export const CLASS_WIDTH = [12, 10, 8.5, 7];     // total carriageway width per class (A, B, C, residential)
export const CLASS_SPEED = [1.0, 0.9, 0.78, 0.55]; // routing preference
const CELL = 64;

export class RoadNet {
  constructor(data) {
    this.nodes = data.nodes.map(([x, z], id) => ({ id, x, z, out: [] }));
    this.edges = data.edges.map(([a, b, cls, flags, name, flat], id) => {
      const pts = [], cum = [0];
      for (let i = 0; i < flat.length; i += 2) pts.push([flat[i], flat[i + 1]]);
      for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      return { id, a, b, cls, oneway: flags & 1, a23: (flags >> 1) & 1, bridge: (flags >> 2) & 1, name: data.names[name], pts, cum, len: cum[cum.length - 1], width: CLASS_WIDTH[cls] };
    });
    for (const e of this.edges) {
      this.nodes[e.a].out.push({ e, dir: 1 });
      if (!e.oneway) this.nodes[e.b].out.push({ e, dir: -1 });
    }
    // edges that can ARRIVE at a node (for degree checks)
    this.nodes.forEach(n => { n.deg = 0; });
    for (const e of this.edges) { this.nodes[e.a].deg++; this.nodes[e.b].deg++; }
    // spatial grid of edge segments
    this.grid = new Map();
    for (const e of this.edges) {
      for (let i = 0; i < e.pts.length - 1; i++) {
        const [x0, z0] = e.pts[i], [x1, z1] = e.pts[i + 1];
        const pad = e.width / 2 + 2;
        const cx0 = Math.floor((Math.min(x0, x1) - pad) / CELL), cx1 = Math.floor((Math.max(x0, x1) + pad) / CELL);
        const cz0 = Math.floor((Math.min(z0, z1) - pad) / CELL), cz1 = Math.floor((Math.max(z0, z1) + pad) / CELL);
        for (let cz = cz0; cz <= cz1; cz++) for (let cx = cx0; cx <= cx1; cx++) {
          const k = cx + ',' + cz; let l = this.grid.get(k); if (!l) this.grid.set(k, l = []);
          l.push(e.id, i);
        }
      }
    }
    this.ngrid = new Map();
    this.nodes.forEach((n, i) => { const k = Math.floor(n.x / 128) + ',' + Math.floor(n.z / 128); let l = this.ngrid.get(k); if (!l) this.ngrid.set(k, l = []); l.push(i); });
  }

  // lane offset (metres to the left of travel direction)
  laneOffset(e) { return e.oneway ? e.width * 0.12 : e.width * 0.25; }

  // position + tangent at arc-length s of edge e travelled in direction dir (s counts from the start of travel)
  pointAt(e, dir, s) {
    const L = e.len; s = Math.max(0, Math.min(L, s));
    const f = dir === 1 ? s : L - s, cum = e.cum;
    let lo = 0, hi = cum.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= f) lo = m; else hi = m; }
    const [x0, z0] = e.pts[lo], [x1, z1] = e.pts[hi], sl = cum[hi] - cum[lo] || 1, t = (f - cum[lo]) / sl;
    let tx = (x1 - x0) / sl, tz = (z1 - z0) / sl;
    if (dir === -1) { tx = -tx; tz = -tz; }
    return { x: x0 + (x1 - x0) * t, z: z0 + (z1 - z0) * t, tx, tz };
  }
  // same, shifted to the left lane
  lanePoint(e, dir, s, off = this.laneOffset(e)) {
    const p = this.pointAt(e, dir, s); return { x: p.x + p.tz * off, z: p.z - p.tx * off, tx: p.tx, tz: p.tz };
  }

  // nearest road centreline within maxD: { e, s (forward arc-length along pts), d, tx, tz, px, pz } or null
  nearest(x, z, maxD = 40, filter = null) {
    let best = null, bd = maxD;
    const r = Math.ceil(maxD / CELL), cx = Math.floor(x / CELL), cz = Math.floor(z / CELL);
    for (let dz = -r; dz <= r; dz++) for (let dx = -r; dx <= r; dx++) {
      const l = this.grid.get((cx + dx) + ',' + (cz + dz)); if (!l) continue;
      for (let k = 0; k < l.length; k += 2) {
        const e = this.edges[l[k]], i = l[k + 1];
        if (filter && !filter(e)) continue;
        const [x0, z0] = e.pts[i], [x1, z1] = e.pts[i + 1], vx = x1 - x0, vz = z1 - z0, ll = vx * vx + vz * vz || 1;
        let t = ((x - x0) * vx + (z - z0) * vz) / ll; t = Math.max(0, Math.min(1, t));
        const px = x0 + vx * t, pz = z0 + vz * t, d = Math.hypot(x - px, z - pz);
        if (d < bd) { bd = d; const sl = Math.sqrt(ll); best = { e, s: e.cum[i] + t * sl, d, tx: vx / sl, tz: vz / sl, px, pz }; }
      }
    }
    return best;
  }

  // distance from (x,z) to the nearest road's edge (carriageway kerb), ignoring edge ignoreId. Infinity if none within maxD.
  clearance(x, z, ignoreId = -1, maxD = 40) {
    let best = Infinity;
    const r = Math.ceil(maxD / CELL), cx = Math.floor(x / CELL), cz = Math.floor(z / CELL);
    for (let dz = -r; dz <= r; dz++) for (let dx = -r; dx <= r; dx++) {
      const l = this.grid.get((cx + dx) + ',' + (cz + dz)); if (!l) continue;
      for (let k = 0; k < l.length; k += 2) {
        const e = this.edges[l[k]]; if (e.id === ignoreId) continue;
        const i = l[k + 1], [x0, z0] = e.pts[i], [x1, z1] = e.pts[i + 1], vx = x1 - x0, vz = z1 - z0, ll = vx * vx + vz * vz || 1;
        let t = ((x - x0) * vx + (z - z0) * vz) / ll; t = Math.max(0, Math.min(1, t));
        const d = Math.hypot(x - (x0 + vx * t), z - (z0 + vz * t)) - e.width / 2;
        if (d < best) best = d;
      }
    }
    return best;
  }

  nearestNode(x, z) {
    let best = -1, bd = Infinity;
    const cx = Math.floor(x / 128), cz = Math.floor(z / 128);
    for (let r = 1; r <= 6 && best < 0; r++) {
      for (let dz = -r; dz <= r; dz++) for (let dx = -r; dx <= r; dx++) {
        const l = this.ngrid.get((cx + dx) + ',' + (cz + dz)); if (!l) continue;
        for (const i of l) { const n = this.nodes[i], d = Math.hypot(n.x - x, n.z - z); if (d < bd) { bd = d; best = i; } }
      }
    }
    return best;
  }

  // project a point onto edge e: returns arc-length s along the edge's forward (a->b) direction
  project(e, x, z) {
    let bd = Infinity, bs = 0;
    for (let i = 0; i < e.pts.length - 1; i++) {
      const [x0, z0] = e.pts[i], [x1, z1] = e.pts[i + 1], vx = x1 - x0, vz = z1 - z0, ll = vx * vx + vz * vz || 1;
      let t = ((x - x0) * vx + (z - z0) * vz) / ll; t = Math.max(0, Math.min(1, t));
      const d = Math.hypot(x - (x0 + vx * t), z - (z0 + vz * t));
      if (d < bd) { bd = d; bs = e.cum[i] + t * Math.sqrt(ll); }
    }
    return bs;
  }

  // A* over nodes. Returns [{e, dir}, ...] or null. cost = length / speed preference.
  route(from, to) {
    if (from === to) return [];
    const N = this.nodes, g = new Map([[from, 0]]), prev = new Map(), open = [[0, from]], closed = new Set();
    const h = i => Math.hypot(N[i].x - N[to].x, N[i].z - N[to].z);
    const push = it => { open.push(it); let i = open.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (open[p][0] <= open[i][0]) break; [open[p], open[i]] = [open[i], open[p]]; i = p; } };
    const pop = () => { const top = open[0], last = open.pop(); if (open.length) { open[0] = last; let i = 0; for (;;) { let l = 2 * i + 1, r = l + 1, m = i; if (l < open.length && open[l][0] < open[m][0]) m = l; if (r < open.length && open[r][0] < open[m][0]) m = r; if (m === i) break; [open[m], open[i]] = [open[i], open[m]]; i = m; } } return top; };
    let guard = 0;
    while (open.length && guard++ < 60000) {
      const [, cur] = pop();
      if (cur === to) {
        const path = []; let c = to;
        while (c !== from) { const p = prev.get(c); path.push(p.step); c = p.node; }
        return path.reverse();
      }
      if (closed.has(cur)) continue; closed.add(cur);
      for (const o of N[cur].out) {
        const nxt = o.dir === 1 ? o.e.b : o.e.a, cost = g.get(cur) + o.e.len / CLASS_SPEED[o.e.cls];
        if (!g.has(nxt) || cost < g.get(nxt)) { g.set(nxt, cost); prev.set(nxt, { node: cur, step: o }); push([cost + h(nxt) * 0.9, nxt]); }
      }
    }
    return null;
  }

  // centreline polyline of a route (list of {e,dir}) as [[x,z],...]
  routePolyline(route, step = 12) {
    const pts = [];
    for (const r of route) for (let s = 0; s < r.e.len; s += step) { const p = this.pointAt(r.e, r.dir, s); pts.push([p.x, p.z]); }
    if (route.length) { const l = route[route.length - 1], p = this.pointAt(l.e, l.dir, l.e.len); pts.push([p.x, p.z]); }
    return pts;
  }
  endNode(step) { return step.dir === 1 ? step.e.b : step.e.a; }
  startNode(step) { return step.dir === 1 ? step.e.a : step.e.b; }
}
