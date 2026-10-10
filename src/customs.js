// Master Customs: options, prices, performance effects.
export const PAINTS = ['#c8321f', '#ff4fa3', '#ff7a1a', '#ffd21a', '#3ddc84', '#1ecbe1', '#1b3a9c', '#7a3dff', '#f2f2f2', '#8da1b9', '#15171c', '#5a2d12'];
export const RIMS = ['#c9ccd2', '#d4a63a', '#15171c', '#ff4fa3', '#31e0ff', '#ff2d2d', '#3ddc84', '#f2f2f2'];
export const NEONS = ['off', '#31e0ff', '#ff4fa3', '#7a3dff', '#3ddc84', '#ff2d2d', '#ffd21a'];
export const FINISHES = ['gloss', 'matte', 'metallic', 'chrome'];
export const SPOILERS = ['stock', 'none', 'lip', 'ducktail', 'gt', 'bigwing'];
export const KITS = ['stock', 'street', 'wide'];
export const LIVERIES = ['stock', 'none', 'stripes', 'flames', 'checker', 'roundel', 'sakura'];
export const LIVERY_COLORS = ['#ffffff', '#111111', '#ffd21a', '#ff2d2d', '#31e0ff', '#ff4fa3', '#3ddc84', '#7a3dff'];
export const PERF = [['ENGINE', 'engine'], ['TURBO', 'turbo'], ['TYRES', 'tyres'], ['NITRO', 'nitro']];
const PERF_STEP = [0, 500, 900, 1500]; // cost to REACH level n

export const PRICE = {
  color: 100, rim: 80, liveryColor: 50, neon: 250,
  finish: { gloss: 0, matte: 150, metallic: 200, chrome: 500 },
  spoiler: { stock: 0, none: 0, lip: 150, ducktail: 250, gt: 350, bigwing: 500 },
  kit: { stock: 0, street: 400, wide: 800 },
  livery: { stock: 0, none: 0, stripes: 250, flames: 300, checker: 250, roundel: 200, sakura: 400 },
};

export function defaultMods(def) {
  return { color: def.color, finish: 'gloss', rim: def.wheelColor || '#c9ccd2', spoiler: 'stock', kit: 'stock', livery: 'stock', liveryColor: '#ffffff', neon: 'off', perf: [0, 0, 0, 0] };
}
export const getMods = (def, m) => ({ ...defaultMods(def), ...(m || {}), perf: [...((m && m.perf) || [0, 0, 0, 0])] });

// concrete values the model builder understands
export function resolveMods(def, m) {
  const mods = getMods(def, m);
  return {
    ...mods,
    spoilerType: mods.spoiler === 'stock' ? (def.bigWing ? 'bigwing' : def.spoiler ? 'gt' : 'none') : mods.spoiler,
    liveryType: mods.livery === 'stock' ? (def.livery ? 'sakura' : 'none') : mods.livery,
  };
}

// performance upgrades -> physics def
export function applyMods(def, m) {
  const p = getMods(def, m).perf;
  return { ...def, vmax: def.vmax * (1 + 0.03 * p[1]), t60: def.t60 / (1 + 0.07 * p[0]), grip: def.grip * (1 + 0.05 * p[2]), nitroDrain: 22 * (1 - 0.12 * p[3]) };
}

// price of moving from saved -> work
export function modCost(def, saved, work) {
  const s = getMods(def, saved), w = getMods(def, work), d = defaultMods(def);
  let c = 0;
  if (w.color !== s.color && w.color !== d.color) c += PRICE.color;
  if (w.rim !== s.rim && w.rim !== d.rim) c += PRICE.rim;
  if (w.finish !== s.finish) c += PRICE.finish[w.finish];
  if (w.spoiler !== s.spoiler) c += PRICE.spoiler[w.spoiler];
  if (w.kit !== s.kit) c += PRICE.kit[w.kit];
  if (w.livery !== s.livery) c += PRICE.livery[w.livery];
  if (w.liveryColor !== s.liveryColor && !['stock', 'none'].includes(w.livery)) c += PRICE.liveryColor;
  if (w.neon !== s.neon && w.neon !== 'off') c += PRICE.neon;
  for (let i = 0; i < 4; i++) for (let l = s.perf[i] + 1; l <= w.perf[i]; l++) c += PERF_STEP[l];
  return c;
}

// menu rows: label, how to read/write, how to display
export const ROWS = [
  { key: 'color', label: 'PAINT', kind: 'swatch', opts: PAINTS },
  { key: 'finish', label: 'FINISH', kind: 'list', opts: FINISHES },
  { key: 'rim', label: 'RIMS', kind: 'swatch', opts: RIMS },
  { key: 'spoiler', label: 'SPOILER', kind: 'list', opts: SPOILERS },
  { key: 'kit', label: 'BODY KIT', kind: 'list', opts: KITS },
  { key: 'livery', label: 'LIVERY', kind: 'list', opts: LIVERIES },
  { key: 'liveryColor', label: 'LIVERY COLOUR', kind: 'swatch', opts: LIVERY_COLORS },
  { key: 'neon', label: 'NEON', kind: 'swatch', opts: NEONS },
  ...PERF.map(([label], i) => ({ key: 'perf' + i, label, kind: 'level', idx: i })),
  { key: 'buy', label: 'BUY & EXIT', kind: 'action' },
];

// change a row's value; `floor` = saved perf levels (can't downgrade)
export function cycle(work, row, dir, saved) {
  if (row.kind === 'level') { work.perf[row.idx] = Math.max(saved.perf[row.idx], Math.min(3, work.perf[row.idx] + dir)); return; }
  if (!row.opts) return;
  const i = row.opts.indexOf(work[row.key]);
  work[row.key] = row.opts[(i + dir + row.opts.length) % row.opts.length];
}

export function displayValue(def, work, row) {
  if (row.kind === 'level') return work.perf[row.idx];
  return work[row.key];
}
