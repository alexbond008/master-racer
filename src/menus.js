import { CARS, CAR_ORDER, MPH } from './cars.js';
import { RIVALS } from './races.js';
import { ROWS, modCost, applyMods, displayValue } from './customs.js';

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

export function showDialog(i, ctx) {
  const r = RIVALS[i], car = CARS[r.car];
  const stake = ctx.wager
    ? `YOUR <b>${esc(CARS[ctx.wager].name)}</b> vs HER/HIS <b>${esc(car.name)}</b> &nbsp;·&nbsp; WINNER KEEPS BOTH`
    : r.slipFree
      ? `NO SLIP FROM YOU — WIN AND TAKE THE <b>${esc(car.name)}</b>`
      : `NO CAR TO WAGER &nbsp;·&nbsp; LOSE = <b>$500</b> &nbsp;·&nbsp; WIN = THE <b>${esc(car.name)}</b>`;
  $('dialogCard').innerHTML = `
    <div class="tag">PINK SLIP RACE ${i + 1} OF ${RIVALS.length}</div>
    <h3>${esc(r.name)}</h3>
    <div class="sub">${esc(r.district)} · ${esc(car.name)}</div>
    <div class="quote">“${esc(r.quote)}”</div>
    <div class="row"><span>ROUTE <b>${(ctx.len / 1000).toFixed(1)} KM</b></span><span>WEATHER <b>${esc(ctx.weather)}</b></span><span>TOP SPEED <b>${Math.round(car.vmax * MPH)} MPH</b></span></div>
    <div class="stake">${stake}</div>
    <div class="keys">ENTER — RACE &nbsp;&nbsp;·&nbsp;&nbsp; ESC — BACK OFF</div>`;
  $('dialog').classList.add('open');
}
export const hideDialog = () => $('dialog').classList.remove('open');

export function showGarage(save, sel) {
  const rows = CAR_ORDER.map((id, k) => {
    const c = CARS[id], own = save.owned.includes(id), eq = save.carId === id;
    const top = Math.min(100, c.vmax * MPH / 2.4), acc = Math.min(100, (26 - c.t60) / 24 * 100);
    return `<div class="carrow ${k === sel ? 'sel' : ''} ${own ? '' : 'locked'}">
      <span>${own ? esc(c.name) : '??? LOCKED'}${eq ? ' &nbsp;<b style="color:#3ddc84">EQUIPPED</b>' : ''}</span>
      <span><div class="bar2"><i style="width:${own ? top : 0}%"></i></div></span>
      <span><div class="bar2"><i style="width:${own ? acc : 0}%"></i></div></span>
      <span>${own ? Math.round(c.vmax * MPH) + ' MPH' : ''}</span></div>`;
  }).join('');
  const bl = RIVALS.map((r, i) => {
    const cls = i < save.raceIdx ? 'done' : i === save.raceIdx ? 'next' : 'lock';
    return `<div class="bl ${cls}">${i + 1}. ${esc(r.name)} <span style="float:right">${esc(r.district)}</span></div>`;
  }).join('');
  $('garageCard').innerHTML = `
    <div class="tag">YOUR GARAGE · CASH $${save.cash}</div>
    <h3>WOJTEK'S STABLE</h3>
    <div class="sub">PINK SLIPS WON ${Math.min(save.raceIdx, RIVALS.length)} / ${RIVALS.length}</div>
    <div class="two"><div>
      <div class="carrow" style="border:none;color:#888"><span>CAR</span><span>TOP SPEED</span><span>ACCEL</span><span></span></div>${rows}
    </div><div><div class="tag" style="margin-bottom:6px">THE FIVE — SOUTH LONDON</div>${bl}</div></div>
    <div class="keys">↑ ↓ SELECT &nbsp;·&nbsp; ENTER EQUIP &nbsp;·&nbsp; TAB / ESC CLOSE</div>`;
  $('garage').classList.add('open');
}
export const hideGarage = () => $('garage').classList.remove('open');

// ---- Master Customs
export function showCustoms(c) {
  const { def, work, saved, sel, cash } = c;
  const total = modCost(def, saved, work);
  const rows = ROWS.map((row, i) => {
    let val = '', price = '';
    if (row.kind === 'swatch') {
      val = row.opts.map(o => (o === 'off' ? `<span class="sw ${work[row.key] === 'off' ? 'on' : ''}" style="background:#111;position:relative"></span>` : `<span class="sw ${work[row.key] === o ? 'on' : ''}" style="background:${o}"></span>`)).join('');
      if (i !== sel) val = row.key === 'neon' && work.neon === 'off' ? 'OFF' : `<span class="sw on" style="background:${work[row.key]}"></span>`;
    } else if (row.kind === 'list') val = String(work[row.key]).toUpperCase();
    else if (row.kind === 'level') { const l = displayValue(def, work, row), cur = saved.perf[row.idx]; val = [1, 2, 3].map(n => `<span class="pip ${n <= cur ? 'cur' : n <= l ? 'on' : ''}"></span>`).join(''); }
    else if (row.kind === 'action') val = total ? `$${total}` : 'EXIT';
    if (row.kind !== 'action') { const one = { ...saved, perf: [...saved.perf] }; if (row.kind === 'level') one.perf[row.idx] = work.perf[row.idx]; else one[row.key] = work[row.key]; const pc = modCost(def, saved, one); price = pc ? `$${pc}` : ''; }
    return `<div class="crow ${i === sel ? 'sel' : ''}"><span>${row.label}</span><span class="v">${val}<span class="price">${price}</span></span></div>`;
  }).join('');
  const a = applyMods(def, saved), b = applyMods(def, work), MPH = 2.23694;
  const st = (l, x, y, fmt, better) => `<div><span>${l}</span><span class="${better(x, y) ? 'up' : ''}">${fmt(x)} → ${fmt(y)}</span></div>`;
  $('customs').innerHTML = `
    <h3>MASTER CUSTOMS</h3><div class="sub">${esc(def.name)}</div>
    ${rows}
    <div class="stats">
      ${st('TOP SPEED', a.vmax * MPH, b.vmax * MPH, v => Math.round(v) + ' MPH', (x, y) => y > x)}
      ${st('0-60', a.t60, b.t60, v => v.toFixed(1) + 's', (x, y) => y < x)}
      ${st('GRIP', a.grip, b.grip, v => v.toFixed(2), (x, y) => y > x)}
      ${st('NITRO BURN', a.nitroDrain || 22, b.nitroDrain || 22, v => v.toFixed(1) + '/s', (x, y) => y < x)}
    </div>
    <div class="foot">CASH <b>$${cash}</b> &nbsp; TOTAL <b style="color:${total > cash ? '#ff3b3b' : '#fff'}">$${total}</b><br>
    <span style="color:#888;font-size:12px">↑↓ ROW &nbsp;·&nbsp; ←→ CHANGE &nbsp;·&nbsp; ENTER BUY &nbsp;·&nbsp; ESC CANCEL</span></div>`;
  $('customs').classList.add('open');
}
export const hideCustoms = () => $('customs').classList.remove('open');
