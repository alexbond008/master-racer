import * as THREE from 'three';
import { resolveMods } from './customs.js';
import { getCarModel } from './models.js';

// Procedural car built from extruded side profiles. Front = +z, origin at ground centre.
// opts: { color, lite (AI car: fewer meshes), headlights (player spotlights), player }
const tireMat = new THREE.MeshStandardMaterial({ color: 0x0c0c0c, roughness: 0.9 });
const glassMat = new THREE.MeshStandardMaterial({ color: 0x0a1018, roughness: 0.08, metalness: 0.9 });
const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.6 });
const headMat = new THREE.MeshStandardMaterial({ color: 0xfff4d0, emissive: 0xfff0c0, emissiveIntensity: 3 });
const wheelGeoCache = new Map();
const geoCache = new Map();

function extrudeProfile(pts, width) {
  const shape = new THREE.Shape(pts.map(([z, y]) => new THREE.Vector2(z, y)));
  const g = new THREE.ExtrudeGeometry(shape, { depth: width, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 2, curveSegments: 4 });
  g.translate(0, 0, -width / 2);
  g.rotateY(-Math.PI / 2); // shape-x -> +z
  return g;
}
function cached(key, fn) { let g = geoCache.get(key); if (!g) { g = fn(); geoCache.set(key, g); } return g; }

export function buildCar(def, opts = {}) {
  if (!opts.procedural && getCarModel(def.id)) return castAll(buildGlbCar(def, opts));
  const root = new THREE.Group();
  const mods = resolveMods(def, opts.mods);
  const paint = makePaint(opts.color || mods.color, mods.finish);
  root.userData.paint = paint;
  const { L, W, gc, noseY, hoodY, tailY, beltY, cabin: c } = def;
  const f = L / 2;

  if (def.bus) addBusBody(root, def, paint);
  else {
    const body = cached(def.id + ':body', () => extrudeProfile([
      [-f, gc], [f, gc], [f, noseY], [f - 0.35, hoodY], [c.z0 + 0.2, hoodY + 0.02],
      [c.z0, beltY], [c.z3, beltY], [-f + 0.1, tailY], [-f, tailY - 0.1],
    ], W * 0.94));
    root.add(new THREE.Mesh(body, paint));

    const cab = cached(def.id + ':cab', () => extrudeProfile([[c.z0, beltY - 0.02], [c.z1, c.roofY], [c.z2, c.roofY], [c.z3, beltY - 0.02]], W * 0.8));
    root.add(new THREE.Mesh(cab, glassMat));
    const roofG = cached(def.id + ':roof', () => extrudeProfile([[c.z1 + 0.04, c.roofY - 0.04], [c.z1 + 0.02, c.roofY + 0.02], [c.z2 - 0.02, c.roofY + 0.02], [c.z2 - 0.04, c.roofY - 0.04]], W * 0.82));
    root.add(new THREE.Mesh(roofG, paint));
  }

  // wheels
  const wheels = [];
  const wz = def.wb / 2, wx = W / 2 - 0.12 + (mods.kit === 'wide' ? 0.06 : 0);
  const rimMat = new THREE.MeshStandardMaterial({ color: new THREE.Color(mods.rim), metalness: 0.9, roughness: 0.25 });
  const wideOff = mods.kit === 'wide' ? 0.08 : 0;
  const wk = def.wheelR.toFixed(2);
  let wg = wheelGeoCache.get(wk);
  if (!wg) {
    const tire = new THREE.CylinderGeometry(def.wheelR, def.wheelR, 0.24, 20); tire.rotateZ(Math.PI / 2);
    const rim = new THREE.CylinderGeometry(def.wheelR * 0.68, def.wheelR * 0.68, 0.25, 10); rim.rotateZ(Math.PI / 2);
    const spokes = new THREE.BoxGeometry(0.26, def.wheelR * 1.2, 0.05);
    wg = { tire, rim, spokes }; wheelGeoCache.set(wk, wg);
  }
  for (const [sx, sz, front] of [[1, 1, true], [-1, 1, true], [1, -1, false], [-1, -1, false]]) {
    const pivot = new THREE.Group();
    pivot.position.set(sx * wx, def.wheelR, sz * wz);
    const spin = new THREE.Group();
    spin.add(new THREE.Mesh(wg.tire, tireMat), new THREE.Mesh(wg.rim, rimMat));
    if (!opts.lite) spin.add(new THREE.Mesh(wg.spokes, blackMat));
    pivot.add(spin); root.add(pivot);
    wheels.push({ pivot, spin, front });
  }
  root.userData.wheels = wheels;

  // lights
  const tailMat = new THREE.MeshStandardMaterial({ color: 0x550000, emissive: 0xff0000, emissiveIntensity: 1.2 });
  root.userData.tailMat = tailMat;
  const lightG = cached('lamp', () => new THREE.BoxGeometry(0.28, 0.09, 0.05));
  for (const s of [-1, 1]) {
    const t = new THREE.Mesh(lightG, tailMat); t.position.set(s * W * 0.34, tailY - 0.08, -f - 0.02); root.add(t);
    if (!opts.lite || opts.police) { const h = new THREE.Mesh(lightG, headMat); h.position.set(s * W * 0.34, noseY + 0.07, f + 0.03); root.add(h); }
  }
  if (opts.headlights) {
    for (const s of [-1, 1]) {
      const sp = new THREE.SpotLight(0xfff0d0, 90, 70, 0.5, 0.6, 1.4);
      sp.position.set(s * W * 0.3, noseY + 0.1, f);
      sp.target.position.set(s * W * 0.3, 0, f + 15);
      root.add(sp, sp.target);
      (root.userData.spots ||= []).push(sp);
    }
  }

  if (!opts.lite) { addSpoiler(root, def, mods.spoilerType, paint); addKit(root, def, mods.kit, paint); }
  if (mods.liveryType !== 'none' && !opts.lite) addLivery(root, def, mods.liveryType, mods.liveryColor);
  if (mods.neon !== 'off' && !opts.lite) addNeon(root, def, mods.neon);
  if (def.police) addPolice(root, def);

  return root;
}

