import { MPH } from './cars.js';
import { DISTRICTS, WORLD } from './world.js';

const $ = id => document.getElementById(id);

export class Hud {
  constructor(world) {
    this.world = world;
    this.sp = $('speedo').getContext('2d');
    this.mm = $('minimap').getContext('2d');
    this.big = $('bigmapCanvas'); this.bigCtx = this.big.getContext('2d');
    this.big.width = 760; this.big.height = Math.round(760 * (WORLD.h + 120) / (WORLD.w + 120));
    this.mapImg = this.renderMap();
    this.route = null; this.dest = null;
    this.bigOpen = false;
    this.zoom = 0.9;

    this.big.addEventListener('click', e => {
      const r = this.big.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width, pz = (e.clientY - r.top) / r.height;
      const wx = -60 + px * (WORLD.w + 120), wz = -60 + pz * (WORLD.h + 120);
      this.onSetDest?.(wx, wz);
    });
  }

  renderMap() {
    const S = 0.4, net = this.world.net, W = WORLD.w, H = WORLD.h;
    const cv = document.createElement('canvas'); cv.width = Math.round((W + 120) * S); cv.height = Math.round((H + 120) * S);
    const x = cv.getContext('2d');
    x.scale(S, S); x.translate(60, 60);
    x.fillStyle = '#0f1013'; x.fillRect(-60, -60, W + 120, H + 120);
    x.fillStyle = '#1c1e23'; x.fillRect(0, 0, W, H);
    x.fillStyle = '#1f4a26';
    for (const pk of this.world.parks) { x.beginPath(); pk.pts.forEach(([px, pz], i) => (i ? x.lineTo(px, pz) : x.moveTo(px, pz))); x.closePath(); x.fill(); }
    // roads, big ones on top
    const width = [11, 9, 7.5, 5.5], color = ['#7a7f8a', '#666b76', '#555a64', '#454953'];
    x.lineCap = 'round'; x.lineJoin = 'round';
    for (const cls of [3, 2, 1, 0]) {
      x.strokeStyle = color[cls]; x.lineWidth = width[cls]; x.beginPath();
      for (const e of net.edges) if (e.cls === cls) e.pts.forEach(([px, pz], i) => (i ? x.lineTo(px, pz) : x.moveTo(px, pz)));
      x.stroke();
    }
    x.strokeStyle = '#d9a441'; x.lineWidth = 3; x.beginPath(); for (const e of net.edges) if (e.a23) e.pts.forEach(([px, pz], i) => (i ? x.lineTo(px, pz) : x.moveTo(px, pz))); x.stroke();
    // district wash + names
    for (const k in DISTRICTS) {
      const d = DISTRICTS[k], g = x.createRadialGradient(d.c[0], d.c[1], 20, d.c[0], d.c[1], 320);
      g.addColorStop(0, d.tint + '44'); g.addColorStop(1, d.tint + '00'); x.fillStyle = g; x.fillRect(d.c[0] - 320, d.c[1] - 320, 640, 640);
      x.fillStyle = '#fff'; x.font = 'bold 56px "Arial Narrow", Arial'; x.textAlign = 'center'; x.fillText(d.name, d.c[0], d.c[1] - 60);
    }
    for (const l of this.world.landmarks) { x.fillStyle = '#ffb400'; x.beginPath(); x.arc(l.x, l.z, 9, 0, 7); x.fill(); }
    // road names: longest edge of each distinct main road
    const best = new Map();
    for (const e of net.edges) if (e.cls <= 1 && e.name && e.len > 90 && (!best.has(e.name) || best.get(e.name).len < e.len)) best.set(e.name, e);
    x.fillStyle = '#ffffffcc'; x.font = 'bold 26px "Arial Narrow", Arial'; x.textAlign = 'center';
    for (const [name, e] of best) {
      const m = net.pointAt(e, 1, e.len / 2); let a = Math.atan2(m.tz, m.tx); if (a > Math.PI / 2) a -= Math.PI; if (a < -Math.PI / 2) a += Math.PI;
      x.save(); x.translate(m.x, m.z); x.rotate(a); x.fillText(name, 0, -9); x.restore();
    }
    return cv;
  }

  setRoute(route, dest) { this.route = route; this.dest = dest; }
  toggleMap(force) { this.bigOpen = force ?? !this.bigOpen; $('bigmap').classList.toggle('open', this.bigOpen); }

  drawRoute(ctx, w) {
    if (!this.route || this.route.length < 2) return;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.strokeStyle = '#000'; ctx.lineWidth = w + 2 / this.cs; ctx.beginPath();
    this.route.forEach(([x, z], i) => (i ? ctx.lineTo(x, z) : ctx.moveTo(x, z))); ctx.stroke();
    ctx.strokeStyle = '#37d4ff'; ctx.lineWidth = w; ctx.beginPath();
    this.route.forEach(([x, z], i) => (i ? ctx.lineTo(x, z) : ctx.moveTo(x, z))); ctx.stroke();
    if (this.dest) { ctx.fillStyle = '#ff2d2d'; ctx.beginPath(); ctx.arc(this.dest[0], this.dest[1], w * 1.6, 0, 7); ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = w * 0.4; ctx.stroke(); }
  }

