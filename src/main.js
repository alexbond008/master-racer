import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { CARS, CAR_ORDER, MPH } from './cars.js';
import { CarPhysics } from './car.js';
import { buildCar, updateCarModel } from './carModel.js';
import { buildWorld, DISTRICTS } from './world.js';
import { Weather, WEATHER } from './weather.js';
import { Input } from './input.js';
import { Hud } from './hud.js';
import { Traffic, KENNEY_FILES } from './traffic.js';
import { preloadKenney, preloadCarModels } from './models.js';
import { PoliceSystem } from './police.js';
import { carVsCar } from './ai.js';
import { RaceSystem, RIVALS } from './races.js';
import { loadSave, saveGame } from './progress.js';
import { GameAudio } from './audio.js';
import { showDialog, hideDialog, showGarage, hideGarage, showCustoms, hideCustoms } from './menus.js';
import { applyMods, getMods, modCost, cycle, ROWS } from './customs.js';

const $ = id => document.getElementById(id);
const canvas = $('game');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(62, 1, 0.3, 2400);
const hemi = new THREE.HemisphereLight(0x8a9bd6, 0x2a1d14, 0.75); scene.add(hemi);
const moon = new THREE.DirectionalLight(0xa9b9ff, 0.55); moon.position.set(-300, 400, 200); scene.add(moon);

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.45;
await preloadCarModels([...Object.keys(CARS), 'cruiser', 'interceptor', 'suv', 'blackcab', 'bus']);   // Blender car models (any that exist)
const netData = await (await fetch('/data/southlondon.json')).json();
// the dev server may already decode .gz (Content-Encoding), so sniff the gzip magic bytes
const gunzipJson = async url => {
  const buf = new Uint8Array(await (await fetch(url)).arrayBuffer());
  if (buf[0] === 0x1f && buf[1] === 0x8b) return new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  return JSON.parse(new TextDecoder().decode(buf));
};
const bdata = await gunzipJson('/data/buildings.json.gz');
const lmdefs = await (await fetch('/data/landmarks.json')).json();
const lmModels = {};
{ // Blender landmark models (any that exist), loaded before the world is built
  const gl = new GLTFLoader();
  await Promise.all(Object.keys(lmdefs).map(async k => { try { lmModels[k] = (await gl.loadAsync(`/models/landmarks/${k}.glb`)).scene; } catch { /* not modelled yet */ } }));
}
const world = buildWorld(scene, netData, { bdata, lmdefs, lmModels });
const weather = new Weather(scene, hemi, moon, world.groundMats, $('flash'));
weather.onThunder = () => audio.thunder();
const input = new Input();
const audio = new GameAudio();
addEventListener('keydown', () => audio.start());
addEventListener('pointerdown', () => audio.start());
audio.onRadio = i => { const el = $('radio'); el.textContent = '♪ ' + i.station + (i.track ? '  —  ' + i.track : ''); el.classList.add('show'); clearTimeout(audio._rt); audio._rt = setTimeout(() => el.classList.remove('show'), 4500); };
const hud = new Hud(world);

// ---------- composer (MSAA + bloom)
const size = new THREE.Vector2();
const rt = new THREE.WebGLRenderTarget(4, 4, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(512, 512), 0.55, 0.7, 0.88); composer.addPass(bloom);
composer.addPass(new OutputPass());
function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false); composer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

