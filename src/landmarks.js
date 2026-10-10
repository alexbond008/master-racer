import * as THREE from 'three';
import { box } from './buildings.js';

// Procedural stand-ins for real South London landmarks (see research/london.md).
// Each builder gets (group, rect, ctx) and returns { solid?, extra?, trees? } collision info.
// ctx: { bMat (window material), update: [] (per-frame callbacks) }

const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, ...o });
const glow = (color, k = 3) => new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k) });
function put(group, geo, mat, x, y, z, ry = 0) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.rotation.y = ry; group.add(m); return m; }

// textured facade box (windows) -> one mesh
function facade(group, ctx, cx, cz, w, d, h, color, y0 = 0, windows = true) {
  const list = []; box(list, cx, cz, w, d, h, color, y0, windows);
  const m = new THREE.Mesh(list[0], ctx.bMat); group.add(m); return m;
}
function sign(text, w, h, bg, fg, sub) {
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = Math.round(512 * h / w);
  const x = cv.getContext('2d'); x.fillStyle = bg; x.fillRect(0, 0, cv.width, cv.height);
  x.strokeStyle = fg; x.lineWidth = 6; x.strokeRect(5, 5, cv.width - 10, cv.height - 10);
  x.fillStyle = fg; x.textAlign = 'center'; x.textBaseline = 'middle';
  let size = 64; x.font = `bold ${size}px "Arial Narrow", Arial`;
  while (x.measureText(text).width > cv.width - 40) { size -= 4; x.font = `bold ${size}px "Arial Narrow", Arial`; }
  x.fillText(text, cv.width / 2, sub ? cv.height * 0.38 : cv.height / 2);
  if (sub) { x.font = `bold ${Math.round(size * 0.5)}px "Arial Narrow", Arial`; x.fillText(sub, cv.width / 2, cv.height * 0.72); }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshBasicMaterial({ map: t, color: new THREE.Color(1.6, 1.6, 1.6) });
}
function clockFace() {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128; const x = cv.getContext('2d');
  x.fillStyle = '#f6f0d8'; x.beginPath(); x.arc(64, 64, 62, 0, 7); x.fill(); x.strokeStyle = '#222'; x.lineWidth = 4; x.stroke();
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; x.beginPath(); x.moveTo(64 + Math.sin(a) * 50, 64 - Math.cos(a) * 50); x.lineTo(64 + Math.sin(a) * 58, 64 - Math.cos(a) * 58); x.stroke(); }
  x.lineWidth = 6; x.beginPath(); x.moveTo(64, 64); x.lineTo(64, 24); x.stroke(); x.lineWidth = 4; x.beginPath(); x.moveTo(64, 64); x.lineTo(92, 78); x.stroke();
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshBasicMaterial({ map: t, color: new THREE.Color(1.9, 1.8, 1.4) });
}
function clockTower(group, ctx, x, z, w, shaft, stone, capColor) {
  facade(group, ctx, x, z, w, w, shaft, stone);
  const stage = std('#6e6a62'); put(group, new THREE.BoxGeometry(w + 1, 6, w + 1), stage, x, shaft + 3, z);
  const face = clockFace(), fg = new THREE.PlaneGeometry(w * 0.8, w * 0.8);
  for (const [dx, dz, ry] of [[0, 1, 0], [0, -1, Math.PI], [1, 0, Math.PI / 2], [-1, 0, -Math.PI / 2]]) put(group, fg, face, x + dx * (w / 2 + 0.55), shaft + 3, z + dz * (w / 2 + 0.55), ry);
  const cap = new THREE.Mesh(new THREE.ConeGeometry((w + 1) * 0.75, 7, 4), std(capColor, { metalness: 0.4 })); cap.position.set(x, shaft + 6 + 3.5, z); cap.rotation.y = Math.PI / 4; group.add(cap);
}
const tree = (group, x, z, h = 6) => {
  put(group, new THREE.CylinderGeometry(0.25, 0.35, h * 0.4, 6), std('#3a2a1a'), x, h * 0.2, z);
  put(group, new THREE.IcosahedronGeometry(h * 0.32, 1), std('#1f4a22', { flatShading: true }), x, h * 0.62, z);
};