  drawBlips(ctx, Z) {
    const t = Math.floor(performance.now() / 250) % 2;
    for (const b of this.blips || []) {
      const r = 7 / Z;
      if (b.k === 'shop') { ctx.fillStyle = '#37d4ff'; ctx.strokeStyle = '#000'; ctx.lineWidth = 2 / Z; ctx.fillRect(b.x - r, b.z - r, r * 2, r * 2); ctx.strokeRect(b.x - r, b.z - r, r * 2, r * 2); continue; }
      if (b.k === 'pin' || b.k === 'pinlock') { ctx.fillStyle = b.k === 'pin' ? '#ffb400' : '#777'; ctx.strokeStyle = '#000'; ctx.lineWidth = 2 / Z; ctx.beginPath(); ctx.moveTo(b.x, b.z - r * 1.4); ctx.lineTo(b.x + r, b.z); ctx.lineTo(b.x, b.z + r * 1.4); ctx.lineTo(b.x - r, b.z); ctx.closePath(); ctx.fill(); ctx.stroke(); continue; }
      if (b.k === 'rival') { ctx.fillStyle = '#ff5ad0'; ctx.strokeStyle = '#000'; ctx.lineWidth = 2 / Z; ctx.beginPath(); ctx.arc(b.x, b.z, r * 1.1, 0, 7); ctx.fill(); ctx.stroke(); continue; }
      if (b.k === 'cp') { ctx.strokeStyle = '#3dff9a'; ctx.lineWidth = 3 / Z; ctx.beginPath(); ctx.arc(b.x, b.z, r * 1.4, 0, 7); ctx.stroke(); continue; }
      if (b.k === 'block') { ctx.strokeStyle = '#ff3b3b'; ctx.lineWidth = 3 / Z; ctx.beginPath(); ctx.moveTo(b.x - r, b.z - r); ctx.lineTo(b.x + r, b.z + r); ctx.moveTo(b.x + r, b.z - r); ctx.lineTo(b.x - r, b.z + r); ctx.stroke(); continue; }
      ctx.fillStyle = b.k === 'disabled' ? '#666' : b.k === 'heli' ? '#fff' : (t ? '#ff3030' : '#3a6bff');
      if (b.k === 'patrol') ctx.fillStyle = '#5a7bd6';
      ctx.beginPath(); ctx.arc(b.x, b.z, b.k === 'heli' ? r * 1.3 : r * 0.8, 0, 7); ctx.fill();
    }
  }

