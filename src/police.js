import * as THREE from 'three';
import { Agent, placeNear } from './traffic.js';
import { steerToward, newInput, randomExit } from './ai.js';
import { buildCar, updateCarModel } from './carModel.js';
import { NPC_CARS } from './cars.js';

// GTA-style wanted system. Heat accumulates from offences; stars = thresholds crossed.
export const HEAT_AT = [0, 8, 25, 55, 95, 150];
const UNITS = [0, 2, 3, 4, 6, 8];
const MIX = { 1: ['cruiser'], 2: ['cruiser'], 3: ['cruiser', 'interceptor'], 4: ['interceptor', 'suv', 'cruiser'], 5: ['interceptor', 'suv', 'interceptor', 'suv'] };
const HP = { cruiser: 90, interceptor: 120, suv: 260 };
const MPH = 2.23694;

export class PoliceSystem {
  constructor(scene, world) {
    this.scene = scene; this.world = world; this.net = world.net;
    this.units = []; this.roadblocks = [];
    this.heat = 0; this.stars = 0;
    this.seen = false; this.unseenT = 0; this.bustedT = 0;
    this.spawnT = 0; this.blockT = 10; this.timeSinceStars = 99;
    this.onEvent = null;
    this.wrecked = 0;

    // pooled flashing lights (real lights on the 2 nearest pursuers)
    this.lights = [0, 1].map(() => { const l = new THREE.PointLight(0xff2020, 0, 28, 1.6); scene.add(l); return l; });

    // helicopter
    const g = new THREE.Group();
    const bodyM = new THREE.MeshStandardMaterial({ color: 0x15171c, roughness: 0.5, metalness: 0.5 });
    const body = new THREE.Mesh(new THREE.SphereGeometry(1.5, 12, 8), bodyM); body.scale.set(1, 0.85, 1.7); g.add(body);
    const tail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.3, 5), bodyM); tail.position.z = -3.6; g.add(tail);
    this.rotor = new THREE.Mesh(new THREE.BoxGeometry(9, 0.05, 0.25), bodyM); this.rotor.position.y = 1.5; g.add(this.rotor);
    const strobe = new THREE.Mesh(new THREE.SphereGeometry(0.15), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 0.2, 0.2) })); strobe.position.set(0, 1.1, -5.9); g.add(strobe);
    this.heliStrobe = strobe;
    this.heliSpot = new THREE.SpotLight(0xe8f0ff, 0, 160, 0.16, 0.5, 1.2); g.add(this.heliSpot); g.add(this.heliSpot.target);
    this.cone = new THREE.Mesh(new THREE.ConeGeometry(7, 45, 20, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.55, 0.65, 0.9), transparent: true, opacity: 0.1, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    this.cone.geometry.translate(0, -22.5, 0); g.add(this.cone);
    g.visible = false; scene.add(g);
    this.heli = { g, x: 0, z: 0, y: 42, active: false };
  }

  // ---------- setup
  seedPatrols(player, n = 6) {
    for (let k = 0; k < n; k++) { const u = this.makeUnit('cruiser', 'patrol'); this.units.push(u); this.respawnPatrol(u, player, 90, 420); }
  }
  makeUnit(type, role) {
    const base = NPC_CARS[type];
    const u = new Agent(this.scene, this.net, type, { laneMul: role === 'patrol' ? 1 : 0, cruise: role === 'patrol' ? 11 : 60, kind: 'cop', hp: HP[type] });
    u.def = { ...base, t60: base.t60 * 0.7 }; u.phys.setDef(u.def); u.type = type; u.role = role; u.mode = 'lane'; u.reverseT = 0; u.disabledT = 0; u.hpMax = HP[type];
    return u;
  }
  respawnPatrol(u, c, minD, maxD) {
    u.drv.laneMul = 1; u.cruise = 11;
    if (placeNear(u, this.net, c, minD, maxD)) { u.hp = u.hpMax; u.role = 'patrol'; u.mode = 'lane'; }
  }

  // ---------- heat
  witnessed(player) { return this.seen || this.units.some(u => u.role !== 'disabled' && Math.hypot(u.phys.x - player.x, u.phys.z - player.z) < 110); }
  addHeat(n, reason, player) {
    const before = this.stars;
    this.heat += n;
    let s = 0; for (let k = 1; k <= 5; k++) if (this.heat >= HEAT_AT[k]) s = k;
    if (s > before) {
      this.stars = s; this.unseenT = 0; this.spawnT = 0;
      this.onEvent?.('wanted', { stars: s, reason, first: before === 0 });
      for (const u of this.units) if (u.role === 'patrol' && Math.hypot(u.phys.x - player.x, u.phys.z - player.z) < 320) this.toPursuit(u);
    }
  }
  // offence reported by the game (collisions etc.)
  offence(kind, player) {
    const table = { civHit: 5, copHit: 9, copWreck: 25, roadblock: 12 };
    const w = this.witnessed(player);
    this.addHeat((table[kind] || 3) * (w ? 1 : 0.25), kind, player);
  }
  toPursuit(u) { u.role = 'pursuit'; u.drv.laneMul = 0; u.mode = 'direct'; u.cruise = 60; }
  toPatrol(u) { u.role = 'patrol'; u.drv.laneMul = 1; u.cruise = 11; u.mode = 'lane'; u.drv.resync(u.phys); }

  damage(u, amount, player, byPlayer = false) {
    if (u.role === 'disabled') return;
    u.hp -= amount;
    if (u.hp <= 0) { u.role = 'disabled'; u.disabledT = 0; this.wrecked++; this.onEvent?.('wreck', { type: u.type }); if (byPlayer) this.offence('copWreck', player); }
  }

  // ---------- spawning
  spawnPursuit(player) {
    const mix = MIX[this.stars]; const pur = this.units.filter(u => u.role === 'pursuit').length;
    const type = mix[pur % mix.length];
    const u = this.makeUnit(type, 'pursuit');
    // prefer a spot out of the player's sight, 110-240 m away
    if (placeNear(u, this.net, player, 90, 190, (x, z) => this.world.lineClear(x, z, player.x, player.z)) || placeNear(u, this.net, player, 90, 220)) {
      u.mode = 'lane'; u.drv.resync(u.phys); this.units.push(u);
    } else this.scene.remove(u.model);
  }

  spawnRoadblock(player) {
    const sp = player.speed > 8 ? [player.vx, player.vz] : [Math.sin(player.th), Math.cos(player.th)], l = Math.hypot(sp[0], sp[1]) || 1;
    const nr = this.net.nearest(player.x + sp[0] / l * 240, player.z + sp[1] / l * 240, 140, e => e.cls <= 2 && e.len > 40);
    if (!nr) return;
    const e = nr.e, p = this.net.pointAt(e, 1, Math.max(8, Math.min(e.len - 8, nr.s))), th = Math.atan2(p.tx, p.tz) + Math.PI / 2; // cars parked ACROSS the road
    const n = Math.max(2, Math.ceil(e.width / 4.2)), spacing = e.width / n + 0.2, count = this.stars >= 4 ? n : n - 1;
    const rb = { x: p.x, z: p.z, age: 0, cars: [] };
    for (let i = 0; i < count; i++) {
      const o = (i - (n - 1) / 2) * spacing, cx = p.x + p.tz * o, cz = p.z - p.tx * o;
      const m = buildCar(NPC_CARS.cruiser, { lite: true, police: true });
      m.position.set(cx, 0, cz); m.rotation.y = th; this.scene.add(m);
      const obb = { cx, cz, c: Math.cos(th), s: Math.sin(th), hx: 1.0, hz: 2.4 };
      this.world.dynamicObbs.push(obb);
      rb.cars.push({ m, obb });
    }
    this.roadblocks.push(rb);
  }
  clearRoadblock(rb) {
    for (const c of rb.cars) { this.scene.remove(c.m); const i = this.world.dynamicObbs.indexOf(c.obb); if (i >= 0) this.world.dynamicObbs.splice(i, 1); }
  }

  removeUnit(u) { this.scene.remove(u.model); u.model.userData.paint?.dispose(); const i = this.units.indexOf(u); if (i >= 0) this.units.splice(i, 1); }

  // ---------- helpers
  sees(u, player, vis) {
    const range = (u.role === 'patrol' ? 85 : 130) * vis;
    const d = Math.hypot(u.phys.x - player.x, u.phys.z - player.z);
    return d < range && this.world.lineClear(u.phys.x, u.phys.z, player.x, player.z);
  }

  // follow the A* route toward the player at every junction
  chooseToward(player) {
    const net = this.net, pn = net.nearestNode(player.x, player.z);
    return (opts, node) => {
      if (Math.random() < 0.04) return opts[(Math.random() * opts.length) | 0];
      const r = net.route(node.id, pn);
      if (r && r.length) { const m = opts.find(o => o.e === r[0].e && o.dir === r[0].dir); if (m) return m; }
      return opts[(Math.random() * opts.length) | 0];
    };
  }

  // ---------- per-frame
  update(dt, player, ctx) {
    const { grip, vis, onUnit } = ctx, world = this.world;
    const STEP = 1 / 60, mph = player.speed * MPH, pv = ctx.playerVmax;
    this.timeSinceStars = this.stars ? 0 : this.timeSinceStars + dt;

    // --- units
    const choose = this.chooseToward(player);
    for (const u of [...this.units]) {
      const p = u.phys, d = Math.hypot(p.x - player.x, p.z - player.z);
      // rubber-band top speed to the player's car so early cars can still be chased + survive
      if (u.role !== 'disabled') {
        const base = NPC_CARS[u.type];
        u.def.vmax = u.type === 'interceptor' ? Math.min(base.vmax, pv * 1.15 + 16) : u.type === 'suv' ? Math.min(base.vmax, pv * 1.05 + 14) : Math.min(base.vmax, pv * 1.0 + 14);
      }
      u.acc += dt; let n = 0;
      while (u.acc >= STEP && n++ < 4) {
        if (u.role === 'pursuit') this.pursuit(u, player, STEP, choose);
        else if (u.role === 'patrol') this.patrol(u);
        else { u.inp.throttle = 0; u.inp.brake = 1; u.inp.steer = 0; }
        p.step(STEP, u.inp, grip, world.collide);
        u.acc -= STEP;
      }
      if (u.acc > STEP * 4) u.acc = 0;
      u.model.position.set(p.x, 0, p.z); u.model.rotation.y = p.th;
      updateCarModel(u.model, p, dt);
      if (u.role === 'disabled') { u.disabledT += dt; if (u.model.userData.bars) { u.model.userData.bars.red.visible = u.model.userData.bars.blue.visible = false; } if (u.disabledT > 25) { this.removeUnit(u); continue; } }
      if (u.role === 'patrol' && d > 520) this.respawnPatrol(u, player, 150, 420);
      u.model.visible = d < 560;
    }

    // --- detection
    let seenNow = false, patrolSees = null;
    for (const u of this.units) {
      if (u.role === 'disabled') continue;
      if (this.sees(u, player, vis)) { seenNow = true; if (u.role === 'patrol' && !patrolSees) patrolSees = u; }
    }
    const h = this.heli;
    if (h.active && Math.hypot(h.x - player.x, h.z - player.z) < 190 * vis) seenNow = true;
    this.seen = seenNow;

    if (this.stars === 0) {
      if (patrolSees && mph > 78 && Math.hypot(patrolSees.phys.x - player.x, patrolSees.phys.z - player.z) < 85) this.addHeat(8, 'speeding', player);
    } else if (seenNow && mph > 90) {
      this.heat = Math.min(HEAT_AT[5] + 30, this.heat + 0.5 * dt);
    }

    // --- pursuit population
    if (this.stars > 0) {
      this.spawnT -= dt;
      const pur = this.units.filter(u => u.role === 'pursuit').length;
      if (pur < UNITS[this.stars] && this.spawnT <= 0) { this.spawnPursuit(player); this.spawnT = 2.2; }
      // far pursuers: pull them back toward the action
      for (const u of this.units) if (u.role === 'pursuit' && Math.hypot(u.phys.x - player.x, u.phys.z - player.z) > 520) { this.removeUnit(u); }
    }

    // --- evade
    if (this.stars > 0) {
      const nearest = this.units.reduce((m, u) => u.role === 'pursuit' ? Math.min(m, Math.hypot(u.phys.x - player.x, u.phys.z - player.z)) : m, Infinity);
      // cops always home in on your last known spot: only counts as "lost" if no one is close either
      if (seenNow || nearest < 90) this.unseenT = Math.max(0, this.unseenT - dt * 2);
      else this.unseenT += dt;
      const need = this.evadeTime;
      if (this.unseenT >= need) this.escape();
    }
    // --- busted
    const close = this.units.find(u => u.role === 'pursuit' && Math.hypot(u.phys.x - player.x, u.phys.z - player.z) < 11);
    if (this.stars > 0 && close && player.speed < 5) this.bustedT += dt; else this.bustedT = Math.max(0, this.bustedT - dt * 0.6);
    if (this.bustedT >= 2.2) { this.bustedT = 0; this.clearAll(); this.onEvent?.('busted', {}); }

    // --- roadblocks
    for (const rb of [...this.roadblocks]) {
      rb.age += dt;
      const d = Math.hypot(rb.x - player.x, rb.z - player.z);
      if (this.stars < 3 || d > 450 || rb.age > 50) { this.clearRoadblock(rb); this.roadblocks.splice(this.roadblocks.indexOf(rb), 1); }
    }
    if (this.stars >= 3) {
      this.blockT -= dt;
      if (this.blockT <= 0 && this.roadblocks.length < (this.stars >= 5 ? 2 : 1)) { this.spawnRoadblock(player); this.blockT = 16; }
    }

    // --- heli
    h.active = this.stars >= 5;
    h.g.visible = h.active;
    if (h.active) {
      const tx = player.x + player.vx * 1.4, tz = player.z + player.vz * 1.4;
      h.x += (tx - h.x) * Math.min(1, dt * 1.2); h.z += (tz - h.z) * Math.min(1, dt * 1.2);
      h.g.position.set(h.x, h.y + Math.sin(performance.now() * 0.001) * 1.5, h.z);
      h.g.rotation.y = Math.atan2(player.x - h.x, player.z - h.z);
      this.rotor.rotation.y += dt * 40;
      this.heliSpot.position.set(0, -0.5, 1.5); this.heliSpot.target.position.set(player.x - h.g.position.x, -h.g.position.y, player.z - h.g.position.z);
      // rotate target into parent space (group is yawed)
      const c = Math.cos(-h.g.rotation.y), s = Math.sin(-h.g.rotation.y), tx2 = this.heliSpot.target.position.x, tz2 = this.heliSpot.target.position.z;
      this.heliSpot.target.position.x = tx2 * c + tz2 * s; this.heliSpot.target.position.z = -tx2 * s + tz2 * c;
      this.heliSpot.intensity = 260;
      this.heliStrobe.visible = Math.floor(performance.now() / 350) % 2 === 0;
      this.cone.lookAt(player.x, 0, player.z);
      this.cone.rotation.set(0, 0, 0); this.cone.rotateX(0);
      this.cone.visible = false; // spot light is enough; cone kept for later tuning
    }

    // --- flashing lights on 2 nearest pursuers
    const t = performance.now() * 0.001, near = this.units.filter(u => u.role === 'pursuit').sort((a, b) => Math.hypot(a.phys.x - player.x, a.phys.z - player.z) - Math.hypot(b.phys.x - player.x, b.phys.z - player.z));
    this.lights.forEach((l, i) => {
      const u = near[i]; if (!u) { l.intensity = 0; return; }
      const on = Math.floor(t * 7) % 2 === 0;
      l.color.set(on ? 0xff1010 : 0x2040ff); l.intensity = 70; l.position.set(u.phys.x, 3, u.phys.z);
    });
    void onUnit;
  }

  get evadeTime() { return 14 + this.stars * 4; }
  get evadeProgress() { return this.stars ? Math.min(1, this.unseenT / this.evadeTime) : 0; }

  patrol(u) {
    const [tx, tz, corner] = u.drv.target(u.phys, randomExit, 12 + u.phys.speed * 0.5);
    steerToward(u.phys, tx, tz, u.cruise * [1.2, 1, 0.85, 0.65][u.drv.e.cls], u.inp, 1, corner);
  }

  pursuit(u, player, step, choose) {
    const p = u.phys, d = Math.hypot(p.x - player.x, p.z - player.z);
    const los = this.world.lineClear(p.x, p.z, player.x, player.z);
    // reverse maneuver when wedged
    if (u.reverseT > 0) {
      u.reverseT -= step; u.inp.throttle = 0; u.inp.brake = 1; u.inp.steer = -Math.sign(u.inp.steer || 1) * 0.9; u.inp.handbrake = false;
      if (u.reverseT <= 0) { u.mode = 'lane'; u.drv.resync(p); u.stuck = 0; }
      return;
    }
    let tx, tz, corner = 0, vmax = u.def.vmax;
    if (los && d < 170) {
      u.mode = 'direct';
      const lead = Math.min(1, d / 60) * 0.7;
      tx = player.x + player.vx * lead; tz = player.z + player.vz * lead;
      if (player.speed < 7 && d < 90) vmax = Math.max(5, Math.min(vmax, (d - 10) * 0.7 + 5));
    } else {
      if (u.mode !== 'lane') { u.drv.resync(p); u.mode = 'lane'; }
      const t = u.drv.target(p, choose, 16 + p.speed * 0.5); tx = t[0]; tz = t[1]; corner = t[2] * 0.6;
      vmax *= 1.05;
    }
    steerToward(p, tx, tz, vmax, u.inp, 1.6, corner);
    if (Math.abs(p.fwdSpeed) < 1.2 && u.inp.throttle > 0.1) { u.stuck = (u.stuck || 0) + step; if (u.stuck > 1.4) { u.reverseT = 1.1; u.stuck = 0; } } else u.stuck = Math.max(0, (u.stuck || 0) - step);
  }

  escape() {
    this.stars = 0; this.heat = 0; this.unseenT = 0; this.bustedT = 0;
    for (const u of this.units) if (u.role === 'pursuit') this.toPatrol(u);
    this.onEvent?.('escaped', {});
  }
  clearAll() {
    this.stars = 0; this.heat = 0; this.unseenT = 0;
    for (const u of [...this.units]) { if (u.role === 'pursuit') this.removeUnit(u); }
    for (const rb of this.roadblocks) this.clearRoadblock(rb); this.roadblocks.length = 0;
  }

  blips() {
    const b = this.units.map(u => ({ x: u.phys.x, z: u.phys.z, k: u.role }));
    for (const rb of this.roadblocks) b.push({ x: rb.x, z: rb.z, k: 'block' });
    if (this.heli.active) b.push({ x: this.heli.x, z: this.heli.z, k: 'heli' });
    return b;
  }
}
