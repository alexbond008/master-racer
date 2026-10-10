// Procedural radio: original instrumentals synthesised live with Web Audio (no samples, nothing licensed).
// Stations: BOOM BAP FM (2000s NYC hip hop), DRILL RADIO (UK drill), ROCK 107 (riff rock). Plus a dynamic CHASE track.
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
const MINOR = [0, 2, 3, 5, 7, 8, 10], PENT = [0, 3, 5, 7, 10];
const chordOf = (root, kind) => ({ m7: [0, 3, 7, 10], m: [0, 3, 7], p5: [0, 7, 12], m9: [0, 3, 7, 10, 14], dim: [0, 3, 6] }[kind]).map(i => root + i);
const rng = seed => () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const hit = (pat, i) => pat[i % pat.length] === 'x' || pat[i % pat.length] === 'X';
const loud = (pat, i) => pat[i % pat.length] === 'X';

// ---- tracks ------------------------------------------------------------------------------------------------------
// bars: [rootMidi, chordKind] per bar; patterns are 16-step strings (x hit, X accent, . rest)
export const STATIONS = [
  { id: 'boombap', name: 'BOOM BAP FM', style: 'boombap', tracks: [
    { name: 'DEAD END POETRY', bpm: 92, swing: 0.57, bars: [[48, 'm7'], [44, 'm7'], [41, 'm7'], [43, 'm']], kick: 'X.....x...x.x...', snare: '....X.......X..x', hat: 'x.x.x.x.x.x.x.xx', seed: 11 },
    { name: 'SOUTH SIDE STATIC', bpm: 88, swing: 0.58, bars: [[50, 'm7'], [46, 'm7'], [43, 'm7'], [45, 'm']], kick: 'X..x..x...x.....', snare: '....X.......X...', hat: 'x.xxx.x.x.xxx.x.', seed: 29 },
    { name: 'IRON LUNG', bpm: 95, swing: 0.56, bars: [[43, 'm7'], [39, 'm7'], [36, 'm7'], [38, 'm']], kick: 'X.x...x...x.x...', snare: '....X.....x.X...', hat: 'x.x.x.x.x.x.x.x.', seed: 47 },
  ] },
  { id: 'drill', name: 'DRILL RADIO', style: 'drill', tracks: [
    { name: 'COLD STREETS', bpm: 140, swing: 0, bars: [[30, 'm'], [30, 'm'], [28, 'm'], [33, 'm']], kick: 'X......x..x.....', snare: '........X.......', hat: 'x.xxx.xx.xx.xxx.', seed: 5 },
    { name: 'PECKHAM NIGHTS', bpm: 142, swing: 0, bars: [[33, 'm'], [33, 'm'], [31, 'm'], [29, 'm']], kick: 'X.....x...x.....', snare: '........X..x....', hat: 'x.x.xxx.x.xx.x.x', seed: 17 },
    { name: 'SLIDE OVER', bpm: 138, swing: 0, bars: [[28, 'm'], [31, 'm'], [26, 'm'], [28, 'm']], kick: 'X.x....x...x....', snare: '........X.......', hat: 'xxx.xx.xxx.xx.xx', seed: 23 },
  ] },
  { id: 'rock', name: 'ROCK 107', style: 'rock', tracks: [
    { name: 'BURN THE CLUTCH', bpm: 128, swing: 0, bars: [[40, 'p5'], [43, 'p5'], [45, 'p5'], [43, 'p5']], kick: 'X...x.x.X...x.x.', snare: '....X.......X...', hat: 'x.x.x.x.x.x.x.x.', seed: 3 },
    { name: 'RUBBER & STEEL', bpm: 140, swing: 0, bars: [[45, 'p5'], [45, 'p5'], [41, 'p5'], [43, 'p5']], kick: 'X..x..x.X..x..x.', snare: '....X.......X..x', hat: 'xxxxxxxxxxxxxxxx', seed: 8 },
    { name: 'ZAMOSC THUNDER', bpm: 120, swing: 0, bars: [[38, 'p5'], [34, 'p5'], [41, 'p5'], [36, 'p5']], kick: 'X.....x.X.x...x.', snare: '....X.......X...', hat: 'x.x.x.x.x.x.x.x.', seed: 13 },
  ] },
];
const CHASE = { name: 'HEAT', bpm: 150, bars: [[33, 'm'], [33, 'm'], [29, 'm'], [31, 'm']] };

