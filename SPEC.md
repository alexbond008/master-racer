# Master Racer — Vertical Slice Spec

Locked via Q&A 2026-10-10.

## Stack
- Browser, Three.js + Vite, vanilla JS (ES modules). Run: `npm run dev`.
- Lives on internal disk (`~/Projects/master-racer`); exFAT Seagate can't hold node_modules symlinks.

## Slice scope
- Open world: Brixton / Peckham / Streatham chunk (procedural roads + buildings from London references, CC0 props).
- Cars (6): Fiat 126 (start) -> Opel Corsa -> Subaru Impreza -> Nissan GT-R -> Ferrari F40 -> JDM Lamborghini (livery, final).
- 5 races. Each race = pink slip. Win -> take the opponent's car (unlocks next car). Lose -> lose the car you raced.
  Safety: never lose your last car; Fiat 126 can't be wagered.
- Nitro on all cars.
- Police: GTA-style 1-5 stars. Heat rises on offences, police escalate (cruisers -> interceptors -> roadblocks -> SWAT/heli stand-in), evade by breaking line of sight + cooldown.
- Garage: Los Santos Customs style (paint, wheels, spoiler, bodykit, neon, livery, perf upgrades) before a race.
- Weather: clear, rain, lightning, snow. Grip + braking distance depend on surface/weather.
- HUD: speedometer, nitro bar, minimap, stars, route guidance (set route in menu, drawn on minimap + in-world).
- Music: original procedural Web Audio — 2000s boom-bap, UK drill, rock, chase tension. In-game radio.
- Controls: keyboard + gamepad.
- Tone: NFS Most Wanted 2004 "bad man" attitude. Rival blacklist-style roster.

## Story
Polish immigrant from Zamosc drives to South London in his Maluch to become London's greatest underground street racer.

## Out of scope for slice
Punto, Octavia, Golf, Evo, mobile touch, multiplayer, vocals.