function addPolice(root, def) {
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 96;
  const x = cv.getContext('2d');
  x.fillStyle = '#ffffff'; x.fillRect(0, 0, 512, 96);
  for (let i = 0; i < 16; i++) { // battenburg: two rows of alternating blue / hi-vis yellow
    x.fillStyle = i % 2 ? '#1c4bd6' : '#e8f21a'; x.fillRect(i * 32, 16, 32, 32);
    x.fillStyle = i % 2 ? '#e8f21a' : '#1c4bd6'; x.fillRect(i * 32, 48, 32, 32);
  }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.MeshBasicMaterial({ map: tex, polygonOffset: true, polygonOffsetFactor: -2 });
  const hgt = def.L * 0.8 * 96 / 512;
  for (const s of [-1, 1]) {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(def.L * 0.8, hgt), mat);
    p.position.set(s * (def.W * 0.47 + 0.055), def.beltY - 0.22, 0); p.rotation.y = s * Math.PI / 2; root.add(p);
  }
  // light bar
  const redMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 0.1, 0.1) });
  const blueMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.2, 0.4, 6) });
  const y = def.cabin.roofY + 0.1, z = (def.cabin.z1 + def.cabin.z2) / 2;
  const a = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.12, 0.2), redMat); a.position.set(-0.3, y, z);
  const b = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.12, 0.2), blueMat); b.position.set(0.3, y, z);
  const base = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.06, 0.24), blackMat); base.position.set(0, y - 0.08, z);
  root.add(base, a, b);
  root.userData.bars = { red: a, blue: b };
}

function addBusBody(root, def, paint) { // double-decker: red slab, two window bands, lit interior glow
  const { L, W, gc } = def, H = def.cabin.roofY;
  const body = new THREE.Mesh(new THREE.BoxGeometry(W, H - gc, L), paint); body.position.set(0, gc + (H - gc) / 2, 0); root.add(body);
  const glassM = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.4, 1.35, 1.0) });
  for (const y of [2.3, 3.7]) {
    const band = new THREE.Mesh(new THREE.BoxGeometry(W + 0.04, 0.8, L * 0.86), glassM); band.position.set(0, y, 0); root.add(band);
    for (let k = -4; k <= 4; k++) { const mull = new THREE.Mesh(new THREE.BoxGeometry(W + 0.08, 0.84, 0.1), paint); mull.position.set(0, y, k * L * 0.095); root.add(mull); }
  }
  const dest = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.35), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 1.6, 0.2) })); dest.position.set(0, 4.05, L / 2 + 0.01); root.add(dest);
}

