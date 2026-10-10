import * as THREE from 'three';
import { CarPhysics } from './car.js';
import { NPC_CARS, CARS } from './cars.js';
import { buildCar, updateCarModel } from './carModel.js';
import { buildKenneyCar } from './models.js';
import { CELL, N } from './world.js';
import { LaneDriver, randomTurn, steerToward, newInput } from './ai.js';

const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const COLORS = ['#b22222', '#1f3d8a', '#d9d9d9', '#111418', '#e0c341', '#2f6f4f', '#8b8f98', '#6d2f8a', '#c96a1b'];
const KINDS = [['k_sedan', 3], ['k_hatch', 3], ['k_sporty', 1], ['k_suv', 2], ['k_suvlux', 0.6], ['k_van', 1.6], ['k_delivery', 0.8], ['blackcab', 2.2], ['fiat126', 1], ['bus', 1.1]];
export const KENNEY_FILES = ['sedan', 'hatchback-sports', 'sedan-sports', 'suv', 'suv-luxury', 'van', 'delivery'];
const pickKind = () => { const tot = KINDS.reduce((a, k) => a + k[1], 0); let r = Math.random() * tot; for (const [id, w] of KINDS) { if ((r -= w) <= 0) return id; } return 'octavia'; };
const defFor = id => NPC_CARS[id] || CARS[id];

// An AI-driven car: physics + model + lane driver (used for civilians and police patrols).
export class Agent {
  constructor(scene, defId, opts = {}) {
    this.def = defFor(defId);
    this.phys = new CarPhysics(this.def);
    this.model = this.def.kenney ? buildKenneyCar(this.def, { color: opts.color }) : buildCar(this.def, { lite: opts.lite ?? true, color: opts.color, police: this.def.police });
    scene.add(this.model);
    this.drv = new LaneDriver(opts.offset ?? 4.5);
    this.inp = newInput();
    this.cruise = opts.cruise ?? 12;
    this.kind = opts.kind || 'civ';
    this.hp = opts.hp ?? 60;
    this.stuck = 0;
    this.acc = 0;
    this.alive = true;
  }
  placeOnRoad(i, j, d, back = 20) {
    const l = [d[1], -d[0]];
    const x = i * CELL - d[0] * back + l[0] * this.drv.offset, z = j * CELL - d[1] * back + l[1] * this.drv.offset;
    this.phys.place(x, z, Math.atan2(d[0], d[1]));
    this.phys.vx = d[0] * this.cruise * 0.8; this.phys.vz = d[1] * this.cruise * 0.8;
    this.drv.aim(i, j, d); this.inp = newInput(); this.stuck = 0;
  }
  dispose(scene) { scene.remove(this.model); this.model.traverse(o => { if (o.material && o.material !== undefined && o.userData.paint !== o.material) { /* shared mats left alone */ } }); this.model.userData.paint?.dispose(); }
}

export class Traffic {
  constructor(scene, world, count = 38) {
    this.scene = scene; this.world = world; this.cars = [];
    for (let k = 0; k < count; k++) {
      const kind = pickKind();
      const a = new Agent(scene, kind, { color: kind === 'bus' ? undefined : COLORS[(Math.random() * COLORS.length) | 0], cruise: kind === 'bus' ? 9 : 9 + Math.random() * 6, kind: 'civ' });
      this.cars.push(a);
      this.respawn(a, { x: 6 * CELL, z: 9 * CELL }, 40, 380);
    }
  }

  respawn(a, c, minD, maxD) {
    for (let tries = 0; tries < 30; tries++) {
      const i = Math.floor(Math.random() * (N + 1)), j = Math.floor(Math.random() * (N + 1));
      const d = DIRS[(Math.random() * 4) | 0];
      if (i + d[0] < 0 || i + d[0] > N || j + d[1] < 0 || j + d[1] > N) continue;
      const x = i * CELL, z = j * CELL, dist = Math.hypot(x - c.x, z - c.z);
      if (dist < minD || dist > maxD) continue;
      a.placeOnRoad(i, j, d, 25 + Math.random() * 20);
      a.hp = 60; a.alive = true; a.model.visible = true;
      return;
    }
  }

  // aheadCars: other agents to avoid rear-ending
  drive(a, others, player) {
    const p = a.phys, drv = a.drv;
    const [tx, tz] = drv.target(p, randomTurn);
    let speed = a.cruise;
    const sn = Math.sin(p.th), cs = Math.cos(p.th);
    // look-ahead for a car in front (including the player) -> slow down / stop
    const check = (q) => {
      const dx = q.x - p.x, dz = q.z - p.z, fwd = dx * sn + dz * cs, lat = dx * cs - dz * sn;
      if (fwd > 0 && fwd < 16 && Math.abs(lat) < 2.6) speed = Math.min(speed, Math.max(0, (fwd - 6) * 1.1));
    };
    for (const o of others) if (o !== a) check(o.phys);
    check(player);
    steerToward(p, tx, tz, speed, a.inp);
  }

  update(dt, player, grip, world, camPos) {
    const STEP = 1 / 60;
    for (const a of this.cars) {
      a.acc += dt;
      let n = 0;
      while (a.acc >= STEP && n++ < 4) {
        this.drive(a, this.cars, player);
        a.phys.step(STEP, a.inp, grip, world.collide);
        a.acc -= STEP;
      }
      if (a.acc > STEP * 4) a.acc = 0;
      // stuck / far recycling
      if (Math.abs(a.phys.fwdSpeed) < 0.6 && a.inp.throttle > 0.1) a.stuck += dt; else a.stuck = Math.max(0, a.stuck - dt);
      const d = Math.hypot(a.phys.x - player.x, a.phys.z - player.z);
      const behindCam = camPos ? ((a.phys.x - camPos.x) * Math.sin(player.th) + (a.phys.z - camPos.z) * Math.cos(player.th)) < 0 : true;
      if (d > 480 || (a.stuck > 6 && (d > 70))) this.respawn(a, player, 120, 400);
      a.model.position.set(a.phys.x, 0, a.phys.z); a.model.rotation.y = a.phys.th;
      a.model.visible = d < 520;
      if (a.model.visible) updateCarModel(a.model, a.phys, dt);
      void behindCam;
    }
  }
}