export class Music {
  constructor(ctx, bus, noise) {
    this.ctx = ctx; this.noise = noise; this.out = ctx.createGain(); this.out.gain.value = 0; this.out.connect(bus);
    this.chaseOut = ctx.createGain(); this.chaseOut.gain.value = 0; this.chaseOut.connect(bus);
    this.station = -1; this.trackIdx = 0; this.step = 0; this.next = 0; this.cstep = 0; this.cnext = 0; this.intensity = 0;
    this.onTrack = null; this.t = null; this.running = false;
    this.dist = (() => { const c = new Float32Array(256); for (let i = 0; i < 256; i++) { const x = i / 128 - 1; c[i] = Math.tanh(x * 5); } return c; })();
  }
  start() { if (this.running) return; this.running = true; this.next = this.cnext = this.ctx.currentTime + 0.1; this.t = setInterval(() => this.tick(), 30); }

  // station -1 = radio off
  setStation(i, announce = true) {
    this.station = i; this.step = 0; this.next = this.ctx.currentTime + 0.05; this.trackIdx = Math.floor(Math.random() * 3); this.bar = 0;
    this.out.gain.cancelScheduledValues(0); this.out.gain.setTargetAtTime(i < 0 ? 0 : 0.55, this.ctx.currentTime, 0.15);
    if (announce) this.announce();
  }
  announce() { const st = STATIONS[this.station]; this.onTrack?.(st ? { station: st.name, track: st.tracks[this.trackIdx].name } : { station: 'RADIO OFF', track: '' }); }
  nextStation() { this.setStation(this.station >= STATIONS.length - 1 ? -1 : this.station + 1); }
  setIntensity(v) { this.intensity = v; const on = v > 0; this.chaseOut.gain.setTargetAtTime(on ? 0.6 : 0, this.ctx.currentTime, 0.4); this.out.gain.setTargetAtTime(this.station < 0 ? 0 : (on ? 0.12 : 0.55), this.ctx.currentTime, 0.5); }

  tick() {
    const now = this.ctx.currentTime, ahead = now + 0.16;
    if (this.station >= 0) while (this.next < ahead) { this.playStep(); }
    if (this.intensity > 0) while (this.cnext < ahead) { this.playChase(); }
    else if (this.cnext < now) this.cnext = now;
  }

  // ---------------- station sequencer
  playStep() {
    const st = STATIONS[this.station], tr = st.tracks[this.trackIdx], i = this.step, bar = Math.floor(i / 16) % 4, s16 = 60 / tr.bpm / 4;
    let t = this.next; if (i % 2 === 1 && tr.swing) t += s16 * (tr.swing * 2 - 1);
    const r = rng(tr.seed * 131 + i), [root, kind] = tr.bars[bar], chord = chordOf(root, kind), k = i % 16;
    const out = this.out;
    if (st.style === 'boombap') {
      if (hit(tr.kick, k)) this.kick(out, t, loud(tr.kick, k) ? 1 : 0.7, 150, 44);
      if (hit(tr.snare, k)) this.snare(out, t, loud(tr.snare, k) ? 1 : 0.5);
      if (hit(tr.hat, k)) this.hat(out, t, k % 4 === 2 ? 0.28 : 0.17, false);
      if (k === 0 || k === 6 || (k === 10 && bar % 2)) chord.forEach((m, j) => this.epiano(out, t + j * 0.006, m + 12, s16 * 5, 0.11));
      if (k === 0 || k === 7 || k === 11) this.pluck(out, t, root - 12 + (k === 7 ? 12 : 0), s16 * 2.4, 0.4);
      if (k % 8 === 3 && r() < 0.6) this.epiano(out, t, root + 24 + [0, 3, 7, 10][(r() * 4) | 0], s16 * 2, 0.06); // eerie motif note
      if (k === 0) this.noiseHiss(out, t, s16 * 16, 0.012); // vinyl dust
    } else if (st.style === 'drill') {
      if (hit(tr.kick, k)) this.kick(out, t, 1, 170, 38);
      if (hit(tr.snare, k)) { this.snare(out, t, 1, true); this.clap(out, t); }
      if (hit(tr.hat, k)) this.hat(out, t, k % 2 ? 0.12 : 0.2, false);
      if (bar % 2 && k >= 12 && k % 2 === 0) { this.hat(out, t + s16 / 2, 0.1, false); this.hat(out, t + s16 * 0.25, 0.07, false); } // rolls
      const glideTo = (k === 10 ? root - 2 : k === 14 ? root + 3 : root);
      if (k === 0 || k === 7 || k === 10 || k === 14) this.sub808(out, t, root, glideTo, s16 * (k === 0 ? 6 : 3.4), 0.7);
      const arp = [0, 3, 7, 3, 12, 7, 3, 0][k % 8]; if (k % 2 === 0) this.darkPiano(out, t, root + 24 + arp, s16 * 3, 0.1);
    } else { // rock
      if (hit(tr.kick, k)) this.kick(out, t, loud(tr.kick, k) ? 1 : 0.8, 120, 52);
      if (hit(tr.snare, k)) this.snare(out, t, 1, false, true);
      if (hit(tr.hat, k)) this.hat(out, t, 0.14, k % 8 === 7);
      if (k === 0) this.crash(out, t);
      if (k % 2 === 0) { const pm = k % 8 === 6 ? 0.28 : 0.1; this.guitar(out, t, root + 12, s16 * (k % 4 === 0 ? 1.7 : 0.8), 0.22, pm); }
      if (k % 2 === 0) this.rockBass(out, t, root, s16 * 1.8, 0.3);
      if (bar >= 2 && k % 4 === 2) this.lead(out, t, root + 24 + PENT[(r() * 5) | 0], s16 * 2.5, 0.07);
    }
    this.next += s16; this.step++;
    if (this.step >= 64) { this.step = 0; this.bar = (this.bar || 0) + 1; if (this.bar % 3 === 0) { this.trackIdx = (this.trackIdx + 1) % 3; this.announce(); } }
  }

