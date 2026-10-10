import * as THREE from 'three';

// Weather drives: sky/fog/light mood, precipitation, road wetness and TYRE GRIP (=> stopping distance).
export const WEATHER = {
  clear: { vis: 1, label: 'CLEAR',     grip: 1.0,  fog: 0.0042, horizon: '#ff7a3d', top: '#101a3a', fogCol: '#3a2a3c', hemi: 0.75, rain: 0,   snow: 0,   rough: 0.82, wet: 0,   groundTint: '#ffffff' },
  rain:  { vis: 0.8, label: 'RAIN',      grip: 0.72, fog: 0.0075, horizon: '#566274', top: '#1c2230', fogCol: '#2b3340', hemi: 0.6,  rain: 1,   snow: 0,   rough: 0.28, wet: 1,   groundTint: '#c9d2e0' },
  storm: { vis: 0.6, label: 'THUNDERSTORM', grip: 0.6, fog: 0.0105, horizon: '#2e3644', top: '#0b0e16', fogCol: '#1b212c', hemi: 0.5, rain: 1,   snow: 0,   rough: 0.18, wet: 1.2, groundTint: '#b0bccf', lightning: true },
  snow:  { vis: 0.65, label: 'SNOW',      grip: 0.38, fog: 0.0095, horizon: '#a8b4c6', top: '#3a4658', fogCol: '#8d98a8', hemi: 1.0,  rain: 0,   snow: 1,   rough: 0.7,  wet: 0.2, groundTint: '#ffffff', whiteGround: true },
};

const RAIN_N = 6000, SNOW_N = 4000, BOX = 70, TOP = 38;