// ---------- player
const game = {
  save: loadSave(), carId: 'fiat126', phys: null, model: null, started: false, stars: 0,
  route: null, routeIdx: 0, dest: null, camMode: 0, hp: 100, cash: 0,
};
function buildPlayerModel(id, mods) {
  const def = CARS[id];
  if (game.model) { scene.remove(game.model); game.model.userData.paint?.dispose(); }
  game.model = buildCar(def, { headlights: true, player: true, mods }); scene.add(game.model);
  // nitro flames
  const fl = new THREE.Mesh(new THREE.ConeGeometry(0.22, 1.6, 8, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 1.2, 4), transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false }));
  fl.rotation.x = -Math.PI / 2; fl.visible = false;
  const fl2 = fl.clone();
  fl.position.set(-def.W * 0.28, def.gc + 0.35, -def.L / 2 - 0.8); fl2.position.set(def.W * 0.28, def.gc + 0.35, -def.L / 2 - 0.8);
  game.model.add(fl, fl2); game.flames = [fl, fl2];
}
function setCar(id) {
  game.carId = id;
  const mods = game.save.mods?.[id], def = applyMods(CARS[id], mods);
  buildPlayerModel(id, mods);
  if (!game.phys) game.phys = new CarPhysics(def); else game.phys.setDef(def);
}
if (!CARS[game.save.carId] || !game.save.owned.includes(game.save.carId)) game.save.carId = 'fiat126';
game.cash = game.save.cash;
setCar(game.save.carId);
let camTh = Math.PI; const camPos = new THREE.Vector3();
const placePlayerPose = (x, z, th) => { game.phys.place(x, z, th); camTh = th; camPos.set(x - Math.sin(th) * 9, 4, z - Math.cos(th) * 9); };
const spawn = () => placePlayerPose(world.spawn.x, world.spawn.z, world.spawn.th); // on the A23 by Lambeth Town Hall, left lane
// put the player back on the nearest road (R key), facing along it
function snapToRoad() {
  const p = game.phys, nr = world.net.nearest(p.x, p.z, 300); if (!nr) return;
  const dir = nr.tx * Math.sin(p.th) + nr.tz * Math.cos(p.th) >= 0 ? 1 : -1, e = nr.e, d = e.oneway ? 1 : dir;
  const lp = world.net.lanePoint(e, d, d === 1 ? nr.s : e.len - nr.s); placePlayerPose(lp.x, lp.z, Math.atan2(lp.tx, lp.tz));
}
spawn();
world.preload(world.spawn.x, world.spawn.z);

// ---------- traffic + police
await preloadKenney(KENNEY_FILES);
const traffic = new Traffic(scene, world, 55);
const police = new PoliceSystem(scene, world);
police.seedPatrols(game.phys, 6);
const starText = n => '★'.repeat(n);
let bannerT = 0;
function banner(text, color = '#ffb400', sub = '', secs = 2.4) {
  const b = $('banner'); b.style.color = color; b.innerHTML = text + (sub ? `<small>${sub}</small>` : ''); b.classList.add('show'); bannerT = secs;
}
function respawnPlayer() { spawn(); game.hp = 100; game.phys.nitro = 100; }
// ---------- Master Customs shop (Brixton)
const shopNr = world.net.nearest(world.places.shop[0], world.places.shop[1], 300, e => e.cls <= 2) || world.net.nearest(world.places.shop[0], world.places.shop[1], 300);
const shopPos = [shopNr.px, shopNr.pz];
{
  const g = new THREE.Group();
  const col = new THREE.Color(0.3, 1.2, 3.2);
  const ring = new THREE.Mesh(new THREE.RingGeometry(5, 7, 40), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.08; g.add(ring);
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 50, 8, 1, true), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  beam.position.y = 25; g.add(beam);
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 128; const x = cv.getContext('2d');
  x.fillStyle = 'rgba(0,0,0,.65)'; x.fillRect(0, 0, 512, 128); x.strokeStyle = '#37d4ff'; x.lineWidth = 6; x.strokeRect(3, 3, 506, 122);
  x.fillStyle = '#37d4ff'; x.font = 'bold 30px "Arial Narrow", Arial'; x.textAlign = 'center'; x.fillText('PAINT · WHEELS · NEON · TUNING', 256, 46);
  x.fillStyle = '#fff'; x.font = 'bold 46px "Arial Narrow", Arial'; x.fillText('MASTER CUSTOMS', 256, 98);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true })); label.scale.set(16, 4, 1); label.position.y = 13; label.renderOrder = 20; g.add(label);
  g.position.set(shopPos[0], 0, shopPos[1]); scene.add(g);
}
const shopAt = p => Math.hypot(p.x - shopPos[0], p.z - shopPos[1]) < 13 && p.speed < 9;
function openCustoms() {
  audio.sting('open');
  const id = game.carId, def = CARS[id], saved = getMods(def, game.save.mods?.[id]);
  menu = { type: 'customs', sel: 0, id, saved, work: getMods(def, saved), ang: 0 };
  renderCustoms();
}
function renderCustoms() { showCustoms({ def: CARS[menu.id], work: menu.work, saved: menu.saved, sel: menu.sel, cash: game.cash }); }
function closeCustoms(buy) {
  const id = menu.id, def = CARS[id];
  if (buy) {
    const cost = modCost(def, menu.saved, menu.work);
    if (cost > game.cash) { audio.sting('deny'); toast('NOT ENOUGH CASH'); return; }
    game.cash -= cost; (game.save.mods ||= {})[id] = menu.work; toast(cost ? `PURCHASED  -$${cost}` : 'NO CHANGES'); if (cost) audio.sting('buy');
  }
  hideCustoms(); menu = null; setCar(id); persist();
}