export function makePaint(color, finish) {
  const c = new THREE.Color(color);
  if (finish === 'matte') return new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.85, metalness: 0.08, clearcoat: 0 });
  if (finish === 'metallic') return new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.18, metalness: 0.95, clearcoat: 1, clearcoatRoughness: 0.05 });
  if (finish === 'chrome') return new THREE.MeshPhysicalMaterial({ color: c.lerp(new THREE.Color('#dfe5ee'), 0.82), roughness: 0.04, metalness: 1, clearcoat: 1, clearcoatRoughness: 0.02 });
  return new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.28, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.08 });
}

function addSpoiler(root, def, type, paint) {
  if (type === 'none') return;
  const { W, L, tailY } = def, f = L / 2;
  const z = -f + 0.3;
  if (type === 'lip') { const m = new THREE.Mesh(new THREE.BoxGeometry(W * 0.88, 0.04, 0.16), paint); m.position.set(0, tailY + 0.03, -f + 0.12); root.add(m); return; }
  if (type === 'ducktail') { const m = new THREE.Mesh(new THREE.BoxGeometry(W * 0.9, 0.05, 0.34), paint); m.position.set(0, tailY + 0.1, -f + 0.2); m.rotation.x = -0.28; root.add(m); return; }
  const hgt = type === 'bigwing' ? 0.5 : 0.36, chord = type === 'bigwing' ? 0.42 : 0.34;
  const wing = new THREE.Mesh(new THREE.BoxGeometry(W * 0.94, 0.045, chord), paint); wing.position.set(0, tailY + hgt, z); root.add(wing);
  for (const s of [-1, 1]) {
    const strut = new THREE.Mesh(new THREE.BoxGeometry(0.04, hgt, 0.12), blackMat); strut.position.set(s * W * 0.32, tailY + hgt / 2, z); root.add(strut);
    if (type === 'bigwing') { const ep = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.2, chord + 0.06), paint); ep.position.set(s * W * 0.47, tailY + hgt + 0.06, z); root.add(ep); }
  }
}

function addKit(root, def, kit, paint) {
  if (kit === 'stock') return;
  const { W, L, gc, wb, wheelR } = def, f = L / 2;
  const dark = blackMat;
  const split = new THREE.Mesh(new THREE.BoxGeometry(W * 0.98, 0.05, 0.4), dark); split.position.set(0, gc + 0.05, f - 0.05); root.add(split);
  const diff = new THREE.Mesh(new THREE.BoxGeometry(W * 0.7, 0.1, 0.3), dark); diff.position.set(0, gc + 0.1, -f + 0.08); root.add(diff);
  for (const s of [-1, 1]) {
    const skirt = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.13, wb * 0.82), paint); skirt.position.set(s * (W * 0.47 + 0.02), gc + 0.12, 0); root.add(skirt);
    if (kit === 'wide') {
      for (const sz of [-1, 1]) {
        const fl = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, wheelR * 2 + 0.55), paint);
        fl.position.set(s * (W / 2 + 0.01), wheelR * 2 - 0.02, sz * wb / 2); root.add(fl);
      }
    }
  }
}

function addNeon(root, def, color) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128;
  const x = cv.getContext('2d'); const g = x.createRadialGradient(64, 64, 8, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,0.95)'); g.addColorStop(0.55, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(cv);
  const mat = new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(color).multiplyScalar(2.4), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -6 });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(def.W + 1.6, def.L + 1.4), mat);
  m.rotation.x = -Math.PI / 2; m.position.y = 0.06; root.add(m);
}

