import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

// Kenney Car Kit (CC0, https://kenney.nl). Each model: 'body' + 'wheel-{front,back}-{left,right}' nodes, one colour atlas.
const cache = new Map();
export async function preloadKenney(names) {
  const loader = new GLTFLoader();
  await Promise.all([...new Set(names)].map(async n => {
    if (cache.has(n)) return;
    const g = await loader.loadAsync(`/models/kenney/${n}.glb`);
    cache.set(n, g.scene);
  }));
}

const tailGeo = new THREE.BoxGeometry(0.3, 0.1, 0.05);
const headMat = new THREE.MeshStandardMaterial({ color: 0xfff4d0, emissive: 0xfff0c0, emissiveIntensity: 3 });

// def.kenney = file name, def.L = real length (m) we scale to. opts.color tints only the body mesh.
export function buildKenneyCar(def, opts = {}) {
  const src = cache.get(def.kenney);
  if (!src) throw new Error('Kenney model not preloaded: ' + def.kenney);
  const inner = src.clone(true);
  const root = new THREE.Group();
  // measure length (z) / width (x) from the body + wheels
  const bb = new THREE.Box3().setFromObject(inner), size = bb.getSize(new THREE.Vector3());
  const s = def.L / size.z;
  inner.scale.setScalar(s);
  inner.position.set(-(bb.min.x + bb.max.x) / 2 * s, -bb.min.y * s, -(bb.min.z + bb.max.z) / 2 * s);
  root.add(inner);

  const wheels = [];
  inner.traverse(o => {
    if (o.name === 'body' && opts.color) {
      o.traverse(m => { if (m.isMesh) { m.material = m.material.clone(); m.material.color.set(opts.color); } });
    }
    if (o.name.startsWith('wheel-')) { o.rotation.order = 'YXZ'; wheels.push({ pivot: o, spin: o, front: o.name.startsWith('wheel-front') }); }
  });
  root.userData.wheels = wheels;
  root.userData.wheelR = 0.3 * s;           // Kenney wheels are 0.3 units in radius
  // lamps (the atlas has no emissive): small glowing boxes
  const tailMat = new THREE.MeshStandardMaterial({ color: 0x550000, emissive: 0xff0000, emissiveIntensity: 1.2 });
  root.userData.tailMat = tailMat;
  const W = size.x * s, y = size.y * s * 0.42;
  for (const sx of [-1, 1]) {
    const t = new THREE.Mesh(tailGeo, tailMat); t.position.set(sx * W * 0.36, y, -def.L / 2 - 0.02); root.add(t);
    const h = new THREE.Mesh(tailGeo, headMat); h.position.set(sx * W * 0.36, y, def.L / 2 + 0.02); root.add(h);
  }
  return root;
}