  minimap(p) {
    const ctx = this.mm, W = 440, Z = this.zoom * (W / 440) * 1.0;
    this.cs = Z;
    ctx.save(); ctx.clearRect(0, 0, W, W);
    ctx.translate(W / 2, W / 2 + 40); ctx.rotate(p.th - Math.PI); ctx.scale(Z, Z); ctx.translate(-p.x, -p.z);
    ctx.drawImage(this.mapImg, -60, -60, WORLD.w + 120, WORLD.h + 120);
    this.drawRoute(ctx, 10);
    this.drawBlips(ctx, Z);
    ctx.restore();
    // player arrow
    ctx.save(); ctx.translate(W / 2, W / 2 + 40);
    ctx.fillStyle = '#ffb400'; ctx.strokeStyle = '#000'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(0, -20); ctx.lineTo(13, 14); ctx.lineTo(0, 7); ctx.lineTo(-13, 14); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  bigmap(p) {
    const c = this.bigCtx, W = this.big.width, Hh = this.big.height;
    c.clearRect(0, 0, W, Hh);
    c.drawImage(this.mapImg, 0, 0, W, Hh);
    const k = W / (WORLD.w + 120);
    c.save(); c.scale(k, k); c.translate(60, 60);
    this.cs = k;
    this.drawRoute(c, 12);
    this.drawBlips(c, this.cs);
    c.translate(p.x, p.z); c.rotate(-p.th + Math.PI);
    c.fillStyle = '#ffb400'; c.strokeStyle = '#000'; c.lineWidth = 6;
    c.beginPath(); c.moveTo(0, -34); c.lineTo(22, 26); c.lineTo(0, 12); c.lineTo(-22, 26); c.closePath(); c.fill(); c.stroke();
    c.restore();
  }

  speedo(p) {
    const c = this.sp, W = 520, cx = W / 2, cy = W / 2, R = 220;
    c.clearRect(0, 0, W, W);
    const mph = p.speed * MPH, top = Math.ceil(p.def.vmax * 1.25 * MPH / 20) * 20;
    const a0 = Math.PI * 0.8, a1 = Math.PI * 2.2, ang = v => a0 + (a1 - a0) * Math.min(1, v / top);
    // dial
    c.fillStyle = 'rgba(8,8,10,.72)'; c.beginPath(); c.arc(cx, cy, R + 14, 0, 7); c.fill();
    c.lineWidth = 6; c.strokeStyle = '#ffb400'; c.beginPath(); c.arc(cx, cy, R + 8, a0, a1); c.stroke();
    // ticks
    c.fillStyle = '#fff'; c.font = '600 22px "Arial Narrow", Arial'; c.textAlign = 'center'; c.textBaseline = 'middle';
    for (let v = 0; v <= top; v += 10) {
      const a = ang(v), major = v % 20 === 0, r1 = R - (major ? 26 : 14);
      c.strokeStyle = v > top * 0.82 ? '#ff2d2d' : '#fff'; c.lineWidth = major ? 4 : 2;
      c.beginPath(); c.moveTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R); c.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); c.stroke();
      if (major && v % 40 === 0) c.fillText(v, cx + Math.cos(a) * (R - 52), cy + Math.sin(a) * (R - 52));
    }
    // rpm arc (inner)
    c.lineWidth = 12; c.strokeStyle = p.rpm > 0.88 ? '#ff2d2d' : '#37d4ff'; c.beginPath(); c.arc(cx, cy, R - 80, a0, a0 + (a1 - a0) * p.rpm); c.stroke();
    // nitro arc
    c.lineWidth = 10; c.strokeStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.arc(cx, cy, R - 98, a0, a1); c.stroke();
    c.strokeStyle = p.nitroOn ? '#9a6bff' : '#4d7bff'; c.beginPath(); c.arc(cx, cy, R - 98, a0, a0 + (a1 - a0) * p.nitro / 100); c.stroke();
    // needle
    const na = ang(mph);
    c.strokeStyle = '#ff2d2d'; c.lineWidth = 6; c.lineCap = 'round';
    c.beginPath(); c.moveTo(cx - Math.cos(na) * 20, cy - Math.sin(na) * 20); c.lineTo(cx + Math.cos(na) * (R - 12), cy + Math.sin(na) * (R - 12)); c.stroke();
    c.fillStyle = '#222'; c.beginPath(); c.arc(cx, cy, 16, 0, 7); c.fill();
    // digits
    c.fillStyle = '#fff'; c.font = 'italic 700 92px Impact, "Arial Narrow"'; c.fillText(Math.round(mph), cx, cy + 62);
    c.font = '600 24px "Arial Narrow", Arial'; c.fillStyle = '#ffb400'; c.fillText('MPH', cx, cy + 112);
    c.font = 'italic 700 54px Impact'; c.fillStyle = '#fff'; c.fillText(p.gear === 0 ? 'R' : (p.speed < 0.5 ? 'N' : p.gear), cx + 130, cy + 140);
  }

  update(p, info) {
    this.blips = info.blips;
    const rc = $('race');
    if (info.race) {
      const r = info.race; rc.style.display = 'block';
      const pe = rc.querySelector('.pos'); pe.textContent = r.pos === 1 ? '1ST' : '2ND'; pe.className = 'pos' + (r.pos === 1 ? '' : ' behind');
      rc.querySelector('.gap').textContent = `${r.name}  ${r.gap >= 0 ? '+' : ''}${r.gap} M`;
      rc.querySelector('.cp').textContent = `CHECKPOINT ${r.cp}/${r.total}`;
      const t = r.t; rc.querySelector('.time').textContent = `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`;
    } else rc.style.display = 'none';
    $('cash').textContent = '$' + (info.cash ?? 0);
    const pr = $('prompt'); pr.style.display = info.prompt ? 'block' : 'none'; if (info.prompt) pr.textContent = info.prompt;
    this.speedo(p);
    if (this.bigOpen) this.bigmap(p);
    this.minimap(p);
    $('district').textContent = info.district + (info.road ? '  ·  ' + info.road : '');
    $('weatherTag').textContent = info.weather + (info.grip < 0.99 ? `  ·  GRIP ${Math.round(info.grip * 100)}%` : '');
    $('carName').textContent = p.def.name;
    $('guide').textContent = info.guide || '';
    const w = $('wanted'), pol = info.police;
    if (pol && pol.stars > 0) {
      w.className = pol.bust > 0.05 ? 'busting' : pol.seen ? 'spotted' : 'evading';
      w.querySelector('.lbl').textContent = pol.bust > 0.05 ? 'BUSTING…' : pol.seen ? 'SPOTTED' : 'EVADING…';
      w.querySelector('.fill').style.width = (pol.bust > 0.05 ? pol.bust : pol.seen ? 0 : pol.evade) * 100 + '%';
    } else { w.className = ''; w.querySelector('.lbl').textContent = ''; w.querySelector('.fill').style.width = '0'; }
    const hp = $('hp'); hp.style.width = Math.max(0, info.hp) + '%'; hp.style.background = info.hp > 55 ? '#3ddc84' : info.hp > 25 ? '#ffb400' : '#ff3b3b';
    const st = $('stars'); const heat = info.stars || 0;
    st.innerHTML = [1, 2, 3, 4, 5].map(i => `<span class="${i <= heat ? 'on' : ''}">★</span>`).join('');
  }
}