// ---------- races / pink slips
const races = new RaceSystem(scene, world);
races.refreshPins(game.save);
let menu = null; // { type:'dialog', i, wager } | { type:'garage', sel }
const persist = () => { game.save.cash = game.cash; game.save.carId = game.carId; saveGame(game.save); };
const carName = id => CARS[id].name;
function raceWager() { return game.carId !== 'fiat126' && !RIVALS[game.save.raceIdx]?.slipFree ? game.carId : null; }
const raceHooks = {
  banner: (...a) => { if (/^[123]$/.test(a[0])) audio.sting('count'); else if (a[0] === 'GO!') audio.sting('go'); banner(...a); },
  toast: t => { if (/^(CHECKPOINT|FINISH)/.test(t)) audio.sting('checkpoint'); toast(t); },
  placePlayer: (x, z, th) => { placePlayerPose(x, z, th); game.hp = 100; game.phys.nitro = 100; },
  onEnd: (result, st) => {
    const r = st.r, save = game.save;
    audio.sting(result === 'win' ? 'win' : 'lose');
    if (result === 'win') {
      if (!save.owned.includes(r.car)) save.owned.push(r.car);
      save.raceIdx = st.i + 1; game.cash += 1000 * (st.i + 1);
      setCar(r.car); save.carId = r.car;
      banner('PINK SLIP WON', '#3ddc84', `${carName(r.car)} IS YOURS  ·  +$${1000 * (st.i + 1)}`, 5);
      toast(`"${r.win}"`);
      if (save.raceIdx >= RIVALS.length) { save.finished = true; setTimeout(() => banner('KING OF SOUTH LONDON', '#ffb400', 'FROM ZAMOŚĆ TO THE TOP OF THE BLACKLIST', 8), 5200); }
    } else {
      if (st.wager) {
        save.owned = save.owned.filter(c => c !== st.wager); if (save.mods) delete save.mods[st.wager];
        banner('YOU LOST THE SLIP', '#ff3b3b', `${carName(st.wager)} GONE`, 5);
        if (game.carId === st.wager) { const best = save.owned[save.owned.length - 1] || 'fiat126'; setCar(best); save.carId = best; }
      } else { game.cash -= 500; banner('YOU LOST', '#ff3b3b', 'PAYS $500', 4); }
      toast(`"${r.lose}"`);
    }
    races.refreshPins(save); persist();
    game.route = null; hud.setRoute(null, null); setBeacon(null);
    setTimeout(() => { races.cleanup(); game.hp = 100; }, 3500);
    if (result === 'win') setTimeout(() => respawnAtPin(st.i), 3500);
  },
};
function respawnAtPin(i) { const po = races.startPose(i); placePlayerPose(po.x, po.z, po.th); }
function openDialog(i) {
  audio.sting('open');
  const info = races.routeInfo(i), r = RIVALS[i];
  menu = { type: 'dialog', i, wager: raceWager(), info };
  showDialog(i, { wager: menu.wager, len: info.len, weather: WEATHER[r.weather].label });
}
function startRace() {
  const m = menu, i = m.i, r = RIVALS[i];
  hideDialog(); menu = null;
  weather.set(r.weather);
  const st = races.begin(i, game.phys, game.phys.def, raceHooks);
  st.wager = m.wager;
  game.route = [...st.cps]; game.routeIdx = 0; game.dest = st.cps[st.cps.length - 1];
  hud.setRoute(st.line, game.dest);
  toast(WEATHER[r.weather].label);
}
function endRaceNow(result) { if (races.state && races.state.stage !== 'done') races.end(result, raceHooks); }