// ---------------- BRIXTON
export function townHall(group, r, ctx) { // Lambeth Town Hall: stone block + 41 m clock tower
  const cx = (r.x0 + r.x1) / 2;
  facade(group, ctx, cx - 3, r.z1 - 9, r.x1 - r.x0 - 8, 14, 14, '#cbc2ac');
  facade(group, ctx, cx - 3, r.z1 - 9, r.x1 - r.x0 - 14, 15, 3, '#e1d9c4', 14, false);
  clockTower(group, ctx, r.x1 - 6, r.z1 - 6, 7, 28, '#c4baa2', '#3f8f78');
  facade(group, ctx, cx, r.z0 + 8, r.x1 - r.x0 - 6, 10, 9, '#a8483a');
  return {};
}
export function academy(group, r, ctx) { // Brixton Academy: cream+green faience front, copper half-dome, bright marquee
  const cx = (r.x0 + r.x1) / 2, front = r.z1 - 5;
  facade(group, ctx, cx, r.z0 + 14, r.x1 - r.x0 - 4, 26, 19, '#6b3a2e', 0, false);
  facade(group, ctx, cx, front, r.x1 - r.x0 - 4, 10, 12, '#ece0bb');
  put(group, new THREE.BoxGeometry(r.x1 - r.x0 - 3.5, 1.2, 10.6), std('#3d8a6a'), cx, 9.2, front);
  const dome = put(group, new THREE.SphereGeometry(6.5, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), std('#4aa88c', { metalness: 0.5, roughness: 0.4 }), cx, 12, front); dome.scale.set(1, 0.8, 0.6);
  put(group, new THREE.PlaneGeometry(14, 3), sign('BRIXTON ACADEMY', 14, 3, '#150a2a', '#ff5ad0', 'LIVE TONIGHT'), cx, 6.2, front + 5.4);
  put(group, new THREE.BoxGeometry(15, 0.4, 3), glow('#ffd36b', 2.5), cx, 4.6, front + 6.2);
  return {};
}
export function plazaChurch(group, r, ctx) { // Windrush Square + St Matthew's (columned portico, tower)
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  put(group, new THREE.BoxGeometry(r.x1 - r.x0 + 6, 0.12, r.z1 - r.z0 + 6), std('#7a7870'), cx, 0.22, cz);
  facade(group, ctx, cx, cz - 6, 14, 22, 11, '#d6cfbd', 0, false);
  for (let i = 0; i < 4; i++) put(group, new THREE.CylinderGeometry(0.55, 0.6, 8, 10), std('#e8e2d2'), cx - 4.2 + i * 2.8, 4, cz + 6.4);
  put(group, new THREE.BoxGeometry(12, 1, 3), std('#e8e2d2'), cx, 8.5, cz + 6.4);
  const tri = new THREE.Shape([new THREE.Vector2(-2.4, 0), new THREE.Vector2(2.4, 0), new THREE.Vector2(0, 2.4)]);
  const pg = new THREE.ExtrudeGeometry(tri, { depth: 12, bevelEnabled: false }); pg.translate(0, 0, -6); pg.rotateY(Math.PI / 2);
  put(group, pg, std('#e8e2d2'), cx, 9, cz + 6.4);
  facade(group, ctx, cx, cz - 15, 6, 6, 22, '#cfc7b3');
  put(group, new THREE.ConeGeometry(3.8, 9, 8), std('#4a5a52'), cx, 26.5, cz - 15);
  const trees = [];
  for (let i = 0; i < 10; i++) { const tx = r.x0 + 5 + (i % 5) * 7.5, tz = r.z1 - 6 - Math.floor(i / 5) * 8; if (tz > cz + 8 || true) { tree(group, tx, tz, 6 + (i % 3)); trees.push({ x: tx, z: tz, r: 1.2 }); } }
  return { solid: { x0: cx - 8, x1: cx + 8, z0: cz - 19, z1: cz + 9 }, trees };
}
export function estate(group, r, ctx) { // Barrier Block-style brick horseshoe
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2, w = r.x1 - r.x0;
  const h = 21, brick = '#7d4a3a';
  facade(group, ctx, cx, r.z0 + 6, w - 2, 12, h, brick); facade(group, ctx, r.x0 + 6, cz + 4, 12, w - 20, h - 3, brick); facade(group, ctx, r.x1 - 6, cz + 4, 12, w - 20, h - 3, brick);
  const deck = glow('#ffcf86', 1.4);
  for (let f = 1; f < 6; f++) put(group, new THREE.BoxGeometry(w - 14, 0.18, 0.2), deck, cx, f * 3.3, r.z0 + 12.2);
  return {};
}
export function windmill(group, r, ctx) { // Ashby's Mill: 15 m brick tower, boat-shaped cap, sails
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  put(group, new THREE.BoxGeometry(r.x1 - r.x0 + 6, 0.1, r.z1 - r.z0 + 6), std('#2f5a2c', { roughness: 1 }), cx, 0.28, cz);
  put(group, new THREE.CylinderGeometry(1.9, 3.3, 15, 14), std('#8a4a34'), cx, 7.5, cz);
  const cap = put(group, new THREE.SphereGeometry(2.4, 12, 8), std('#2a2a2e'), cx, 15.4, cz); cap.scale.set(1, 0.7, 1.5);
  const sails = new THREE.Group(); sails.position.set(cx, 14.8, cz + 3.4);
  for (let i = 0; i < 4; i++) { const a = new THREE.Group(); a.rotation.z = i * Math.PI / 2; const blade = new THREE.Mesh(new THREE.BoxGeometry(1.6, 9, 0.12), std('#d8d0bc')); blade.position.y = 5.5; a.add(blade); sails.add(a); }
  group.add(sails); ctx.update.push(dt => { sails.rotation.z += dt * 0.12; });
  const trees = [{ x: cx, z: cz, r: 6 }];
  for (let i = 0; i < 8; i++) { const a = i * 0.78, tx = cx + Math.cos(a) * 15, tz = cz + Math.sin(a) * 15; tree(group, tx, tz, 6); trees.push({ x: tx, z: tz, r: 1.2 }); }
  return { park: true, trees };
}

