# Master Racer

Browser street-racing game set in South London (Brixton, Peckham, Streatham), in the spirit of NFS Most Wanted (2004).
Three.js + Vite. Polish immigrant from Zamość arrives in a Fiat 126, races for pink slips, dodges the police.

## Run
```bash
npm install
npm run dev     # http://localhost:5173  (add ?reset to wipe the save, ?dev for debug keys)
```

## Features so far
Driving + nitro, weather that changes grip (rain / thunderstorm / snow), HUD + minimap + route guidance, GTA-style 1-5 star police
(patrols, pursuit AI, roadblocks, helicopter, evade/busted), 5 pink-slip races, garage + car unlocks, Master Customs (paint, rims,
spoilers, body kits, livery, neon, performance tiers), London landmarks + street furniture, civilian traffic.
Real OpenStreetMap road layout (A23 spine, Rye Lane, parks) and a fully procedural audio system: per-car engines (turbo, burble, scream), tyres, nitro, sirens, rain/thunder, impacts, plus a radio (Q) with original Boom Bap / UK Drill / Rock tracks and a chase track that builds with the wanted level.

Controls: W/S throttle-brake, A/D steer, Space handbrake, Shift nitro, M map, C camera, 1-4 weather, Tab garage, Q radio, -/= volume, Enter interact. Gamepad supported.

See `SPEC.md`, `research/`, and `CREDITS.md`.

## Credits / licences
- Kenney Car Kit (CC0) for civilian traffic models.
- Road data: © OpenStreetMap contributors (ODbL), `public/data/southlondon.json` is derived from it.

## Assets
- **World**: real OpenStreetMap roads, parks and 76k building footprints at 1:1 scale (`public/data/*`), streamed by distance.
- **Cars and landmarks**: modelled in Blender via Python (`blender/*.py`, run headless: `blender -b --python <script>`), exported to `public/models/{cars,landmarks}/*.glb`. See `blender/CONVENTIONS.md`.
- Dev helpers: `window.__game` (teleportTo, police, traffic...), `game.devCam = {x,y,z,lx,ly,lz,fov,showCar}` for a free camera.