  // ---------------- chase track (layers rise with stars)
  playChase() {
    const lvl = this.intensity, s16 = 60 / CHASE.bpm / 4, t = this.cnext, i = this.cstep, k = i % 16, bar = Math.floor(i / 16) % 4, [root] = CHASE.bars[bar], o = this.chaseOut;
    if (k % 4 === 0) this.kick(o, t, 1, 160, 46);
    if (lvl >= 2 && (k === 4 || k === 12)) this.snare(o, t, 0.9, false, true);
    if (lvl >= 1 && k % 2 === 0) this.hat(o, t, 0.12, false);
    if (lvl >= 3 && k % 2 === 1) this.hat(o, t, 0.07, false);
    this.synthBass(o, t, root, s16 * 0.9, 0.5);
    if (lvl >= 2 && (k === 0 || k === 6 || k === 10)) chordOf(root + 24, 'm').forEach(m => this.stab(o, t, m, s16 * 1.2, 0.07));
    if (lvl >= 4 && k % 2 === 0) this.stab(o, t, root + 36 + [0, 3, 7, 12][(k / 2) % 4], s16 * 0.9, 0.05);
    if (lvl >= 5 && k === 0) this.riser(o, t, s16 * 16, 0.12);
    if (k === 0 && bar === 0) this.tom(o, t, 0.6);
    this.cnext += s16; this.cstep++;
  }

