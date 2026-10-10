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
Work in progress: real OpenStreetMap road layout (replacing the grid) and the audio/music system.

Controls: W/S throttle-brake, A/D steer, Space handbrake, Shift nitro, M map, C camera, 1-4 weather, Tab garage, Enter interact. Gamepad supported.

See `SPEC.md`, `research/`, and `CREDITS.md`.

## Credits / licences
- Kenney Car Kit (CC0) for civilian traffic models.
- Road data: © OpenStreetMap contributors (ODbL), `public/data/southlondon.json` is derived from it.