function liveryTexture(type, color) {
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 128;
  const x = cv.getContext('2d');
  x.clearRect(0, 0, 512, 128);
  if (type === 'stripes') { x.fillStyle = color; x.fillRect(0, 46, 512, 14); x.fillStyle = '#ffffff'; x.fillRect(0, 66, 512, 6); }
  else if (type === 'checker') { for (let i = 0; i < 32; i++) for (let j = 0; j < 4; j++) { x.fillStyle = (i + j) % 2 ? color : '#ffffff'; x.fillRect(i * 16, 40 + j * 12, 16, 12); } }
  else if (type === 'flames') {
    x.fillStyle = color;
    for (let k = 0; k < 6; k++) { // flame tongues streaming back from the front (left)
      const y0 = 40 + k * 10; x.beginPath(); x.moveTo(0, y0 + 10); x.quadraticCurveTo(120, y0 - 6, 230 + k * 26, y0 + 12); x.quadraticCurveTo(120, y0 + 18, 0, y0 + 22); x.fill();
    }
    x.fillStyle = '#fff3'; x.fillRect(0, 62, 150, 4);
  }
  else if (type === 'roundel') { x.fillStyle = '#fff'; x.beginPath(); x.arc(256, 70, 40, 0, 7); x.fill(); x.fillStyle = color; x.beginPath(); x.arc(256, 70, 31, 0, 7); x.fill(); x.fillStyle = '#fff'; x.font = 'bold 44px Impact, sans-serif'; x.textAlign = 'center'; x.fillText('07', 256, 85); x.fillStyle = color; x.fillRect(0, 62, 190, 6); x.fillRect(322, 62, 190, 6); }
  else if (type === 'sakura') {
    x.fillStyle = '#ffffff'; x.fillRect(0, 50, 512, 10); x.fillStyle = '#31e0ff'; x.fillRect(0, 64, 512, 5);
    x.beginPath(); x.arc(380, 64, 38, 0, 7); x.fill(); x.fillStyle = '#d4003c'; x.beginPath(); x.arc(380, 64, 28, 0, 7); x.fill();
    x.fillStyle = '#111'; x.font = 'bold 26px sans-serif'; x.fillText('MASTER RACER', 70, 40);
    x.fillStyle = '#ffd1e6'; for (let i = 0; i < 14; i++) { x.beginPath(); x.arc(40 + (i * 53) % 330, 85 + ((i * 29) % 30), 5, 0, 7); x.fill(); }
  }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.wrapS = THREE.RepeatWrapping; return tex;
}