police.onEvent = (type, d) => {
  if (type === 'wanted') { audio.sting('wanted'); }
  if (type === 'wanted') { toast(starText(d.stars) + ' WANTED'); if (d.first) banner('SPOTTED', '#4da6ff', 'POLICE ARE AFTER YOU'); }
  else if (type === 'escaped') { audio.sting('escaped'); banner('ESCAPED', '#3ddc84', 'YOU LOST THE POLICE'); }
  else if (type === 'busted') { audio.sting('busted'); if (races.state) { endRaceNow('lose'); return; } game.cash -= 300; banner('BUSTED', '#ff3b3b', 'FINE $300'); respawnPlayer(); persist(); }
  else if (type === 'wreck') toast('UNIT DOWN');
};

// blob shadow
const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.5, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4 }));
shadow.rotation.x = -Math.PI / 2; scene.add(shadow);

// smoke
const SMOKE_N = 160, smokeGeo = new THREE.BufferGeometry();
const smokePos = new Float32Array(SMOKE_N * 3).fill(-999), smokeAge = new Float32Array(SMOKE_N).fill(9), smokeVel = new Float32Array(SMOKE_N * 3);
smokeGeo.setAttribute('position', new THREE.BufferAttribute(smokePos, 3));
const smoke = new THREE.Points(smokeGeo, new THREE.PointsMaterial({ color: 0xcfd3d8, size: 1.8, transparent: true, opacity: 0.28, depthWrite: false, sizeAttenuation: true }));
smoke.frustumCulled = false; scene.add(smoke);
let smokeI = 0;

// ---------- route
hud.onSetDest = (wx, wz) => {
  const p = game.phys;
  const r = world.routeToPoint(p.x, p.z, wx, wz);
  if (!r || r.nodes.length < 2) { toast('NO ROUTE FOUND'); return; }
  game.route = r.nodes; game.routeIdx = 0; game.dest = r.nodes[r.nodes.length - 1];
  hud.setRoute(r.poly, game.dest);
  toast('ROUTE SET');
  setBeacon(game.dest);
  hud.toggleMap(false);
};
const beacon = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 160, 16, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.2, 1.6, 2.4), transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
beacon.visible = false; scene.add(beacon);
function setBeacon(d) { beacon.visible = !!d; if (d) beacon.position.set(d[0], 80, d[1]); }
const arrow = new THREE.Mesh(new THREE.ConeGeometry(0.5, 1.3, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.3, 2.0, 3.0), transparent: true, opacity: 0.9 }));
arrow.rotation.x = Math.PI / 2; const arrowG = new THREE.Group(); arrowG.add(arrow); arrowG.visible = false; scene.add(arrowG);

function guidance(p) {
  if (!game.route) { arrowG.visible = false; return ''; }
  const r = game.route;
  while (game.routeIdx < r.length - 1 && Math.hypot(r[game.routeIdx][0] - p.x, r[game.routeIdx][1] - p.z) < 22) game.routeIdx++;
  const nxt = r[game.routeIdx];
  const dEnd = Math.hypot(game.dest[0] - p.x, game.dest[1] - p.z);
  if (dEnd < 25 && races.state) { /* race handles its own finish */ }
  else if (dEnd < 25) { toast('YOU HAVE ARRIVED'); game.route = null; hud.setRoute(null, null); setBeacon(null); arrowG.visible = false; return ''; }
  arrowG.visible = true;
  arrowG.position.set(p.x, 3.4 + Math.sin(performance.now() * 0.004) * 0.15, p.z);
  arrowG.rotation.y = Math.atan2(nxt[0] - p.x, nxt[1] - p.z);
  // turn instruction: angle between heading and next point
  let a = Math.atan2(nxt[0] - p.x, nxt[1] - p.z) - p.th; a = Math.atan2(Math.sin(a), Math.cos(a));
  const dn = Math.hypot(nxt[0] - p.x, nxt[1] - p.z);
  const dir = Math.abs(a) < 0.5 ? 'STRAIGHT ON' : a > 0 ? 'TURN LEFT' : 'TURN RIGHT';
  return `${dir} IN ${Math.round(dn)} M  ·  ${Math.round(dEnd)} M TO GO`;
}

