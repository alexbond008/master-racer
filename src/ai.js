import { CELL, N } from './world.js';
import { MASS } from './cars.js';

const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
export const massOf = def => def.mass || MASS[def.id] || 1300;
// UK: drive on the LEFT. left of travel direction d=(dx,dz) is (dz,-dx).
const leftOf = ([dx, dz]) => [dz, -dx];
const LANE = 4.5, ENTRY = 10;

// Follows the road grid, choosing a direction at every intersection via `choose`.
export class LaneDriver {
  constructor(offset = LANE) { this.offset = offset; this.i = 0; this.j = 0; this.d = [1, 0]; this.stage = 'entry'; this.wx = 0; this.wz = 0; }

  // Put the driver on road (ni,nj) travelling dir d, heading for node (ni,nj).
  aim(ni, nj, d) { this.i = ni; this.j = nj; this.d = d; this.stage = 'entry'; this.#setEntry(); }

  // Re-sync from an arbitrary car pose: take the road along its dominant heading axis.
  resync(car) {
    const sn = Math.sin(car.th), cs = Math.cos(car.th);
    // which road is the car physically on? (within the 18 m carriageway of a vertical or horizontal road)
    const rx = Math.round(car.x / CELL), rz = Math.round(car.z / CELL);
    const onV = Math.abs(car.x - rx * CELL) < 10, onH = Math.abs(car.z - rz * CELL) < 10;
    const alongX = onH && !onV ? true : onV && !onH ? false : Math.abs(sn) > Math.abs(cs);
    const d = alongX ? [sn >= 0 ? 1 : -1, 0] : [0, cs >= 0 ? 1 : -1];
    let ni, nj;
    if (alongX) { nj = rz; ni = d[0] > 0 ? Math.floor(car.x / CELL) + 1 : Math.ceil(car.x / CELL) - 1; }
    else { ni = rx; nj = d[1] > 0 ? Math.floor(car.z / CELL) + 1 : Math.ceil(car.z / CELL) - 1; }
    ni = clamp(ni, 0, N); nj = clamp(nj, 0, N);
    this.aim(ni, nj, d);
  }

  #setEntry() {
    const l = leftOf(this.d);
    this.wx = this.i * CELL - this.d[0] * ENTRY + l[0] * this.offset;
    this.wz = this.j * CELL - this.d[1] * ENTRY + l[1] * this.offset;
  }

  // advance waypoint state; returns [x,z] to steer at. choose(i,j,d,options)->dir
  target(car, choose) {
    const dx = this.wx - car.x, dz = this.wz - car.z;
    const dd = this.stage === 'exit' ? this.nd : this.d;
    const ahead = dx * dd[0] + dz * dd[1];
    if (ahead < 3 || Math.hypot(dx, dz) < 3) {
      if (this.stage === 'entry') {
        // pick next direction
        const opts = DIRS.filter(([x, z]) => !(x === -this.d[0] && z === -this.d[1]) && this.i + x >= 0 && this.i + x <= N && this.j + z >= 0 && this.j + z <= N);
        const nd = opts.length ? choose(this.i, this.j, this.d, opts) : [-this.d[0], -this.d[1]];
        const l = leftOf(nd);
        this.nd = nd;
        this.wx = this.i * CELL + nd[0] * ENTRY + l[0] * this.offset;
        this.wz = this.j * CELL + nd[1] * ENTRY + l[1] * this.offset;
        this.stage = 'exit';
      } else {
        this.d = this.nd; this.i += this.d[0]; this.j += this.d[1];
        this.i = clamp(this.i, 0, N); this.j = clamp(this.j, 0, N);
        this.stage = 'entry'; this.#setEntry();
      }
    }
    return [this.wx, this.wz];
  }
}

export const randomTurn = (i, j, d, opts) => {
  const straight = opts.find(o => o[0] === d[0] && o[1] === d[1]);
  if (straight && Math.random() < 0.6) return straight;
  return opts[Math.floor(Math.random() * opts.length)];
};

// Produce control inputs to drive `car` toward (tx,tz) at ~targetSpeed (m/s). `inp` is reused/mutated.
export function steerToward(car, tx, tz, targetSpeed, inp, aggression = 1, corner = 0) {
  const err = wrap(Math.atan2(tx - car.x, tz - car.z) - car.th);
  const vf = car.fwdSpeed;
  const want = clamp(-err * 1.7, -1, 1);
  inp.steer += (want - inp.steer) * 0.35;
  const sp = targetSpeed * (1 - 0.6 * Math.min(1, Math.abs(err) / 1.1)) * (1 - 0.5 * Math.min(1, corner / 1.0));
  inp.throttle = 0; inp.brake = 0; inp.handbrake = false; inp.nitro = false;
  if (vf < sp - 0.4) inp.throttle = clamp((sp - vf) / 3, 0.15, 1);
  else if (vf > sp + 1.0) inp.brake = clamp((vf - sp) / (5 / aggression), 0, 1);
  return err;
}

export function newInput() { return { throttle: 0, brake: 0, steer: 0, handbrake: false, nitro: false }; }