export class Weather {
  constructor(scene, hemi, moon, groundMats, flashEl) {
    this.scene = scene; this.hemi = hemi; this.moon = moon; this.groundMats = Array.isArray(groundMats) ? groundMats : [groundMats]; this.flashEl = flashEl;
    this.name = 'clear'; this.k = { ...WEATHER.clear, grip: 1 };
    this.cur = {
      grip: 1, vis: 1, fog: WEATHER.clear.fog, hemi: 0.75, rain: 0, snow: 0, rough: 0.82, wet: 0,
      horizon: new THREE.Color(WEATHER.clear.horizon), top: new THREE.Color(WEATHER.clear.top), fogCol: new THREE.Color(WEATHER.clear.fogCol), tint: new THREE.Color('#ffffff'), snowCover: 0,
    };
    this.flash = 0; this.nextBolt = 6; this.boltStage = 0;
    this.onThunder = null;

    scene.fog = new THREE.FogExp2(this.cur.fogCol.clone(), this.cur.fog);
    // sky dome
    this.skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: { top: { value: this.cur.top.clone() }, horizon: { value: this.cur.horizon.clone() }, flash: { value: 0 } },
      vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
      fragmentShader: 'uniform vec3 top; uniform vec3 horizon; uniform float flash; varying vec3 vP; void main(){ float h = clamp(vP.y,0.,1.); vec3 c = mix(horizon, top, pow(h,0.55)); c += vec3(0.55,0.65,0.9)*flash*(1.-h*0.5); gl_FragColor = vec4(c,1.); }',
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1800, 24, 16), this.skyMat);
    this.sky.renderOrder = -10; this.sky.frustumCulled = false;
    scene.add(this.sky);

    // rain
    const rp = new Float32Array(RAIN_N * 6), rw = new Float32Array(RAIN_N * 3);
    for (let i = 0; i < RAIN_N; i++) { rw[i * 3] = (Math.random() - .5) * BOX; rw[i * 3 + 1] = Math.random() * TOP; rw[i * 3 + 2] = (Math.random() - .5) * BOX; }
    this.rainW = rw;
    const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.BufferAttribute(rp, 3).setUsage(THREE.DynamicDrawUsage));
    this.rain = new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: 0xb8c8e0, transparent: true, opacity: 0.42, fog: false, depthWrite: false }));
    this.rain.frustumCulled = false; this.rain.visible = false; scene.add(this.rain);

    // snow
    const sp = new Float32Array(SNOW_N * 3), sw = new Float32Array(SNOW_N * 3);
    for (let i = 0; i < SNOW_N; i++) { sw[i * 3] = (Math.random() - .5) * BOX; sw[i * 3 + 1] = Math.random() * TOP; sw[i * 3 + 2] = (Math.random() - .5) * BOX; }
    this.snowW = sw;
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(sp, 3).setUsage(THREE.DynamicDrawUsage));
    this.snow = new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xffffff, size: 0.22, transparent: true, opacity: 0.9, depthWrite: false, sizeAttenuation: true }));
    this.snow.frustumCulled = false; this.snow.visible = false; scene.add(this.snow);
  }

  set(name) { if (WEATHER[name]) { this.name = name; this.k = WEATHER[name]; } }
  get grip() { return this.cur.grip; }
  get vis() { return this.cur.vis; }
  get label() { return this.k.label; }

  update(dt, cam, speed) {
    const k = this.k, c = this.cur, a = Math.min(1, dt * 0.9);
    c.grip += (k.grip - c.grip) * a; c.vis += (k.vis - c.vis) * a; c.fog += (k.fog - c.fog) * a; c.hemi += (k.hemi - c.hemi) * a;
    c.rain += (k.rain - c.rain) * a; c.snow += (k.snow - c.snow) * a; c.rough += (k.rough - c.rough) * a; c.wet += (k.wet - c.wet) * a;
    c.horizon.lerp(new THREE.Color(k.horizon), a); c.top.lerp(new THREE.Color(k.top), a); c.fogCol.lerp(new THREE.Color(k.fogCol), a);
    c.tint.lerp(new THREE.Color(k.groundTint), a);
    c.snowCover += ((k.whiteGround ? 1 : 0) - c.snowCover) * Math.min(1, dt * 0.25);

    this.scene.fog.color.copy(c.fogCol); this.scene.fog.density = c.fog;
    this.hemi.intensity = c.hemi + this.flash * 3;
    this.moon.intensity = 0.55 + this.flash * 4;
    this.skyMat.uniforms.top.value.copy(c.top); this.skyMat.uniforms.horizon.value.copy(c.horizon); this.skyMat.uniforms.flash.value = this.flash;
    this.sky.position.copy(cam.position);

    // road surface: wet = shiny + darker; snow = white
    for (const m of this.groundMats) {
      m.roughness = Math.min(1, c.rough + (m.userData.rough0 ?? 0));
      m.color.copy(c.tint).lerp(new THREE.Color('#e8eef5'), c.snowCover * 0.8).multiplyScalar(1 - c.wet * 0.25 * (1 - c.snowCover));
      m.metalness = Math.min(0.35, c.wet * 0.3);
    }

    // precipitation
    const camx = cam.position.x, camz = cam.position.z, camy = Math.max(0, cam.position.y - 6);
    this.rain.visible = c.rain > 0.02;
    if (this.rain.visible) {
      const pos = this.rain.geometry.attributes.position.array, w = this.rainW;
      const n = Math.floor(RAIN_N * Math.min(1, c.rain));
      const fall = 42, len = 0.9 + speed * 0.02;
      for (let i = 0; i < RAIN_N; i++) {
        if (i >= n) { pos[i * 6] = pos[i * 6 + 3] = 0; pos[i * 6 + 1] = pos[i * 6 + 4] = -999; continue; }
        w[i * 3 + 1] -= fall * dt; if (w[i * 3 + 1] < 0) w[i * 3 + 1] += TOP;
        const x = ((w[i * 3] - camx) % BOX + BOX * 1.5) % BOX - BOX / 2 + camx;
        const z = ((w[i * 3 + 2] - camz) % BOX + BOX * 1.5) % BOX - BOX / 2 + camz;
        const y = w[i * 3 + 1] + camy * 0;
        pos[i * 6] = x; pos[i * 6 + 1] = y; pos[i * 6 + 2] = z; pos[i * 6 + 3] = x; pos[i * 6 + 4] = y + len; pos[i * 6 + 5] = z;
      }
      this.rain.geometry.attributes.position.needsUpdate = true;
    }
    this.snow.visible = c.snow > 0.02;
    if (this.snow.visible) {
      const pos = this.snow.geometry.attributes.position.array, w = this.snowW, t = performance.now() * 0.001;
      const n = Math.floor(SNOW_N * Math.min(1, c.snow));
      for (let i = 0; i < SNOW_N; i++) {
        if (i >= n) { pos[i * 3 + 1] = -999; continue; }
        w[i * 3 + 1] -= (1.4 + (i % 5) * 0.25) * dt; if (w[i * 3 + 1] < 0) w[i * 3 + 1] += TOP;
        const sway = Math.sin(t * 0.9 + i) * 0.6;
        pos[i * 3] = ((w[i * 3] - camx) % BOX + BOX * 1.5) % BOX - BOX / 2 + camx + sway;
        pos[i * 3 + 1] = w[i * 3 + 1];
        pos[i * 3 + 2] = ((w[i * 3 + 2] - camz) % BOX + BOX * 1.5) % BOX - BOX / 2 + camz + Math.cos(t * 0.7 + i * 1.3) * 0.6;
      }
      this.snow.geometry.attributes.position.needsUpdate = true;
    }

    // lightning: double-flash then thunder
    if (k.lightning) {
      this.nextBolt -= dt;
      if (this.nextBolt <= 0) { this.flash = 1; this.boltStage = 1; this.nextBolt = 5 + Math.random() * 9; this._thunderIn = 0.3 + Math.random() * 2.2; }
    }
    if (this._thunderIn != null) { this._thunderIn -= dt; if (this._thunderIn <= 0) { this._thunderIn = null; this.onThunder?.(); } }
    if (this.flash > 0) {
      this.flash = Math.max(0, this.flash - dt * (this.boltStage === 1 ? 3.2 : 2.4));
      if (this.boltStage === 1 && this.flash < 0.12) { this.flash = 0.9; this.boltStage = 2; }
    }
    if (this.flashEl) this.flashEl.style.opacity = (this.flash * 0.35).toFixed(3);
  }
}