  // ---------------- voices
  g(out, t, a, peak, hold, rel) { const g = this.ctx.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(peak, t + a); g.gain.setValueAtTime(peak, t + a + hold); g.gain.exponentialRampToValueAtTime(0.0001, t + a + hold + rel); g.connect(out); return g; }
  osc(type, f, t, d, dest, f2) { const o = this.ctx.createOscillator(); o.type = type; o.frequency.setValueAtTime(f, t); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + d * 0.6); o.connect(dest); o.start(t); o.stop(t + d + 0.05); return o; }
  nz(t, d, dest, off = 0) { const s = this.ctx.createBufferSource(); s.buffer = this.noise; s.loop = true; s.connect(dest); s.start(t, off); s.stop(t + d + 0.05); return s; }
  filt(type, f, q, dest) { const b = this.ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; b.Q.value = q; b.connect(dest); return b; }

  kick(out, t, v, f0, f1) { const g = this.g(out, t, 0.002, 0.9 * v, 0.02, 0.28); this.osc('sine', f0, t, 0.3, g, f1); const c = this.g(out, t, 0.001, 0.25 * v, 0, 0.02); this.nz(t, 0.03, this.filt('highpass', 1500, 0.7, c)); }
  snare(out, t, v, tight, rock) { const g = this.g(out, t, 0.001, 0.5 * v, 0.01, rock ? 0.22 : 0.16); this.nz(t, 0.25, this.filt('bandpass', rock ? 3000 : 2200, 0.8, g)); const b = this.g(out, t, 0.001, 0.35 * v, 0, 0.09); this.osc('triangle', tight ? 220 : 180, t, 0.1, b, 120); }
  clap(out, t) { for (let j = 0; j < 3; j++) { const g = this.g(out, t + j * 0.012, 0.001, 0.22, 0, 0.07); this.nz(t + j * 0.012, 0.08, this.filt('bandpass', 1500, 1.2, g)); } }
  hat(out, t, v, open) { const g = this.g(out, t, 0.001, v, 0, open ? 0.2 : 0.045); this.nz(t, 0.25, this.filt('highpass', 7500, 0.8, g), Math.random() * 0.5); }
  crash(out, t) { const g = this.g(out, t, 0.002, 0.2, 0.05, 1.1); this.nz(t, 1.2, this.filt('highpass', 5500, 0.6, g)); }
  tom(out, t, v) { const g = this.g(out, t, 0.002, 0.5 * v, 0.02, 0.3); this.osc('sine', 140, t, 0.35, g, 70); }
  noiseHiss(out, t, d, v) { const g = this.g(out, t, 0.3, v, d, 0.3); this.nz(t, d, this.filt('highpass', 2500, 0.5, g)); }
  epiano(out, t, m, d, v) { const g = this.g(out, t, 0.004, v, 0.02, d); this.osc('sine', mtof(m), t, d, g); const g2 = this.g(out, t, 0.002, v * 0.35, 0, d * 0.4); this.osc('sine', mtof(m) * 3.01, t, d * 0.4, g2); const g3 = this.g(out, t, 0.002, v * 0.18, 0, d * 0.2); this.osc('triangle', mtof(m) * 2, t, d * 0.2, g3); }
  pluck(out, t, m, d, v) { const g = this.g(out, t, 0.003, v, 0.01, d); this.osc('sine', mtof(m), t, d, g); const g2 = this.g(out, t, 0.002, v * 0.4, 0, d * 0.5); this.osc('triangle', mtof(m) * 2, t, d * 0.5, g2); }
  sub808(out, t, m, mTo, d, v) { const g = this.g(out, t, 0.004, v, d * 0.5, d * 0.5); const ws = this.ctx.createWaveShaper(); ws.curve = this.dist; ws.oversample = '2x'; const pre = this.ctx.createGain(); pre.gain.value = 0.55; pre.connect(ws); ws.connect(g); const o = this.ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(mtof(m), t); o.frequency.exponentialRampToValueAtTime(mtof(mTo), t + d * 0.7); o.connect(pre); o.start(t); o.stop(t + d + 0.1); }
  darkPiano(out, t, m, d, v) { const f = mtof(m), g = this.g(out, t, 0.003, v, 0.01, d); this.osc('sine', f, t, d, g); const g2 = this.g(out, t, 0.002, v * 0.5, 0, d * 0.6); this.osc('triangle', f * 2, t, d * 0.6, g2); const g3 = this.g(out, t, 0.001, v * 0.2, 0, d * 0.25); this.osc('sine', f * 4.02, t, d * 0.25, g3); }
  guitar(out, t, m, d, v, mute) {
    const g = this.g(out, t, 0.003, v, d * mute * 3, d), ws = this.ctx.createWaveShaper(); ws.curve = this.dist; const lp = this.filt('lowpass', 2600, 0.7, g); ws.connect(lp);
    const pre = this.ctx.createGain(); pre.gain.value = 0.5; pre.connect(ws);
    for (const [r, det] of [[1, 0], [1, 6], [1.4983, -4], [2, 3]]) { const o = this.ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.setValueAtTime(mtof(m) * r, t); o.detune.value = det; o.connect(pre); o.start(t); o.stop(t + d * (1 + mute * 3) + 0.2); }
  }
  rockBass(out, t, m, d, v) { const g = this.g(out, t, 0.004, v, d * 0.5, d * 0.5); this.osc('sawtooth', mtof(m - 12), t, d, this.filt('lowpass', 500, 0.9, g)); const s = this.g(out, t, 0.004, v * 0.6, d * 0.5, d * 0.5); this.osc('sine', mtof(m - 12), t, d, s); }
  lead(out, t, m, d, v) { const g = this.g(out, t, 0.005, v, d * 0.3, d), ws = this.ctx.createWaveShaper(); ws.curve = this.dist; ws.connect(this.filt('lowpass', 3500, 0.7, g)); const pre = this.ctx.createGain(); pre.gain.value = 0.4; pre.connect(ws); this.osc('sawtooth', mtof(m), t, d, pre); }
  synthBass(out, t, m, d, v) { const g = this.g(out, t, 0.003, v, d * 0.3, d * 0.6); const f = this.filt('lowpass', 700, 4, g); this.osc('sawtooth', mtof(m - 12), t, d, f); this.osc('square', mtof(m - 24), t, d, g); }
  stab(out, t, m, d, v) { const g = this.g(out, t, 0.003, v, d * 0.2, d), f = this.filt('lowpass', 2200, 1, g); this.osc('sawtooth', mtof(m), t, d, f); this.osc('sawtooth', mtof(m) * 1.007, t, d, f); }
  riser(out, t, d, v) { const g = this.ctx.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + d * 0.95); g.gain.exponentialRampToValueAtTime(0.0001, t + d); const f = this.ctx.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 3; f.frequency.setValueAtTime(300, t); f.frequency.exponentialRampToValueAtTime(5000, t + d); f.connect(g); g.connect(out); this.nz(t, d, f); }
}
