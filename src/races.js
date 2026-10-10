import * as THREE from 'three';
import { Agent } from './traffic.js';
import { steerToward, newInput } from './ai.js';
import { updateCarModel } from './carModel.js';
import { CARS } from './cars.js';

// The Five: sequential pink-slip rivals. Win => take their car.
export const RIVALS = [
  { id: 'kev', name: "KEV 'CORSA' BRADLEY", district: 'BRIXTON', car: 'corsa', color: '#7bd31a', weather: 'clear', slipFree: true,
    quote: "Oi, Maluch! Is that a car or a biscuit tin? Keep your tin. I'll put my Corsa on the line, you've got nothing I want.",
    win: "Okay, okay. The Corsa's yours. Mind the clutch, it bites.", lose: "Told you. Go home to Zamość, bruv." },
  { id: 'drez', name: 'LADY DREZ', district: 'PECKHAM', car: 'impreza', color: '#e9f2ff', weather: 'rain', slipFree: false,
    quote: "Peckham don't do tourists. Put your wheels up, I'll put my Impreza. Loser walks.",
    win: "Hmph. Keys are in the glovebox. Don't scratch her.", lose: "Rye Lane sends its regards." },
  { id: 'oj', name: 'BIG OJ', district: 'STREATHAM', car: 'gtr', color: '#15171c', weather: 'clear', slipFree: false,
    quote: "Streatham's mine. Four turbos, one rule: I don't lose. You want the GT-R? Come take it.",
    win: "...Respect. Take the R. Next one's nastier.", lose: "Another one for the collection." },
  { id: 'deacon', name: 'THE DEACON', district: 'BRIXTON ARCHES', car: 'f40', color: '#0c0c0e', weather: 'snow', slipFree: false,
    quote: "Under the arches, where the railway hums. Twin turbo V8, no electronics. Say your prayers, Polish.",
    win: "The Lord giveth. Go. Find Tanaka.", lose: "Amen." },
  { id: 'tanaka', name: "RYU 'SAKURA' TANAKA", district: 'PECKHAM LEVELS', car: 'lambo', color: '#ff4fa3', weather: 'storm', slipFree: false,
    quote: "Tokyo drift, London rain. Seven wins. Nobody takes the Sakura. Show me what a Maluch can become.",
    win: "Hah! The king of the south has a new name. Wojtek.", lose: "Sayonara, Maluch." },
];

