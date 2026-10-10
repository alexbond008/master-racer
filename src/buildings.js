import * as THREE from 'three';

// seeded rng so the map is stable between runs
let seed = 1337;
export const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
export const pick = a => a[Math.floor(rnd() * a.length)];


export function windowTextures() {
  const mk = lit => {
    const cv = document.createElement('canvas'); cv.width = cv.height = 256;
    const x = cv.getContext('2d');
    x.fillStyle = lit ? '#000' : '#ffffff'; x.fillRect(0, 0, 256, 256);
    if (!lit) { // brick courses
      for (let y = 0; y < 256; y += 4) { x.fillStyle = '#d9d9d9'; x.fillRect(0, y, 256, 1); for (let xx = (y / 4) % 2 ? 0 : 6; xx < 256; xx += 12) x.fillRect(xx, y, 1, 4); }
    }
    for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) {
      const on = (i * 7 + j * 13 + (i ^ j) * 3) % 7 < 2; // fixed pattern; per-face offsets vary it
      const px = i * 64 + 20, py = j * 64 + 14;
      if (lit) { if (on) { x.fillStyle = '#ffb347'; x.fillRect(px, py, 24, 34); } }
      else {
        x.fillStyle = '#f2f2f2'; x.fillRect(px - 3, py - 3, 30, 3); x.fillRect(px - 3, py + 34, 30, 4); // sill + lintel
        x.fillStyle = '#121a24'; x.fillRect(px, py, 24, 34); x.fillStyle = '#3a4656'; x.fillRect(px, py + 16, 24, 2); x.fillRect(px + 11, py, 2, 34);
      }
    }
    const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8; return t;
  };
  return { map: mk(false), emissive: mk(true) };
}

// Pushes a textured box into the geometry list.
export function box(list, cx, cz, w, d, h, color, y0 = 0, windows = true, rot = 0) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.attributes.uv, n = uv.count;
  const col = new Float32Array(n * 3);
  const c = new THREE.Color(color), roof = c.clone().multiplyScalar(0.55);
  for (let f = 0; f < 6; f++) {
    const ext = f < 2 ? d : w; // px/nx run along z; pz/nz along x
    const ox = Math.floor(rnd() * 4) / 4, oy = Math.floor(rnd() * 4) / 4;
    for (let v = 0; v < 4; v++) {
      const i = f * 4 + v;
      if (f === 2 || f === 3 || !windows) { uv.setXY(i, 0.01, 0.01); }
      else uv.setXY(i, uv.getX(i) * ext / 3.5 / 4 + ox, uv.getY(i) * h / 3.2 / 4 + oy);
      const cc = f === 2 ? roof : c;
      col[i * 3] = cc.r; col[i * 3 + 1] = cc.g; col[i * 3 + 2] = cc.b;
    }
  }
  uv.needsUpdate = true;
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  if (rot) g.rotateY(rot);
  g.translate(cx, y0 + h / 2, cz);
  list.push(g);
}


export function slabBox(cx, cz, w, d, h, y0 = 0) {
  const g = new THREE.BoxGeometry(w, h, d);
  g.translate(cx, y0 + h / 2, cz);
  g.deleteAttribute('uv');
  // merge needs uniform attributes
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2));
  return g;
}
