import { Music, STATIONS } from './music.js';

// All sound is synthesised live with Web Audio. Created on the first user gesture (browser autoplay rules).
// Per-car engine profile: base/max = firing fundamental (Hz) at idle/redline; turbo = whistle; burble = flat-4 style lumpiness.
const CAR_SND = {
  fiat126: { base: 46, max: 150, cut: 1700, grit: 0.5, turbo: 0, lump: 0.55, sub: 0.15 },
  corsa: { base: 38, max: 175, cut: 2000, grit: 0.4, turbo: 0, lump: 0.1, sub: 0.25 },
  impreza: { base: 32, max: 195, cut: 2300, grit: 0.55, turbo: 0.8, lump: 0.45, sub: 0.35 },
  gtr: { base: 29, max: 205, cut: 2600, grit: 0.5, turbo: 1, lump: 0.05, sub: 0.4 },
  f40: { base: 26, max: 235, cut: 3000, grit: 0.8, turbo: 1, lump: 0.0, sub: 0.35, harsh: 1 },
  lambo: { base: 25, max: 310, cut: 4200, grit: 0.6, turbo: 0, lump: 0.0, sub: 0.3, scream: 1 },
};

export class GameAudio {
  constructor() { this.ctx = null; this.ready = false; this.vol = 0.8; this.carId = null; this.boost = 0; this.lastGear = 1; this.radioInfo = null; this.lastPop = 0; }