const polyLen = pts => pts.reduce((s, p, i) => s + (i ? Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);
const CP_SPACING = 105;

export class RaceSystem {
  constructor(scene, world) {
    this.scene = scene; this.world = world; this.net = world.net; this.plans = new Map();
    this.state = null;
    this.pins = RIVALS.map((r, i) => this.makePin(r, i));
    this.beaconA = this.makeBeam(0.9); this.beaconB = this.makeBeam(0.35);
    this.beaconA.visible = this.beaconB.visible = false;
  }

  makeBeam(op) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 60, 16, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.4, 2.2, 1.0), transparent: true, opacity: 0.3 * op, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    this.scene.add(m); return m;
  }
  makePin(r, i) {
    const g = new THREE.Group();
    const ring = new THREE.Mesh(new THREE.RingGeometry(5, 7, 40), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2.2, 0.2), transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
    ring.rotation.x = -Math.PI / 2; ring.position.y = 0.08; g.add(ring);
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 50, 8, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2.2, 0.2), transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    beam.position.y = 25; g.add(beam);
    const cv = document.createElement('canvas'); cv.width = 512; cv.height = 128; const x = cv.getContext('2d');
    x.fillStyle = 'rgba(0,0,0,.65)'; x.fillRect(0, 0, 512, 128); x.strokeStyle = '#ffb400'; x.lineWidth = 6; x.strokeRect(3, 3, 506, 122);
    x.fillStyle = '#ffb400'; x.font = 'bold 30px "Arial Narrow", Arial'; x.textAlign = 'center'; x.fillText(`PINK SLIP ${i + 1}/5`, 256, 42);
    x.fillStyle = '#fff'; x.font = 'bold 40px "Arial Narrow", Arial'; x.fillText(r.name, 256, 90);
    const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
    const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true })); label.scale.set(16, 4, 1); label.position.y = 13; label.renderOrder = 20;
    g.add(label);
    const st = this.startPos(i); g.position.set(st[0], 0, st[1]);
    this.scene.add(g);
    return { g, ring, beam, label, r };
  }

  refreshPins(save) {
    this.pins.forEach((p, i) => {
      const beaten = i < save.raceIdx, locked = i > save.raceIdx;
      p.g.visible = !beaten;
      const c = locked ? new THREE.Color(0.5, 0.5, 0.55) : new THREE.Color(3, 2.2, 0.2);
      p.ring.material.color.copy(c); p.beam.material.color.copy(c); p.beam.material.opacity = locked ? 0.1 : 0.35;
      p.label.visible = !locked || true;
    });
  }

  // nearest unlocked, un-beaten pin the player is parked at
  pinAt(player, save) {
    if (this.state) return -1;
    const i = save.raceIdx; if (i >= RIVALS.length) return -1;
    const st = this.startPos(i), d = Math.hypot(player.x - st[0], player.z - st[1]);
    return d < 13 && player.speed < 9 ? i : -1;
  }

  // the start pin sits on the real road node nearest the chosen start point
  startPos(i) { const n = this.net.nodes[this.net.nearestNode(...this.world.places.races[i].start)]; return [n.x, n.z]; }
  startPose(i) { const st = this.plan(i).steps[0], p = this.net.lanePoint(st.e, st.dir, 3); return { x: p.x, z: p.z, th: Math.atan2(p.tx, p.tz) }; }

  // plan a race: A* legs between the real start/via points -> route steps + checkpoints every ~105 m
  plan(i) {
    if (this.plans.has(i)) return this.plans.get(i);
    const pl = this.world.places.races[i], net = this.net, pts = [pl.start, ...pl.via].map(p => net.nearestNode(p[0], p[1]));
    const steps = [];
    for (let k = 0; k < pts.length - 1; k++) { if (pts[k] === pts[k + 1]) continue; const r = net.route(pts[k], pts[k + 1]); if (r) steps.push(...r); }
    const line = net.routePolyline(steps, 6), cps = []; let acc = 0;
    for (let k = 1; k < line.length; k++) { acc += Math.hypot(line[k][0] - line[k - 1][0], line[k][1] - line[k - 1][1]); if (acc >= CP_SPACING) { cps.push(line[k]); acc = 0; } }
    const last = line[line.length - 1]; if (!cps.length || Math.hypot(cps[cps.length - 1][0] - last[0], cps[cps.length - 1][1] - last[1]) > 25) cps.push(last);
    const plan = { steps, cps, len: polyLen(line), line };
    this.plans.set(i, plan); return plan;
  }
  routeInfo(i) { const p = this.plan(i); return { cps: p.cps, len: p.len }; }

  begin(i, player, playerDef, hooks) {
    const r = RIVALS[i], plan = this.plan(i), cps = plan.cps, net = this.net, st0 = plan.steps[0];
    const p0 = net.pointAt(st0.e, st0.dir, 2), th = Math.atan2(p0.tx, p0.tz), s0 = [p0.x, p0.z];
    const pts = [s0, ...cps];
    const cum = []; let acc = 0; for (let k = 1; k < pts.length; k++) { acc += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]); cum.push(acc); }

    const rival = new Agent(this.scene, net, r.car, { color: r.color, laneMul: 0.55, lite: false, kind: 'rival', hp: 999 });
    const base = CARS[r.car];
    rival.def = { ...base, vmax: Math.min(base.vmax, playerDef.vmax * (0.98 + 0.02 * i)), t60: Math.max(base.t60, playerDef.t60 * 0.95) };
    rival.phys.setDef(rival.def); rival.baseVmax = rival.def.vmax;
    // side by side on the start line (player left lane, rival right lane), 2 m behind the first point
    rival.phys.place(p0.x - p0.tz * 2.4 - p0.tx * 2, p0.z + p0.tx * 2.4 - p0.tz * 2, th);
    rival.cp = 0; rival.reverseT = 0; rival.stuck = 0;
    rival.ri = 1; rival.drv.aim(st0.e, st0.dir, 2); rival.route = plan.steps;
    hooks.placePlayer(p0.x + p0.tz * 2.4 - p0.tx * 2, p0.z - p0.tx * 2.4 - p0.tz * 2, th);

    this.state = { i, r, cps, cum, total: acc, pts, stage: 'countdown', cd: 3.99, cp: 0, t: 0, rival, wager: null, result: null, lastNum: 4, line: plan.line };
    this.beaconA.visible = this.beaconB.visible = true;
    return this.state;
  }

  progressOf(k, x, z) {
    const st = this.state, prev = k > 0 ? st.cum[k - 1] : 0, seg = st.cum[Math.min(k, st.cum.length - 1)] - prev;
    const tgt = st.cps[Math.min(k, st.cps.length - 1)];
    return prev + Math.max(0, seg - Math.hypot(tgt[0] - x, tgt[1] - z));
  }

  // returns { lock } ; hooks: banner, onEnd(result), toast
  update(dt, player, ctx, hooks) {
    const st = this.state; if (!st) return { lock: false };
    this.grip = ctx.grip;
    const rv = st.rival, rp = rv.phys;

    // ---- rival driving (always simulated; locked during countdown)
    const STEP = 1 / 60; rv.acc += dt; let n = 0;
    while (rv.acc >= STEP && n++ < 4) {
      if (st.stage === 'racing') this.driveRival(rv, st, player);
      else { rv.inp.throttle = 0; rv.inp.brake = 1; rv.inp.steer = 0; }
      rp.step(STEP, rv.inp, ctx.grip, this.world.collide);
      rv.acc -= STEP;
    }
    if (rv.acc > STEP * 4) rv.acc = 0;
    rv.model.position.set(rp.x, 0, rp.z); rv.model.rotation.y = rp.th; updateCarModel(rv.model, rp, dt);

    // ---- countdown
    if (st.stage === 'countdown') {
      st.cd -= dt; const num = Math.ceil(st.cd);
      if (num !== st.lastNum && num > 0) { st.lastNum = num; hooks.banner(String(num), '#ffb400', '', 0.9); }
      if (st.cd <= 0) { st.stage = 'racing'; hooks.banner('GO!', '#3ddc84', '', 1.0); }
    } else if (st.stage === 'racing') {
      st.t += dt;
      // player checkpoints
      const c = st.cps[st.cp];
      if (c && Math.hypot(player.x - c[0], player.z - c[1]) < 22) {
        st.cp++; hooks.toast(st.cp >= st.cps.length ? 'FINISH!' : `CHECKPOINT ${st.cp}/${st.cps.length}`);
      }
      // rival checkpoints
      const rc = st.cps[rv.cp];
      if (rc && Math.hypot(rp.x - rc[0], rp.z - rc[1]) < 16) rv.cp++;
      if (st.cp >= st.cps.length) this.end('win', hooks);
      else if (rv.cp >= st.cps.length) this.end('lose', hooks);
    }

    // beacons
    const A = st.cps[Math.min(st.cp, st.cps.length - 1)], B = st.cps[Math.min(st.cp + 1, st.cps.length - 1)];
    this.beaconA.position.set(A[0], 30, A[1]); this.beaconB.position.set(B[0], 30, B[1]);
    this.beaconB.visible = st.cp + 1 < st.cps.length;
    return { lock: st.stage === 'countdown' };
  }

  driveRival(rv, st, player) {
    const p = rv.phys, base = rv.baseVmax;
    // rubber band against the player along the route
    const pp = this.progressOf(st.cp, player.x, player.z), rpg = this.progressOf(rv.cp, p.x, p.z), gap = rpg - pp; // + = rival ahead
    let vmax = base * (gap > 90 ? 0.88 : gap > 40 ? 0.95 : gap < -70 ? 1.12 : gap < -30 ? 1.05 : 1);
    vmax = Math.min(vmax, CARS[st.r.car].vmax);
    p.def.vmax = vmax;
    if (rv.reverseT > 0) { rv.reverseT -= 1 / 60; rv.inp.throttle = 0; rv.inp.brake = 1; rv.inp.steer = -Math.sign(rv.inp.steer || 1) * 0.9; if (rv.reverseT <= 0) rv.drv.resync(p); return; }
    const choose = opts => { const nx = rv.route[rv.ri++]; return (nx && opts.find(o => o.e === nx.e && o.dir === nx.dir)) || opts[0]; };
    const [tx, tz, corner] = rv.drv.target(p, choose, 16 + p.speed * 0.45);
    steerToward(p, tx, tz, vmax * (0.9 + 0.1 * Math.min(1, this.grip + 0.1)) * [1.1, 1, 0.9, 0.78][rv.drv.e.cls], rv.inp, 1.8, corner);
    if (Math.abs(p.fwdSpeed) < 1.2 && rv.inp.throttle > 0.1) { rv.stuck += 1 / 60; if (rv.stuck > 1.3) { rv.reverseT = 1.0; rv.stuck = 0; } } else rv.stuck = Math.max(0, rv.stuck - 1 / 60);
  }

  end(result, hooks) {
    const st = this.state; if (!st || st.stage === 'done') return;
    st.stage = 'done'; st.result = result;
    this.beaconA.visible = this.beaconB.visible = false;
    hooks.onEnd(result, st);
  }

  cleanup() {
    const st = this.state; if (!st) return;
    this.scene.remove(st.rival.model); st.rival.model.userData.paint?.dispose();
    this.beaconA.visible = this.beaconB.visible = false;
    this.state = null;
  }

  hud(player) {
    const st = this.state; if (!st) return null;
    const pp = this.progressOf(st.cp, player.x, player.z), rp = this.progressOf(st.rival.cp, st.rival.phys.x, st.rival.phys.z);
    return { name: st.r.name, pos: pp >= rp ? 1 : 2, gap: Math.round(pp - rp), cp: Math.min(st.cp, st.cps.length), total: st.cps.length, t: st.t, stage: st.stage };
  }
  blips(save) {
    const b = [];
    this.pins.forEach((p, i) => { if (p.g.visible) b.push({ x: p.g.position.x, z: p.g.position.z, k: i === save.raceIdx ? 'pin' : 'pinlock' }); });
    const st = this.state;
    if (st) {
      b.push({ x: st.rival.phys.x, z: st.rival.phys.z, k: 'rival' });
      const c = st.cps[Math.min(st.cp, st.cps.length - 1)]; b.push({ x: c[0], z: c[1], k: 'cp' });
    }
    return b;
  }
}
void newInput;
