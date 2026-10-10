import * as THREE from 'three';

// seeded rng so the map is stable between runs
let seed = 1337;
export const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
export const pick = a => a[Math.floor(rnd() * a.length)];


export function windowTextures() {
  // 4x4 atlas of Victorian sash windows (cell = 3.5 m wide x 3.1 m storey). Albedo is near-white brick so vertex colours tint it.
  const N = 512, C = N / 4;
  const mk = lit => {
    const cv = document.createElement('canvas'); cv.width = cv.height = N;
    const x = cv.getContext('2d');
    x.fillStyle = lit ? '#000' : '#ffffff'; x.fillRect(0, 0, N, N);
    if (!lit) { // brick courses
      x.fillStyle = '#d4d4d4'; for (let y = 0; y < N; y += 6) { x.fillRect(0, y, N, 1); for (let xx = (y / 6) % 2 ? 0 : 9; xx < N; xx += 18) x.fillRect(xx, y, 1, 6); }
    }
    for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) {
      const on = (i * 7 + j * 13 + (i ^ j) * 3) % 7 < 2, ox = i * C, oy = j * C, wx = ox + 36, wy = oy + 18, ww = 56, wh = 78;
      if (lit) {
        if (on) { const g = x.createLinearGradient(0, wy, 0, wy + wh); g.addColorStop(0, '#ffcf80'); g.addColorStop(1, '#ff9a4a'); x.fillStyle = g; x.fillRect(wx, wy, ww, wh); x.fillStyle = '#000'; x.fillRect(wx + ww / 2 - 1, wy, 2, wh); x.fillRect(wx, wy + wh * 0.42, ww, 2); }
      } else {
        x.fillStyle = '#e7e0cf'; x.fillRect(wx - 7, wy - 14, ww + 14, 10);                 // stone lintel
        x.fillStyle = '#d6cdb6'; x.beginPath(); x.moveTo(wx - 4, wy - 4); x.quadraticCurveTo(wx + ww / 2, wy - 20, wx + ww + 4, wy - 4); x.lineTo(wx + ww + 4, wy); x.lineTo(wx - 4, wy); x.fill(); // segmental arch
        x.fillStyle = '#efe9d8'; x.fillRect(wx - 6, wy + wh, ww + 12, 7);                  // sill
        x.fillStyle = '#f4f0e4'; x.fillRect(wx - 3, wy - 3, ww + 6, wh + 6);                // frame
        x.fillStyle = '#111923'; x.fillRect(wx, wy, ww, wh);                                 // glass
        x.fillStyle = '#f4f0e4'; x.fillRect(wx + ww / 2 - 1.5, wy, 3, wh); x.fillRect(wx, wy + wh * 0.42, ww, 3);  // glazing bars
        x.fillStyle = 'rgba(120,150,190,0.25)'; x.fillRect(wx, wy, ww, wh * 0.4);            // sky reflection
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