// ---------------- PECKHAM
export function library(group, r, ctx) { // Will Alsop's inverted-L: 12 m up on angled legs, patinated copper
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2, w = r.x1 - r.x0;
  const cu = std('#3fb08f', { metalness: 0.55, roughness: 0.35 });
  put(group, new THREE.BoxGeometry(w + 2, 0.1, r.z1 - r.z0 + 2), std('#6a6962'), cx, 0.22, cz);
  put(group, new THREE.BoxGeometry(w - 4, 9, 14), cu, cx, 12 + 4.5, r.z0 + 12);                    // the long upper bar
  put(group, new THREE.BoxGeometry(11, 24, 12), cu, r.x1 - 9, 12, r.z0 + 12 + 14 - 7);            // the downstroke of the L
  put(group, new THREE.BoxGeometry(w - 6, 4, 0.3), glow('#ff9a3d', 1.5), cx, 17, r.z0 + 12 + 7.2);   // coloured glass band
  const stiltMat = std('#2b2e33', { metalness: 0.6 });
  for (let i = 0; i < 9; i++) { const sx = r.x0 + 6 + i * ((w - 12) / 8), s = put(group, new THREE.CylinderGeometry(0.22, 0.22, 13, 6), stiltMat, sx, 6, r.z0 + 8 + (i % 3) * 4); s.rotation.z = ((i * 7) % 5 - 2) * 0.09; s.rotation.x = ((i * 3) % 5 - 2) * 0.07; }
  for (let i = 0; i < 3; i++) { const p = put(group, new THREE.SphereGeometry(2.2, 12, 8), std(['#e0502a', '#f0c030', '#3a7bd5'][i]), cx - 10 + i * 10, 23, r.z0 + 12); p.scale.set(1.3, 0.8, 1); }
  return { solid: { x0: r.x1 - 15, x1: r.x1 - 3, z0: r.z0 + 10, z1: r.z0 + 28 }, extra: [] };
}
export function bussey(group, r, ctx) { // Bussey Building: yellow-brown Victorian brick factory + festoon lights
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2, w = r.x1 - r.x0;
  facade(group, ctx, cx, cz, w - 2, 22, 22, '#a38f64');
  facade(group, ctx, cx, cz, w - 6, 18, 2, '#7d6e4c', 22, false);
  const bulb = glow('#ffcf80', 2.2);
  for (let i = 0; i < 18; i++) put(group, new THREE.SphereGeometry(0.22, 6, 4), bulb, r.x0 + 3 + i * ((w - 6) / 17), 24.2, cz + 9.2 + Math.sin(i * 0.9) * 0.2);
  put(group, new THREE.PlaneGeometry(12, 2.4), sign('THE BUSSEY', 12, 2.4, '#101010', '#ffb400'), cx, 10, cz + 11.3);
  return {};
}
export function clockCorner(group, r, ctx) { // Jones & Higgins style Venetian clock tower on a corner
  clockTower(group, ctx, r.x1 - 5, r.z0 + 5, 6, 24, '#b8492f', '#3a7a68');
  return {};
}