  start() {
    if (this.ctx) { this.ctx.resume?.(); return; }
    const C = window.AudioContext || window.webkitAudioContext; if (!C) return;
    const ctx = this.ctx = new C({ latencyHint: 'interactive' });
    this.master = ctx.createGain(); this.master.gain.value = this.vol;
    this.comp = ctx.createDynamicsCompressor(); this.comp.threshold.value = -14; this.comp.knee.value = 12; this.comp.ratio.value = 5; this.comp.attack.value = 0.004; this.comp.release.value = 0.2;
    this.analyser = ctx.createAnalyser(); this.analyser.fftSize = 512;
    this.master.connect(this.comp); this.comp.connect(this.analyser); this.comp.connect(ctx.destination);
    this.sfx = ctx.createGain(); this.sfx.gain.value = 0.9; this.sfx.connect(this.master);
    this.musicBus = ctx.createGain(); this.musicBus.gain.value = 0.6; this.musicBus.connect(this.master);
    // shared noise
    const len = ctx.sampleRate * 2, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0); let b0 = 0;
    for (let i = 0; i < len; i++) { const w = Math.random() * 2 - 1; b0 = 0.97 * b0 + 0.03 * w; d[i] = w * 0.7 + b0 * 6; }
    this.noise = buf;
    this.buildEngine(); this.buildLoops();
    this.music = new Music(ctx, this.musicBus, this.noise); this.music.onTrack = i => { this.radioInfo = i; this.onRadio?.(i); };
    this.music.start(); this.music.setStation(0, false);
    this.ready = true; ctx.resume?.();
  }

  // ---------------- helpers
  loopNoise(type, f, q) { const s = this.ctx.createBufferSource(); s.buffer = this.noise; s.loop = true; const fl = this.ctx.createBiquadFilter(); fl.type = type; fl.frequency.value = f; fl.Q.value = q; const g = this.ctx.createGain(); g.gain.value = 0; s.connect(fl); fl.connect(g); g.connect(this.sfx); s.start(0, Math.random()); return { s, f: fl, g }; }
  burst(type, f, q, v, dur, dest = this.sfx, delay = 0) { const t = this.ctx.currentTime + delay, s = this.ctx.createBufferSource(); s.buffer = this.noise; const fl = this.ctx.createBiquadFilter(); fl.type = type; fl.frequency.value = f; fl.Q.value = q; const g = this.ctx.createGain(); g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur); s.connect(fl); fl.connect(g); g.connect(dest); s.start(t, Math.random() * 0.8); s.stop(t + dur + 0.05); }
  tone(f, dur, type = 'sine', v = 0.2, slide = 0, delay = 0) { const t = this.ctx.currentTime + delay, o = this.ctx.createOscillator(), g = this.ctx.createGain(); o.type = type; o.frequency.setValueAtTime(f, t); if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(20, f * slide), t + dur); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(v, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + dur); o.connect(g); g.connect(this.sfx); o.start(t); o.stop(t + dur + 0.05); }
  curve(k) { const c = new Float32Array(256); for (let i = 0; i < 256; i++) { const x = i / 128 - 1; c[i] = Math.tanh(x * k); } return c; }

  // ---------------- persistent voices
  buildEngine() {
    const ctx = this.ctx, e = this.eng = {};
    e.out = ctx.createGain(); e.out.gain.value = 0;
    e.lp = ctx.createBiquadFilter(); e.lp.type = 'lowpass'; e.lp.Q.value = 2.2; e.lp.frequency.value = 800;
    e.ws = ctx.createWaveShaper(); e.ws.curve = this.curve(2.5); e.ws.oversample = '2x';
    e.mod = ctx.createGain(); e.mod.gain.value = 1;            // lumpiness (cylinder pulses)
    e.ws.connect(e.lp); e.lp.connect(e.mod); e.mod.connect(e.out); e.out.connect(this.sfx);
    e.o = [['sawtooth', 1, 0.5], ['square', 0.5, 0.3], ['sawtooth', 2.005, 0.18], ['triangle', 3, 0.1]].map(([type, mult, gain]) => {
      const o = ctx.createOscillator(); o.type = type; o.frequency.value = 40; const g = ctx.createGain(); g.gain.value = gain; o.connect(g); g.connect(e.ws); o.start(); return { o, g, mult, gain };
    });
    e.lfo = ctx.createOscillator(); e.lfo.type = 'sine'; e.lfo.frequency.value = 10; e.lfoG = ctx.createGain(); e.lfoG.gain.value = 0; e.lfo.connect(e.lfoG); e.lfoG.connect(e.mod.gain); e.lfo.start();
    // turbo whistle + intake noise
    e.tw = ctx.createOscillator(); e.tw.type = 'sine'; e.tw.frequency.value = 2000; e.twG = ctx.createGain(); e.twG.gain.value = 0; e.tw.connect(e.twG); e.twG.connect(this.sfx); e.tw.start();
    e.intake = this.loopNoise('bandpass', 900, 0.8);
  }
  buildLoops() {
    this.wind = this.loopNoise('lowpass', 500, 0.4); this.rain = this.loopNoise('highpass', 2500, 0.5); this.rain2 = this.loopNoise('lowpass', 900, 0.3);
    this.squeal = this.loopNoise('bandpass', 1700, 6); this.nitroN = this.loopNoise('highpass', 3200, 0.7); this.heli = this.loopNoise('bandpass', 160, 1.2);
    this.heliLfo = this.ctx.createOscillator(); this.heliLfo.type = 'square'; this.heliLfo.frequency.value = 11; this.heliLfoG = this.ctx.createGain(); this.heliLfoG.gain.value = 0; this.heliLfo.connect(this.heliLfoG); this.heliLfoG.connect(this.heli.g.gain); this.heliLfo.start();
    // sirens (3 positional voices)
    this.sirens = [0, 1, 2].map(() => { const o = this.ctx.createOscillator(); o.type = 'square'; o.frequency.value = 600; const f = this.ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 2200; const g = this.ctx.createGain(); g.gain.value = 0; const p = this.ctx.createStereoPanner(); o.connect(f); f.connect(g); g.connect(p); p.connect(this.sfx); o.start(); return { o, g, p }; });
  }

  setVolume(v) { this.vol = Math.max(0, Math.min(1, v)); if (this.ready) this.master.gain.setTargetAtTime(this.vol, this.ctx.currentTime, 0.05); }
  level() { if (!this.ready) return 0; const a = new Uint8Array(this.analyser.fftSize); this.analyser.getByteTimeDomainData(a); let s = 0; for (const v of a) s += (v - 128) * (v - 128); return Math.sqrt(s / a.length) / 128; }

  // ---------------- per-frame
  // s: { rpm, throttle, speed, slip, braking, nitro, gear, carId, rain, snow, paused, stars, units:[{x,z,role}], heli:{active,x,z}, cam:{x,z,th} }
  update(dt, s) {
    if (!this.ready) return;
    const ctx = this.ctx, t = ctx.currentTime, e = this.eng, prof = CAR_SND[s.carId] || CAR_SND.corsa, tc = 0.05;
    const quiet = s.paused ? 0.25 : 1;
    // --- engine
    const f = prof.base + (prof.max - prof.base) * Math.max(0, Math.min(1, (s.rpm - 0.12) / 0.88));
    e.o.forEach(({ o, mult }) => o.frequency.setTargetAtTime(f * mult, t, 0.03));
    const load = 0.35 + 0.65 * s.throttle;
    e.o[1].g.gain.setTargetAtTime(e.o[1].gain * (0.5 + prof.sub * 2), t, tc);
    e.o[2].g.gain.setTargetAtTime(e.o[2].gain * (0.4 + load) * (prof.harsh ? 1.6 : 1) * (prof.scream ? 2 : 1), t, tc);
    e.o[3].g.gain.setTargetAtTime(e.o[3].gain * (prof.scream ? 3 : 1) * s.rpm * 1.5, t, tc);
    e.lp.frequency.setTargetAtTime(prof.cut * (0.35 + 0.65 * s.rpm) * (0.55 + 0.6 * load), t, tc);
    e.out.gain.setTargetAtTime((0.09 + 0.16 * load + 0.05 * s.rpm) * quiet * (s.nitro ? 1.25 : 1), t, tc);
    e.lfoG.gain.setTargetAtTime(prof.lump * (0.5 - 0.35 * s.rpm) * (1 - s.throttle * 0.3), t, 0.1); e.lfo.frequency.setTargetAtTime(Math.max(6, f / 2.2), t, 0.1);
    // turbo: spool follows throttle*rpm, whistles; blow-off valve when lifting at boost
    const target = prof.turbo * s.throttle * Math.min(1, s.rpm * 1.3);
    const prevBoost = this.boost; this.boost += (target - this.boost) * Math.min(1, dt * (target > this.boost ? 2.2 : 5));
    e.tw.frequency.setTargetAtTime(1500 + this.boost * 3800, t, 0.05); e.twG.gain.setTargetAtTime(this.boost * 0.035 * quiet, t, 0.05);
    if (prof.turbo && prevBoost > 0.55 && target < 0.2 && t - this.lastPop > 0.5) { this.burst('highpass', 3500, 0.8, 0.14, 0.35); this.lastPop = t; }
    e.intake.f.frequency.setTargetAtTime(500 + s.rpm * 1800, t, tc); e.intake.g.gain.setTargetAtTime(0.02 + 0.07 * s.throttle * s.rpm, t, tc);
    // gear change: brief cut + exhaust pop on lift
    if (s.gear !== this.lastGear && s.gear > 0) { e.out.gain.setTargetAtTime(0.02, t, 0.01); e.out.gain.setTargetAtTime((0.09 + 0.16 * load) * quiet, t + 0.07, 0.04); if (prof.turbo || prof.harsh) this.burst('bandpass', 400, 1.2, 0.2, 0.12); }
    this.lastGear = s.gear;
    // --- tyres / wind / nitro
    const sp = s.speed;
    this.squeal.g.gain.setTargetAtTime(Math.min(1, s.slip * 1.4) * Math.min(1, sp / 22) * (s.rain > 0.3 ? 0.07 : 0.15) * quiet, t, 0.04);
    this.squeal.f.frequency.setTargetAtTime(1500 + sp * 18 + s.slip * 500, t, 0.05);
    this.wind.g.gain.setTargetAtTime(Math.min(0.22, sp * sp / 7000) * quiet, t, 0.1); this.wind.f.frequency.setTargetAtTime(300 + sp * 14, t, 0.1);
    const nitroOn = s.nitro ? 1 : 0; if (nitroOn && !this._nitro) this.burst('highpass', 2000, 0.6, 0.35, 0.5); this._nitro = nitroOn;
    this.nitroN.g.gain.setTargetAtTime(nitroOn * 0.14 * quiet, t, 0.04); this.nitroN.f.frequency.setTargetAtTime(2600 + sp * 20, t, 0.1);
    // --- weather beds
    this.rain.g.gain.setTargetAtTime(s.rain * 0.11, t, 0.4); this.rain2.g.gain.setTargetAtTime(s.rain * 0.12, t, 0.4);
    if (s.snow > 0.1) this.wind.g.gain.setTargetAtTime(Math.min(0.24, 0.05 + sp * sp / 7000), t, 0.5);
    // --- sirens + helicopter (positional relative to the camera)
    const cam = s.cam, rx = Math.cos(cam.th), rz = -Math.sin(cam.th);
    const pur = (s.units || []).filter(u => u.role === 'pursuit').map(u => ({ u, d: Math.hypot(u.x - cam.x, u.z - cam.z) })).sort((a, b) => a.d - b.d).slice(0, 3);
    this.sirens.forEach((v, i) => {
      const it = pur[i]; if (!it || s.paused) { v.g.gain.setTargetAtTime(0, t, 0.1); return; }
      const dx = it.u.x - cam.x, dz = it.u.z - cam.z, l = it.d || 1, pan = Math.max(-1, Math.min(1, (dx * rx + dz * rz) / l));
      const phase = (t * 2.4 + i * 0.37) % 1, hi = phase < 0.5;                               // UK two-tone 'nee-naw'
      v.o.frequency.setTargetAtTime(hi ? 780 : 585, t, 0.012); v.p.pan.setTargetAtTime(pan, t, 0.05);
      v.g.gain.setTargetAtTime(0.1 / (1 + l / 45), t, 0.08);
    });
    const h = s.heli;
    if (h && h.active) { const d = Math.hypot(h.x - cam.x, h.z - cam.z); const a = Math.min(0.3, 20 / (d + 30)) * quiet; this.heli.g.gain.setTargetAtTime(a, t, 0.2); this.heliLfoG.gain.setTargetAtTime(a, t, 0.2); this.heli.f.frequency.setTargetAtTime(130 + 8 * Math.sin(t), t, 0.1); } else { this.heli.g.gain.setTargetAtTime(0, t, 0.3); this.heliLfoG.gain.setTargetAtTime(0, t, 0.3); }
    // --- music: chase layers with the wanted level
    this.music.setIntensity(s.stars || 0);
  }

  // ---------------- one-shots
  impact(v) { if (!this.ready || v < 1.5) return; const k = Math.min(1, v / 16); this.burst('bandpass', 700, 0.7, 0.5 * k, 0.28); this.tone(95, 0.22, 'sine', 0.5 * k, 0.4); if (k > 0.4) this.burst('highpass', 3000, 0.7, 0.25 * k, 0.4); }
  thunder() { if (!this.ready) return; this.burst('highpass', 2500, 0.5, 0.3, 0.18); const d = 0.15; this.burst('lowpass', 140, 0.5, 0.7, 3.2, this.sfx, d); this.burst('lowpass', 70, 0.5, 0.6, 4, this.sfx, d + 0.3); }
  sting(kind) {
    if (!this.ready) return;
    const m = { wanted: () => { this.tone(220, 0.5, 'sawtooth', 0.18, 0.5); this.tone(233, 0.5, 'sawtooth', 0.18, 0.5, 0.0); this.tone(110, 0.8, 'sine', 0.3); },
      escaped: () => [523, 659, 784, 1047].forEach((f, i) => this.tone(f, 0.35, 'triangle', 0.2, 1, i * 0.1)),
      busted: () => { [392, 349, 311, 233].forEach((f, i) => this.tone(f, 0.4, 'sawtooth', 0.22, 0.98, i * 0.16)); this.burst('lowpass', 200, 0.5, 0.6, 1.2); },
      win: () => [523, 659, 784, 1047, 1319].forEach((f, i) => this.tone(f, 0.45, 'square', 0.12, 1, i * 0.09)),
      lose: () => [330, 294, 262, 196].forEach((f, i) => this.tone(f, 0.5, 'triangle', 0.22, 0.97, i * 0.2)),
      checkpoint: () => { this.tone(880, 0.12, 'square', 0.1); this.tone(1320, 0.18, 'square', 0.1, 1, 0.08); },
      count: () => this.tone(440, 0.18, 'square', 0.14), go: () => this.tone(880, 0.5, 'square', 0.16),
      buy: () => { this.tone(1200, 0.08, 'square', 0.1); this.tone(1800, 0.12, 'square', 0.1, 1, 0.07); }, deny: () => this.tone(140, 0.25, 'sawtooth', 0.2),
      menu: () => this.tone(660, 0.05, 'square', 0.07), open: () => this.tone(330, 0.12, 'triangle', 0.12, 1.5),
    };
    m[kind]?.();
  }
  nextStation() { if (this.ready) this.music.nextStation(); }
}
export { STATIONS };
