import * as THREE from 'three';
import { CarPhysics } from './car.js';
import { NPC_CARS, CARS } from './cars.js';
import { buildCar, updateCarModel } from './carModel.js';
import { buildKenneyCar } from './models.js';
import { NetDriver, randomExit, steerToward, newInput } from './ai.js';

const COLORS = ['#b22222', '#1f3d8a', '#d9d9d9', '#111418', '#e0c341', '#2f6f4f', '#8b8f98', '#6d2f8a', '#c96a1b'];
const KINDS = [['k_sedan', 3], ['k_hatch', 3], ['k_sporty', 1], ['k_suv', 2], ['k_suvlux', 0.6], ['k_van', 1.6], ['k_delivery', 0.8], ['blackcab', 2.2], ['fiat126', 1], ['bus', 1.1]];
export const KENNEY_FILES = ['sedan', 'hatchback-sports', 'sedan-sports', 'suv', 'suv-luxury', 'van', 'delivery'];
const pickKind = () => { const tot = KINDS.reduce((a, k) => a + k[1], 0); let r = Math.random() * tot; for (const [id, w] of KINDS) { if ((r -= w) <= 0) return id; } return 'k_sedan'; };
const defFor = id => NPC_CARS[id] || CARS[id];
const SPEED_BY_CLASS = [1.4, 1.2, 1.0, 0.8];

// put an agent on a random road within [minD,maxD] of centre c (optionally rejecting spots for which reject(x,z) is true)
export function placeNear(a, net, c, minD, maxD, reject) {
  for (let tries = 0; tries < 40; tries++) {
    const ang = Math.random() * Math.PI * 2, d = minD + Math.random() * (maxD - minD);
    const nr = net.nearest(c.x + Math.cos(ang) * d, c.z + Math.sin(ang) * d, 70);
    if (!nr || nr.e.len < 12) continue;
    const dist = Math.hypot(nr.px - c.x, nr.pz - c.z); if (dist < minD || dist > maxD) continue;
    if (reject && reject(nr.px, nr.pz)) continue;
    a.placeOn(nr.e, nr.e.oneway || Math.random() < 0.5 ? 1 : -1, nr.s, nr);
    return true;
  }
  return false;
}

// An AI-driven car: physics + model + road driver (civilians, patrols, pursuit units, race rivals).
export class Agent {
  constructor(scene, net, defId, opts = {}) {
    this.net = net; this.def = defFor(defId);
    this.phys = new CarPhysics(this.def);
    this.model = this.def.kenney ? buildKenneyCar(this.def, { color: opts.color }) : buildCar(this.def, { lite: opts.lite ?? true, color: opts.color, police: this.def.police });
    scene.add(this.model);
    this.drv = new NetDriver(net, opts.laneMul ?? 1);
    this.inp = newInput();
    this.cruise = opts.cruise ?? 12;
    this.kind = opts.kind || 'civ';
    this.hp = opts.hp ?? 60;
    this.stuck = 0; this.acc = 0; this.alive = true;
  }
  // place on edge e travelling `dir`, at arc length s measured along the edge's forward direction
  placeOn(e, dir, sFwd) {
    const s = dir === 1 ? sFwd : e.len - sFwd, p = this.net.lanePoint(e, dir, Math.max(0, Math.min(e.len, s)), this.drv.off(e));
    this.phys.place(p.x, p.z, Math.atan2(p.tx, p.tz));
    this.phys.vx = p.tx * this.cruise * 0.8; this.phys.vz = p.tz * this.cruise * 0.8;
    this.drv.aim(e, dir, s); this.inp = newInput(); this.stuck = 0;
  }
  dispose(scene) { scene.remove(this.model); this.model.userData.paint?.dispose(); }
}

export class Traffic {
  constructor(scene, world, count = 55) {
    this.scene = scene; this.world = world; this.net = world.net; this.cars = [];
    for (let k = 0; k < count; k++) {
      const kind = pickKind();
      const a = new Agent(scene, this.net, kind, { color: kind === 'bus' ? undefined : COLORS[(Math.random() * COLORS.length) | 0], cruise: kind === 'bus' ? 9 : 9 + Math.random() * 6, kind: 'civ' });
      this.cars.push(a); this.respawn(a, world.spawn, 40, 420);
    }
  }
  respawn(a, c, minD, maxD) { if (placeNear(a, this.net, c, minD, maxD)) { a.hp = 60; a.alive = true; a.model.visible = true; } }

  drive(a, others, player) {
    const p = a.phys, drv = a.drv;
    const [tx, tz, corner] = drv.target(p, randomExit, 12 + p.speed * 0.5);
    let speed = a.cruise * SPEED_BY_CLASS[drv.e.cls];
    const sn = Math.sin(p.th), cs = Math.cos(p.th);
    const check = q => { const dx = q.x - p.x, dz = q.z - p.z, fwd = dx * sn + dz * cs, lat = dx * cs - dz * sn; if (fwd > 0 && fwd < 16 && Math.abs(lat) < 2.6) speed = Math.min(speed, Math.max(0, (fwd - 6) * 1.1)); };
    for (const o of others) if (o !== a) check(o.phys);
    check(player);
    steerToward(p, tx, tz, speed, a.inp, 1, corner);
  }

  update(dt, player, grip, world) {
    const STEP = 1 / 60;
    for (const a of this.cars) {
      a.acc += dt; let n = 0;
      while (a.acc >= STEP && n++ < 4) { this.drive(a, this.cars, player); a.phys.step(STEP, a.inp, grip, world.collide); a.acc -= STEP; }
      if (a.acc > STEP * 4) a.acc = 0;
      if (Math.abs(a.phys.fwdSpeed) < 0.6 && a.inp.throttle > 0.1) a.stuck += dt; else a.stuck = Math.max(0, a.stuck - dt);
      const d = Math.hypot(a.phys.x - player.x, a.phys.z - player.z);
      if (d > 520 || (a.stuck > 6 && d > 70)) this.respawn(a, player, 120, 420);
      a.model.position.set(a.phys.x, 0, a.phys.z); a.model.rotation.y = a.phys.th;
      a.model.visible = d < 560;
      if (a.model.visible) updateCarModel(a.model, a.phys, dt);
    }
  }
}
