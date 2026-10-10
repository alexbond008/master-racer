// Arcade-sim car physics. World: +z forward at heading 0, car yaw = rotation.y.
// forward f = (sin th, cos th); right r = (-cos th, sin th). Steer>0 = right = th decreases.
const G = 9.81;

export class CarPhysics {
  constructor(def) {
    this.setDef(def);
    this.x = 0; this.z = 0; this.th = 0;
    this.vx = 0; this.vz = 0;
    this.yawRate = 0;
    this.nitro = 100; this.nitroOn = false;
    this.rpm = 0.15; this.gear = 1;
    this.slip = 0; // 0..1 lateral slip, drives smoke/skid/audio
    this.braking = false;
    this.lastImpact = 0;
    this.steerVis = 0;
  }
  setDef(def) { this.def = def; this.a0 = 1.2 * 26.82 / def.t60; }

  get speed() { return Math.hypot(this.vx, this.vz); }
  get fwdSpeed() { return this.vx * Math.sin(this.th) + this.vz * Math.cos(this.th); }

  place(x, z, th) { this.x = x; this.z = z; this.th = th; this.vx = this.vz = 0; this.yawRate = 0; }

  // grip: surface/weather multiplier (1 dry .. ~0.35 snow)
  step(dt, inp, grip, collide) {
    const d = this.def;
    const sn = Math.sin(this.th), cs = Math.cos(this.th);
    let vf = this.vx * sn + this.vz * cs;
    let vl = this.vx * -cs + this.vz * sn; // right-positive
    const mu = d.grip * grip;

    // ---- nitro
    const wantNitro = inp.nitro && this.nitro > 0 && inp.throttle > 0;
    this.nitroOn = wantNitro;
    if (wantNitro) this.nitro = Math.max(0, this.nitro - (d.nitroDrain || 22) * dt);
    else this.nitro = Math.min(100, this.nitro + (inp.handbrake || this.slip > 0.35 ? 9 : 1.6) * dt);

    // ---- longitudinal
    const vmax = d.vmax * (wantNitro ? 1.22 : 1);
    this.braking = false;
    if (inp.throttle > 0) {
      const taper = Math.max(0, 1 - Math.pow(Math.max(vf, 0) / vmax, 1.7));
      let a = this.a0 * taper * (wantNitro ? 2.1 : 1) * inp.throttle;
      // wheelspin: limited by traction, worse on wet
      a = Math.min(a, mu * G * 0.95 + 0.4);
      if (vf < -0.5) a += 14 * grip; // throttle while reversing = brake first
      vf += a * dt;
    }
    if (inp.brake > 0) {
      if (vf > 0.6) { // braking: decel limited by grip => stopping distance depends on weather
        vf = Math.max(0, vf - mu * G * 0.98 * inp.brake * dt);
        this.braking = true;
      } else { // reverse
        vf -= Math.min(5, d.vmax * 0.12) * 0.9 * inp.brake * dt * (1 + 0.0);
        vf = Math.max(vf, -d.vmax * 0.25);
        this.braking = vf > -0.5;
      }
    }
    // drag + rolling resistance
    const sgn = Math.sign(vf);
    vf -= sgn * Math.min(Math.abs(vf), (0.12 + 0.0016 * vf * vf + (inp.throttle > 0 ? 0 : 0.5)) * dt);

    // ---- yaw (bicycle-ish). Lock reduces with speed; yaw capped by tyre grip -> understeer when pushing.
    const spd = Math.abs(vf);
    const lock = d.steer * (1 / (1 + spd * 0.09)) + 0.06;
    const delta = inp.steer * lock;
    let yawTarget = (spd < 0.3 ? 0 : (vf >= 0 ? 1 : -1) * spd * Math.tan(delta) / d.wb);
    if (inp.handbrake) yawTarget *= 1.45;
    const maxYaw = (mu * G * 1.25) / Math.max(spd, 6);
    yawTarget = Math.max(-maxYaw * (inp.handbrake ? 1.5 : 1), Math.min(maxYaw * (inp.handbrake ? 1.5 : 1), yawTarget));
    this.yawRate += (-yawTarget - this.yawRate) * Math.min(1, 9 * dt);
    this.th += this.yawRate * dt;
    this.steerVis = delta;

    // ---- lateral grip: friction circle. Sliding when lateral demand exceeds mu*g.
    const muRear = inp.handbrake ? mu * 0.32 : mu * (this.nitroOn ? 0.9 : 1);
    const maxLat = muRear * G * dt;
    const visc = Math.min(Math.abs(vl), 2.2 * grip * dt * Math.abs(vl));
    vl -= Math.sign(vl) * Math.min(Math.abs(vl), maxLat + visc);
    this.slip = Math.min(1, Math.abs(vl) / 7 + (inp.handbrake && spd > 8 ? 0.4 : 0));

    // recompose (heading changed, so re-project with new basis; keeps car rotating inside its velocity => drift)
    const sn2 = Math.sin(this.th), cs2 = Math.cos(this.th);
    // lateral/forward are measured in OLD basis then mapped to new => velocity keeps its world direction
    this.vx = vf * sn + vl * -cs;
    this.vz = vf * cs + vl * sn;
    // yaw changed after measuring; the old-basis recompose preserves world velocity, so only friction aligns it.
    void sn2; void cs2;

    this.x += this.vx * dt;
    this.z += this.vz * dt;

    // ---- rpm / gear (for HUD + audio)
    const frac = Math.min(1, Math.max(0, Math.abs(vf) / d.vmax));
    const gears = 6;
    const g = Math.min(gears - 1, Math.floor(frac * gears * 0.98));
    const inGear = frac * gears - g;
    this.gear = vf < -0.5 ? 0 : g + 1;
    const target = 0.18 + 0.62 * inGear + inp.throttle * 0.14 + (wantNitro ? 0.05 : 0);
    this.rpm += (target - this.rpm) * Math.min(1, 12 * dt);

    if (collide) collide(this);
  }