function addLivery(root, def, type, color) {
  const directional = type === 'flames';
  for (const s of [-1, 1]) {
    const tex = liveryTexture(type, color);
    if (directional && s === -1) { tex.repeat.x = -1; tex.offset.x = 1; } // keep the flames at the car's front on both flanks
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 });
    const p = new THREE.Mesh(new THREE.PlaneGeometry(def.L * 0.7, def.L * 0.7 * 0.25), mat);
    p.position.set(s * (def.W * 0.47 + 0.055), def.beltY - 0.28, -0.1); p.rotation.y = s * Math.PI / 2; root.add(p);
  }
  if (type === 'stripes' || type === 'checker' || type === 'sakura' || type === 'roundel') {
    const hood = new THREE.Mesh(new THREE.PlaneGeometry(type === 'roundel' ? 0.0001 : 0.5, def.L * 0.5), new THREE.MeshBasicMaterial({ color: type === 'sakura' ? 0xffffff : new THREE.Color(color), transparent: true, opacity: 0.92, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
    hood.rotation.x = -Math.PI / 2; hood.position.set(0, def.hoodY + 0.075, def.L * 0.18); root.add(hood);
  }
}

const castAll = r => { r.traverse(o => { if (o.isMesh && !(o.material && o.material.transparent)) { o.castShadow = true; o.receiveShadow = true; } }); return r; };

// call every frame
export function updateCarModel(model, phys, dt, time = performance.now() * 0.001) {
  for (const wh of model.userData.wheels) {
    wh.spin.rotation.x += phys.fwdSpeed * dt / (model.userData.wheelR || phys.def.wheelR);
    if (wh.front) wh.pivot.rotation.y = -phys.steerVis;
  }
  if (model.userData.tailMat) model.userData.tailMat.emissiveIntensity = phys.braking ? 6 : 1.2;
  const bars = model.userData.bars;
  if (bars) { const on = Math.floor(time * 7) % 2 === 0; bars.red.visible = on; bars.blue.visible = !on; }
}


// ---------------- Blender-made car (GLB): recolourable Paint/Rim, spinning + steering wheels, flashing police bars
function buildGlbCar(def, opts) {
  const src = getCarModel(def.id), inner = src.clone(true), root = new THREE.Group(), mods = resolveMods(def, opts.mods);
  const bb = new THREE.Box3().setFromObject(inner), size = bb.getSize(new THREE.Vector3()), s = def.L / size.z;
  inner.scale.setScalar(s); inner.position.set(-(bb.min.x + bb.max.x) / 2 * s, -bb.min.y * s, -(bb.min.z + bb.max.z) / 2 * s);
  root.add(inner); root.updateMatrixWorld(true);
  const paint = makePaint(opts.color || mods.color, mods.finish), wheels = [], H = size.y * s, W = size.x * s, L = def.L;
  const mats = new Map(), inst = m => { if (!mats.has(m)) mats.set(m, m.clone()); return mats.get(m); };
  let tail = null, rimR = 0.32;
  inner.traverse(o => {
    if (o.isMesh) {
      const list = Array.isArray(o.material) ? o.material : [o.material];
      const out = list.map(m => {
        if (m.name === 'Paint') return paint;
        if (m.name === 'Rim') { const r = inst(m); r.color.set(mods.rim); return r; }
        if (m.name === 'TailLight') { tail = inst(m); return tail; }
        if (m.name === 'Glass' || m.name === 'GlassClear') { const g = inst(m); if (g.opacity < 0.99) { g.transparent = true; g.depthWrite = false; } return g; }
        return m;
      });
      o.material = Array.isArray(o.material) ? out : out[0];
    }
    if (/^wheel_(fl|fr|rl|rr)$/.test(o.name)) {
      o.rotation.order = 'YXZ';
      const wb = new THREE.Box3().setFromObject(o); rimR = (wb.max.y - wb.min.y) / 2;
      wheels.push({ pivot: o, spin: o, front: o.name.startsWith('wheel_f') });
    }
    if (o.name === 'lightbar_red' || o.name === 'lightbar_blue') (root.userData.bars ||= {})[o.name === 'lightbar_red' ? 'red' : 'blue'] = o;
    if (o.name === 'spoiler') root.userData.glbSpoiler = o;
  });
  root.userData.wheels = wheels; root.userData.wheelR = rimR;           // already in world units (inner scale applied via setFromObject)
  root.userData.paint = paint; root.userData.tailMat = tail;
  // dims for decals / body kits / neon on a model whose proportions differ from the procedural profile
  const dims = { ...def, L, W, beltY: H * 0.6, hoodY: H * 0.52, tailY: H * 0.62, noseY: H * 0.38, gc: 0.12 };
  if (!opts.lite) {
    if (mods.spoilerType === 'none' && root.userData.glbSpoiler) root.userData.glbSpoiler.visible = false;
    else if (mods.spoiler !== 'stock') { if (root.userData.glbSpoiler) root.userData.glbSpoiler.visible = false; addSpoiler(root, dims, mods.spoilerType, paint); }
    addKit(root, dims, mods.kit, paint);
    if (mods.liveryType !== 'none' && !def.police) addLivery(root, dims, mods.liveryType, mods.liveryColor);
    if (mods.neon !== 'off') addNeon(root, dims, mods.neon);
  }
  if (opts.headlights) {
    for (const sx of [-1, 1]) {
      const sp = new THREE.SpotLight(0xfff0d0, 90, 70, 0.5, 0.6, 1.4);
      sp.position.set(sx * W * 0.3, H * 0.38, L / 2); sp.target.position.set(sx * W * 0.3, 0, L / 2 + 15);
      root.add(sp, sp.target); (root.userData.spots ||= []).push(sp);
    }
  }
  return root;
}
