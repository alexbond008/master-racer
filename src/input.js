// Keyboard + gamepad. Outputs a single normalised state object.
export class Input {
  constructor() {
    this.keys = new Set();
    this.pressed = new Set(); // edge-triggered, cleared each frame
    this.s = { throttle: 0, brake: 0, steer: 0, handbrake: false, nitro: false };
    this._steer = 0;
    addEventListener('keydown', e => {
      if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.code)) e.preventDefault();
      if (!e.repeat) this.pressed.add(e.code);
      this.keys.add(e.code);
    });
    addEventListener('keyup', e => this.keys.delete(e.code));
    addEventListener('blur', () => this.keys.clear());
  }
  was(code) { return this.pressed.has(code); }
  down(code) { return this.keys.has(code); }

  update(dt) {
    const k = this.keys, s = this.s;
    let steerTarget = (k.has('KeyA') || k.has('ArrowLeft') ? -1 : 0) + (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0);
    let throttle = k.has('KeyW') || k.has('ArrowUp') ? 1 : 0;
    let brake = k.has('KeyS') || k.has('ArrowDown') ? 1 : 0;
    let handbrake = k.has('Space');
    let nitro = k.has('ShiftLeft') || k.has('ShiftRight');

    const gp = (navigator.getGamepads ? [...navigator.getGamepads()] : []).find(g => g && g.connected);
    if (gp) {
      const dz = v => (Math.abs(v) < 0.12 ? 0 : v);
      const ax = dz(gp.axes[0] || 0);
      if (ax) { steerTarget = ax; this._steer = ax; } // analog: no smoothing
      throttle = Math.max(throttle, gp.buttons[7]?.value || 0);
      brake = Math.max(brake, gp.buttons[6]?.value || 0);
      handbrake = handbrake || !!gp.buttons[0]?.pressed;
      nitro = nitro || !!gp.buttons[5]?.pressed || !!gp.buttons[1]?.pressed;
      if (gp.buttons[3]?.pressed && !this._gpY) this.pressed.add('KeyC');
      this._gpY = !!gp.buttons[3]?.pressed;
      if (gp.buttons[2]?.pressed && !this._gpX) this.pressed.add('Enter');
      this._gpX = !!gp.buttons[2]?.pressed;
      if (gp.buttons[9]?.pressed && !this._gpS) this.pressed.add('KeyM');
      this._gpS = !!gp.buttons[9]?.pressed;
    }

    if (!gp || !dz0(gp.axes[0])) {
      // keyboard: ramp steering so it feels analog
      const rate = steerTarget === 0 ? 7 : 4.5;
      this._steer += Math.sign(steerTarget - this._steer) * Math.min(Math.abs(steerTarget - this._steer), rate * dt);
    }
    s.steer = this._steer; s.throttle = throttle; s.brake = brake; s.handbrake = handbrake; s.nitro = nitro;
  }

  endFrame() { this.pressed.clear(); }
}
const dz0 = v => Math.abs(v || 0) >= 0.12;