// ---------------- STREATHAM
export function churches(group, r, ctx) { // Streatham Green: St Leonard's + English Martyrs twin spires
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  put(group, new THREE.BoxGeometry(r.x1 - r.x0 + 6, 0.12, r.z1 - r.z0 + 6), std('#2f5a2c', { roughness: 1 }), cx, 0.22, cz);
  const a = [cx - 10, cz - 4], b = [cx + 10, cz + 6];
  for (const [x, z, h, col] of [[a[0], a[1], 17, '#7f786a'], [b[0], b[1], 26, '#d1c4a4']]) {
    facade(group, ctx, x, z, 9, 20, 11, col, 0, false);
    facade(group, ctx, x, z - 11, 6, 6, h, col, 0, false);
    put(group, new THREE.ConeGeometry(3.8, h * 0.9, 8), std('#44504a'), x, h + h * 0.45, z - 11);
  }
  const trees = [];
  for (let i = 0; i < 8; i++) { const tx = r.x0 + 6 + (i % 4) * 9, tz = r.z0 + 6 + Math.floor(i / 4) * 28; tree(group, tx, tz, 7); trees.push({ x: tx, z: tz, r: 1.2 }); }
  return { park: true, solid: null, extra: [{ x0: a[0] - 5, x1: a[0] + 5, z0: a[1] - 14, z1: a[1] + 10 }, { x0: b[0] - 5, x1: b[0] + 5, z0: b[1] - 14, z1: b[1] + 10 }], trees };
}
export function theatre(group, r, ctx) { // Streatham Hill Theatre (Sprague, 1929): lavish stone block + neon blade sign
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  facade(group, ctx, cx, cz, r.x1 - r.x0 - 2, 32, 15, '#a39c88', 0, false);
  facade(group, ctx, cx, r.z1 - 4, r.x1 - r.x0 - 6, 5, 18, '#b4ad98');
  put(group, new THREE.BoxGeometry(1.2, 9, 3), glow('#ff3b6b', 2.4), cx + 12, 11, r.z1 + 0.5);
  put(group, new THREE.PlaneGeometry(16, 3), sign('THEATRE', 16, 3, '#1a0c0c', '#ffd36b', 'STREATHAM HILL'), cx, 7, r.z1 + 0.15);
  put(group, new THREE.BoxGeometry(16, 0.3, 4), glow('#ffd36b', 2), cx, 4.6, r.z1 + 1.8);
  return {};
}
export function barrelArena(group, r, ctx) { // 1931 Streatham Ice Arena: curved barrel roof
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2, w = r.x1 - r.x0 - 2;
  facade(group, ctx, cx, cz, w, 28, 7, '#cfc9b6', 0, false);
  const rg = new THREE.CylinderGeometry(11, 11, w, 24, 1, true, 0, Math.PI); rg.rotateZ(Math.PI / 2); // upper half-pipe, axis along x
  const roof = put(group, rg, std('#8fa0ac', { metalness: 0.4, roughness: 0.5, side: THREE.DoubleSide }), cx, 7, cz); roof.scale.z = 1.3;
  put(group, new THREE.PlaneGeometry(18, 3.4), sign('ICE ARENA', 18, 3.4, '#0a2b5a', '#9de3ff', 'OPEN SKATE · TONIGHT'), cx, 6, r.z1 - 0.8 + 0.2);
  return {};
}