// ---- car vs car (two circles each + impulse). returns impact speed (m/s) or 0.
function circles(c) {
  const h = c.def.L / 2 - c.def.W * 0.5, r = c.def.W * 0.5 * 0.95, sn = Math.sin(c.th), cs = Math.cos(c.th);
  return [{ x: c.x + sn * h, z: c.z + cs * h, r, off: h }, { x: c.x - sn * h, z: c.z - cs * h, r, off: -h }];
}
export function carVsCar(a, b) {
  const dx = b.x - a.x, dz = b.z - a.z, reach = (a.def.L + b.def.L) * 0.5 + 0.5;
  if (dx * dx + dz * dz > reach * reach) return 0;
  const ma = massOf(a.def), mb = massOf(b.def), tm = ma + mb;
  let impact = 0;
  for (const pa of circles(a)) for (const pb of circles(b)) {
    const ex = pb.x - pa.x, ez = pb.z - pa.z, d = Math.hypot(ex, ez), rr = pa.r + pb.r;
    if (d >= rr || d < 1e-4) continue;
    const nx = ex / d, nz = ez / d, pen = rr - d;
    a.x -= nx * pen * mb / tm; a.z -= nz * pen * mb / tm; b.x += nx * pen * ma / tm; b.z += nz * pen * ma / tm;
    const vn = (b.vx - a.vx) * nx + (b.vz - a.vz) * nz;
    if (vn < 0) {
      const j = -1.35 * vn / (1 / ma + 1 / mb);
      a.vx -= j * nx / ma; a.vz -= j * nz / ma; b.vx += j * nx / mb; b.vz += j * nz / mb;
      // off-centre hits spin the cars
      const ta = (pa.off * Math.cos(a.th)) * (-j * nx) - (pa.off * Math.sin(a.th)) * (-j * nz);
      const tb = (pb.off * Math.cos(b.th)) * (j * nx) - (pb.off * Math.sin(b.th)) * (j * nz);
      a.yawRate += clamp(ta / (ma * 1.8), -2.5, 2.5); b.yawRate += clamp(tb / (mb * 1.8), -2.5, 2.5);
      impact = Math.max(impact, -vn);
    }
  }
  return impact;
}

// ---- graph driver: follows OSM road edges in the left lane, picks an exit at every junction via choose(options, node, edge)
export class NetDriver {
  constructor(net, laneMul = 1) { this.net = net; this.e = null; this.dir = 1; this.s = 0; this.next = null; this.laneMul = laneMul; }
  off(e) { return this.net.laneOffset(e) * this.laneMul; }
  aim(e, dir = 1, s = 0) { this.e = e; this.dir = e.oneway ? 1 : dir; this.s = s; this.next = null; }
  // snap onto the road the car is on, travelling the way it faces
  resync(car) {
    const nr = this.net.nearest(car.x, car.z, 80); if (!nr) return false;
    const dir = nr.tx * Math.sin(car.th) + nr.tz * Math.cos(car.th) >= 0 ? 1 : -1, e = nr.e, d = e.oneway ? 1 : dir;
    this.e = e; this.dir = d; this.s = d === 1 ? nr.s : e.len - nr.s; this.next = null; return true;
  }
  endNode() { return this.dir === 1 ? this.e.b : this.e.a; }
  _decide(choose) {
    const node = this.net.nodes[this.endNode()];
    let opts = node.out.filter(o => o.e !== this.e);
    if (!opts.length) opts = node.out.filter(o => o.e === this.e);   // dead end: turn round
    if (!opts.length) return { e: this.e, dir: -this.dir };              // one-way trap
    return choose(opts, node, this.e) || opts[0];
  }
  // returns [x, z, corner] : look-ahead point on the lane, and how sharp the road bends ahead (radians)
  target(car, choose, look = 16) {
    const net = this.net;
    for (let guard = 0; guard < 4; guard++) {
      const e = this.e, sf = net.project(e, car.x, car.z);
      this.s = this.dir === 1 ? sf : e.len - sf;
      if (this.s > e.len - 2.5) { if (!this.next) this.next = this._decide(choose); this.e = this.next.e; this.dir = this.next.dir; this.s = 0; this.next = null; continue; }
      break;
    }
    const e = this.e, pt = d => {
      const a = this.s + d;
      if (a <= e.len) return net.lanePoint(e, this.dir, a, this.off(e));
      if (!this.next) this.next = this._decide(choose);
      const n = this.next; return net.lanePoint(n.e, n.dir, Math.min(a - e.len, n.e.len), this.off(n.e));
    };
    const p1 = pt(look), p2 = pt(look + 32);
    const a1 = Math.atan2(p1.x - car.x, p1.z - car.z), a2 = Math.atan2(p2.x - p1.x, p2.z - p1.z);
    const corner = Math.abs(Math.atan2(Math.sin(a2 - a1), Math.cos(a2 - a1)));
    return [p1.x, p1.z, corner];
  }
}
export const randomExit = (opts, node, e) => {
  const straight = opts.reduce((b, o) => { const ex = e.dir, t = 0; void ex; void t; return b; }, null); void straight;
  return opts[Math.floor(Math.random() * opts.length)];
};