// ---------- toast
let toastT = 0;
function toast(t) { const e = $('toast'); e.textContent = t; e.classList.add('show'); toastT = 2; }

// ---------- main loop
const STEP = 1 / 120;
let acc = 0, last = performance.now(), shake = 0;
const camTarget = new THREE.Vector3(), camDir = new THREE.Vector3();
let started = false, startAt = 0;
addEventListener('keydown', e => { if (e.code === 'Enter' && !started) { started = true; startAt = performance.now(); game.started = true; $('title').style.display = 'none'; } });

function frame(now) {
  requestAnimationFrame(frame);
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  const p = game.phys;

  input.update(dt);
  if (input.was('KeyM')) hud.toggleMap();
  if (input.was('KeyQ')) audio.nextStation();
  if (input.was('Minus')) { audio.setVolume(audio.vol - 0.1); toast('VOLUME ' + Math.round(audio.vol * 100) + '%'); }
  if (input.was('Equal')) { audio.setVolume(audio.vol + 0.1); toast('VOLUME ' + Math.round(audio.vol * 100) + '%'); }
  if (input.was('KeyX')) { game.route = null; hud.setRoute(null, null); setBeacon(null); arrowG.visible = false; }
  if (input.was('KeyC')) game.camMode = (game.camMode + 1) % 3;
  if (location.search.includes('dev') && input.was('KeyN')) { const i = (CAR_ORDER.indexOf(game.carId) + 1) % CAR_ORDER.length; setCar(CAR_ORDER[i]); toast(CARS[CAR_ORDER[i]].name); }
  // ---- menus
  const pin = started && now - startAt > 400 && !menu && !hud.bigOpen ? races.pinAt(game.phys, game.save) : -1;
  if (menu) {
    if (menu.type === 'dialog') { if (input.was('Enter')) startRace(); else if (input.was('Escape')) { hideDialog(); menu = null; } }
    else if (menu.type === 'garage') {
      if (input.was('ArrowUp')) menu.sel = (menu.sel + CAR_ORDER.length - 1) % CAR_ORDER.length;
      if (input.was('ArrowDown')) menu.sel = (menu.sel + 1) % CAR_ORDER.length;
      if (input.was('Enter')) { const id = CAR_ORDER[menu.sel]; if (game.save.owned.includes(id)) { setCar(id); game.save.carId = id; persist(); toast(CARS[id].name); } }
      if (input.was('Tab') || input.was('Escape')) { hideGarage(); menu = null; } else showGarage(game.save, menu.sel);
    }
    else if (menu.type === 'customs') {
      let changed = false;
      if (input.was('ArrowUp')) { menu.sel = (menu.sel + ROWS.length - 1) % ROWS.length; changed = true; }
      if (input.was('ArrowDown')) { menu.sel = (menu.sel + 1) % ROWS.length; changed = true; }
      const dir = (input.was('ArrowRight') ? 1 : 0) - (input.was('ArrowLeft') ? 1 : 0);
      if (dir) { const before = JSON.stringify(menu.work); cycle(menu.work, ROWS[menu.sel], dir, menu.saved); if (JSON.stringify(menu.work) !== before) { buildPlayerModel(menu.id, menu.work); } changed = true; }
      if (input.was('Enter')) closeCustoms(true);
      else if (input.was('Escape')) closeCustoms(false);
      else if (changed) renderCustoms();
    }
  } else if (started && !races.state) {
    if (input.was('Tab')) { if (police.stars > 0) toast('SHAKE THE POLICE FIRST'); else { menu = { type: 'garage', sel: Math.max(0, CAR_ORDER.indexOf(game.carId)) }; showGarage(game.save, menu.sel); } }
    else if (shopAt(game.phys) && input.was('Enter') && now - startAt > 400) { if (police.stars > 0) toast('SHAKE THE POLICE FIRST'); else openCustoms(); }
    else if (pin >= 0 && input.was('Enter')) { if (police.stars > 0) toast('SHAKE THE POLICE FIRST'); else openDialog(pin); }
  }
  if (input.was('KeyR') && !races.state) snapToRoad();
  ['clear', 'rain', 'storm', 'snow'].forEach((w, i) => { if (input.was('Digit' + (i + 1))) { weather.set(w); toast(WEATHER[w].label); } });

  const raceTick = races.update(dt, game.phys, { grip: weather.grip }, raceHooks);
  const driving = started && !hud.bigOpen && !menu && !raceTick.lock;
  if (menu && menu.type === 'customs') menu.ang += dt * 0.4;
  const ctrl = driving ? input.s : { throttle: 0, brake: 0, steer: 0, handbrake: true, nitro: false };
  acc += dt;
  while (acc >= STEP) {
    const grip = weather.grip * world.surfaceGrip(p.x, p.z);
    p.step(STEP, ctrl, grip, world.collide);
    acc -= STEP;
  }
  const wasStars = police.stars;
  // ---- AI + collisions
  const grip0 = weather.grip;
  traffic.update(dt, p, grip0, world, camera.position);
  police.update(dt, p, { grip: grip0, vis: weather.vis, playerVmax: p.def.vmax });
  const hitT = performance.now() * 0.001;
  const agents = [...traffic.cars, ...police.units];
  if (races.state) agents.push(races.state.rival);
  for (const a of agents) {
    const imp = carVsCar(p, a.phys);
    if (imp > 1.5) {
      audio.impact(imp);
      shake = Math.min(1, shake + imp * 0.04);
      const rel = Math.sqrt((a.def.mass || 1300) / (p.def.mass || 1300));
      if (a.kind === 'cop') {
        police.damage(a, Math.max(0, imp - 3) * 2.5, p, true);
        if (!a.hitAt || hitT - a.hitAt > 1.2) { a.hitAt = hitT; police.offence('copHit', p); }
        game.hp -= Math.max(0, imp - 4) * 1.3 * rel;
      } else if (a.kind === 'rival') {
        game.hp -= Math.max(0, imp - 4) * 0.9 * rel;
      } else {
        if (!a.hitAt || hitT - a.hitAt > 1.5) { a.hitAt = hitT; if (imp > 2.5) police.offence('civHit', p); }
        game.hp -= Math.max(0, imp - 4) * 1.1 * rel;
      }
    }
  }
  // AI vs AI (cops ram civilians, civilians pile up)
  for (let i = 0; i < agents.length; i++) for (let j = i + 1; j < agents.length; j++) {
    const imp = carVsCar(agents[i].phys, agents[j].phys);
    if (imp > 4) { if (agents[i].kind === 'cop') police.damage(agents[i], (imp - 4) * 1.5, p); if (agents[j].kind === 'cop') police.damage(agents[j], (imp - 4) * 1.5, p); }
  }
  void wasStars;
  if (p.lastImpact > 0) {
    audio.impact(p.lastImpact);
    shake = Math.min(1, shake + p.lastImpact * 0.05);
    if (p.lastImpact > 6) { game.hp -= (p.lastImpact - 6) * 1.6; if (police.roadblocks.some(r => Math.hypot(r.x - p.x, r.z - p.z) < 14)) police.offence('roadblock', p); }
    p.lastImpact = 0;
  }
  if (game.hp <= 0 && started && races.state) { game.hp = 1; endRaceNow('lose'); }
  else if (game.hp <= 0 && started) { game.cash -= 500; banner('WRECKED', '#ff3b3b', 'REPAIRS $500'); police.clearAll(); respawnPlayer(); }
  game.stars = police.stars;

  // ---- model
  const m = game.model;
  m.position.set(p.x, 0, p.z); m.rotation.y = p.th;
  // body roll / pitch from lateral accel (cheap)
  m.rotation.z = THREE.MathUtils.lerp(m.rotation.z, -p.yawRate * p.fwdSpeed * 0.0035, 0.1);
  updateCarModel(m, p, dt);
  shadow.position.set(p.x, 0.04, p.z); shadow.rotation.z = -p.th; shadow.scale.set(p.def.W * 1.15, p.def.L * 1.1, 1);
  game.flames.forEach(f => { f.visible = p.nitroOn; if (p.nitroOn) { f.scale.y = 0.8 + Math.random() * 0.8; } });
  if (m.userData.spots) m.userData.spots.forEach(s => { s.intensity = 90 * (weather.name === 'clear' ? 1 : 1.2); });

  // ---- smoke from sliding
  if (p.slip > 0.45 && p.speed > 5) {
    for (const off of [-1, 1]) {
      const i = smokeI++ % SMOKE_N, sn = Math.sin(p.th), cs = Math.cos(p.th);
      const rx = p.x - sn * p.def.wb * 0.5 + cs * -off * p.def.W * 0.4, rz = p.z - cs * p.def.wb * 0.5 - sn * -off * p.def.W * 0.4;
      smokePos[i * 3] = rx; smokePos[i * 3 + 1] = 0.3; smokePos[i * 3 + 2] = rz; smokeAge[i] = 0;
      smokeVel[i * 3] = p.vx * 0.2 + (Math.random() - .5); smokeVel[i * 3 + 1] = 0.8 + Math.random() * 0.8; smokeVel[i * 3 + 2] = p.vz * 0.2 + (Math.random() - .5);
    }
  }
  for (let i = 0; i < SMOKE_N; i++) {
    if (smokeAge[i] > 2) { smokePos[i * 3 + 1] = -999; continue; }
    smokeAge[i] += dt; smokePos[i * 3] += smokeVel[i * 3] * dt; smokePos[i * 3 + 1] += smokeVel[i * 3 + 1] * dt; smokePos[i * 3 + 2] += smokeVel[i * 3 + 2] * dt;
  }
  smokeGeo.attributes.position.needsUpdate = true;

  // ---- camera: chase on blend of heading and velocity angle
  const spd = p.speed;
  let velAng = spd > 4 ? Math.atan2(p.vx, p.vz) : p.th;
  const blend = Math.min(0.55, spd / 60);
  let d = velAng - p.th; d = Math.atan2(Math.sin(d), Math.cos(d));
  const wantAng = p.th + d * blend * (p.fwdSpeed > 0 ? 1 : 0);
  let da = wantAng - camTh; da = Math.atan2(Math.sin(da), Math.cos(da));
  camTh += da * Math.min(1, dt * 5.5);
  const dist = [7.2, 5.2, 0][game.camMode] + Math.min(spd * 0.02, 1.8), hgt = [2.9, 2.2, 1.15][game.camMode];
  if (game.camMode === 2) {
    camTarget.set(p.x + Math.sin(p.th) * 0.3, hgt, p.z + Math.cos(p.th) * 0.3);
    camPos.copy(camTarget);
  } else {
    camTarget.set(p.x - Math.sin(camTh) * dist, hgt, p.z - Math.cos(camTh) * dist);
    camPos.lerp(camTarget, Math.min(1, dt * 9));
  }
  camera.position.copy(camPos);
  shake = Math.max(0, shake - dt * 2.5);
  const sh = shake * 0.25 + (p.nitroOn ? 0.03 : 0);
  camera.position.x += (Math.random() - .5) * sh; camera.position.y += (Math.random() - .5) * sh;
  const lookDist = game.camMode === 2 ? 20 : 6;
  camera.lookAt(p.x + Math.sin(p.th) * lookDist * (game.camMode === 2 ? 1 : 0.5), game.camMode === 2 ? 1.15 : 1.2, p.z + Math.cos(p.th) * lookDist * (game.camMode === 2 ? 1 : 0.5));
  camera.fov += ((62 + Math.min(spd * 0.28, 16) + (p.nitroOn ? 12 : 0)) - camera.fov) * Math.min(1, dt * 4);
  camera.updateProjectionMatrix();
  m.visible = game.camMode !== 2 || (menu && menu.type === 'customs');
  if (menu && menu.type === 'customs') {
    const R = p.def.L * 2.1 + 2.2, a = menu.ang + 0.6, W = innerWidth, H = innerHeight, panel = Math.min(440, W * 0.5);
    camera.position.set(p.x + Math.sin(a) * R, 1.5 + Math.sin(menu.ang * 0.7) * 0.3, p.z + Math.cos(a) * R);
    camera.lookAt(p.x, 0.65, p.z); camera.fov = 40;
    camera.setViewOffset(W, H, -panel / 2, 0, W, H); // centre the car in the space right of the menu
    if (m.userData.spots) m.userData.spots.forEach(sp => { sp.intensity = 0; });
    m.visible = true;
  } else if (camera.view && camera.view.enabled) { camera.clearViewOffset(); camera.updateProjectionMatrix(); }

  world.update(dt, p.x, p.z);
  weather.update(dt, camera, spd);
  const guide = guidance(p);

  if (bannerT > 0) { bannerT -= dt; if (bannerT <= 0) $('banner').classList.remove('show'); }
  if (toastT > 0) { toastT -= dt; if (toastT <= 0) $('toast').classList.remove('show'); }
  hud.update(p, {
    district: DISTRICTS[world.districtAt(p.x, p.z)].name, road: world.roadNameAt(p.x, p.z), weather: weather.label, grip: weather.grip, guide, stars: game.stars, hp: game.hp, blips: [...police.blips(), ...races.blips(game.save), { x: shopPos[0], z: shopPos[1], k: 'shop' }], race: races.hud(game.phys),
    prompt: menu || races.state ? '' : pin >= 0 ? `ENTER — CHALLENGE ${RIVALS[pin].name}` : (shopAt(game.phys) ? 'ENTER — MASTER CUSTOMS' : ''), cash: game.cash,
    police: { stars: police.stars, seen: police.seen, evade: police.evadeProgress, bust: police.bustedT / 2.2 },
  });

  camera.getWorldDirection(camDir);
  audio.update(dt, {
    rpm: p.rpm, throttle: ctrl.throttle, speed: spd, slip: p.slip, braking: p.braking, nitro: p.nitroOn, gear: p.gear, carId: game.carId,
    rain: weather.cur.rain, snow: weather.cur.snow, paused: !started || !!menu || hud.bigOpen, stars: police.stars,
    units: police.units.map(u => ({ x: u.phys.x, z: u.phys.z, role: u.role })), heli: police.heli,
    cam: { x: camera.position.x, z: camera.position.z, th: Math.atan2(camDir.x, camDir.z) },
  });
  composer.render();
  input.endFrame();
}
requestAnimationFrame(frame);

// debug hook
// dev helper: drop the player onto the nearest main road at (x,z)
async function teleportTo(x, z) {
  const nr = world.net.nearest(x, z, 300, e => e.cls <= 2) || world.net.nearest(x, z, 300), lp = world.net.lanePoint(nr.e, 1, nr.s);
  placePlayerPose(lp.x, lp.z, Math.atan2(lp.tx, lp.tz)); game.phys.vx = game.phys.vz = 0; world.preload(lp.x, lp.z);
  await new Promise(r => setTimeout(r, 1500)); return nr.e.name;
}
window.__game = { teleportTo, audio, races, get menu() { return menu; }, persist, composer, bloom, traffic, police, game, world, weather, scene, camera, renderer, setCar, input, hud, start: () => { started = true; game.started = true; $('title').style.display = 'none'; } };
void MPH;