  // push car out of an oriented box {cx,cz,c,s,hx,hz} (local frame = rotateY(theta): c=cos, s=sin). Same response as resolveRect.
  resolveOBB(o, rad) {
    const dx = this.x - o.cx, dz = this.z - o.cz, lx = dx * o.c - dz * o.s, lz = dx * o.s + dz * o.c;
    const qx = Math.max(-o.hx, Math.min(o.hx, lx)), qz = Math.max(-o.hz, Math.min(o.hz, lz));
    let ex = lx - qx, ez = lz - qz, dist = Math.hypot(ex, ez), pen;
    if (dist >= rad) return 0;
    if (dist < 1e-4) { // centre inside the box: eject along the shortest axis
      const px = o.hx - Math.abs(lx), pz = o.hz - Math.abs(lz);
      if (px < pz) { ex = Math.sign(lx) || 1; ez = 0; pen = rad + px; } else { ex = 0; ez = Math.sign(lz) || 1; pen = rad + pz; }
    } else { ex /= dist; ez /= dist; pen = rad - dist; }
    const nx = ex * o.c + ez * o.s, nz = -ex * o.s + ez * o.c; // local -> world normal
    this.x += nx * pen; this.z += nz * pen;
    const vn = this.vx * nx + this.vz * nz;
    if (vn < 0) {
      this.vx -= 1.25 * vn * nx; this.vz -= 1.25 * vn * nz; this.vx *= 0.93; this.vz *= 0.93;
      this.lastImpact = Math.max(this.lastImpact, -vn); this.yawRate *= 0.6; return -vn;
    }
    return 0;
  }

  // push car out of AABB rect. returns impact speed along normal.
  resolveRect(rect, rad) {
    const cx = Math.max(rect.x0, Math.min(this.x, rect.x1));
    const cz = Math.max(rect.z0, Math.min(this.z, rect.z1));
    let dx = this.x - cx, dz = this.z - cz;
    let dist = Math.hypot(dx, dz);
    if (dist >= rad) return 0;
    if (dist < 1e-4) { // centre inside rect: eject along shortest axis
      const l = this.x - rect.x0, r = rect.x1 - this.x, t = this.z - rect.z0, b = rect.z1 - this.z;
      const m = Math.min(l, r, t, b);
      dx = m === l ? -1 : m === r ? 1 : 0; dz = m === t ? -1 : m === b ? 1 : 0; dist = 0;
    } else { dx /= dist; dz /= dist; }
    this.x = cx + dx * rad + (dist === 0 ? dx * 0.01 : 0);
    this.z = cz + dz * rad + (dist === 0 ? dz * 0.01 : 0);
    const vn = this.vx * dx + this.vz * dz;
    if (vn < 0) {
      this.vx -= (1.25) * vn * dx; this.vz -= 1.25 * vn * dz; // restitution .25
      this.vx *= 0.93; this.vz *= 0.93;
      this.lastImpact = Math.max(this.lastImpact, -vn);
      this.yawRate *= 0.6;
      return -vn;
    }
    return 0;
  }
}
