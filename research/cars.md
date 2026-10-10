# Free 3D car models for master-racer (Three.js)

Research date: 2026-10-10. Method: web search + page reads only. **Nothing was downloaded or executed.** Anything I could not read directly on a page is marked **UNVERIFIED**. Polygon counts and wheel structure could only be checked from page text or third-party reports, not by opening the files, so inspect each file once downloaded.

Rules applied: CC0 / CC-BY (or equivalent) only; no login-gated downloads; no editorial-only, paid or ripped models.

## 1. Bottom line

1. **Kenney Car Kit** (CC0) is the best base: 25+ consistent low-poly vehicles, wheels are separate, glTF included. It covers traffic, police, ambulance, fire truck, taxi, van and trucks. There is no bus and no double-decker.
2. **rgsdev "Free Low Poly Vehicles Pack"** (CC0) is the best second source. It has 21 vehicles with separated wheels and one material per colour, including 4 police variants, a bus, a taxi, a van and a limousine. File formats are not stated (UNVERIFIED glTF, see section 3).
3. For recognisable hero cars the only real-world models I could find that are properly licensed and loginless are **Ferrari F40** and **Nissan GTR**, both on Poly Pizza under CC-BY 3.0. Poly Pizza's no-login download is UNVERIFIED (see section 4).
4. **Sketchfab is out.** Its own docs say "Downloading models requires users to be authenticated with a Sketchfab account." (https://sketchfab.com/developers/download-api). Every Sketchfab model fails the no-login rule, even CC0 or CC-BY ones.

Hero cars with no usable free model (keep procedural): **Fiat 126p, Opel/Vauxhall Corsa, Subaru Impreza 22B/GC8, Lamborghini (Countach/Diablo/Aventador)**. The Nissan R34 is UNVERIFIED: Poly Pizza's "Nissan GTR" does not state its generation.

## 2. Candidate sources ranked

| Rank | Source | Licence (as quoted) | Formats | Size | Style / polys | Wheels separate | Paint recolourable | Login-free download |
|---|---|---|---|---|---|---|---|---|
| 1 | Kenney Car Kit 3.1 | "Creative Commons CC0" (kenney.nl); "CC0 1.0 Universal" (itch.io) | OBJ, FBX, glTF (itch.io); "Separate FBX, OBJ, and glTF models" (OpenGameArt) | 4.8 MB (OGA, kenney_car-kit_3.1.zip); 3.4 MB (itch.io); kenney.nl zip size UNVERIFIED | Low-poly, stylised. Roughly 3,100 to 5,000 vertices per vehicle (Cinevva mirror listing, third-party) | Yes. 8 separate wheel models (OGA page); third-party GLB report: body node plus four `wheel-*` nodes | Partly. Colours come from one colour atlas (16x4 swatches). Third-party report says the atlas is stored outside the GLB. UNVERIFIED, see section 7 | Yes. kenney.nl "Continue without donating"; itch.io is name-your-own-price; OGA is direct |
| 2 | rgsdev Free Low Poly Vehicles Pack | CC0 ("Licence is CC0", OGA); "Creative Commons Zero v1.0 Universal" (itch.io) | Not stated, only a zip. UNVERIFIED glTF | 1.4 MB (OGA); 1.3 MB (itch.io) | Low-poly, game ready. Triangle counts not given | Yes ("separated wheels") | Yes ("Colors are separated by material") | Yes. Direct OGA link; itch.io name-your-own-price, login only for comments |
| 3 | Kay Lousberg "City Builder Bits" cars on Poly Pizza | "Public Domain (CC0)" | FBX/GLTF | UNVERIFIED | Very low-poly, flat colour | UNVERIFIED | UNVERIFIED | Poly Pizza download button present; no-login UNVERIFIED |
| 4 | Poly Pizza, Quaternius models (Sports Car, SUV, Police Car, Taxi, Pickup, Truck, several "Car") | "Public Domain (CC0)" (Police Car page) | OBJ and GLTF (Police Car page) | UNVERIFIED | Low-poly, flat colour | UNVERIFIED | UNVERIFIED | Same as above |
| 5 | Poly Pizza, real-model CC-BY items (Ferrari F40, Nissan GTR) | "Creative Commons Attribution", CC BY 3.0 | FBX/GLTF (F40); OBJ/GLTF (GTR) | UNVERIFIED | Low-poly; counts not shown | UNVERIFIED | UNVERIFIED | Same as above |
| 6 | Quaternius Cars Pack / Public Transport Pack (quaternius.com, OGA, itch.io) | CC0 | FBX, OBJ, Blend. **No glTF** (convert in Blender) | Cars 2.6 MB (itch.io); OGA Car Pack 911 KB; OGA Public Transport 1.4 MB | Low-poly, flat colour; 8 cars, 12 public transport vehicles | Not stated | Not stated | Yes. itch.io is name-your-own-price. Cop SUV is Patreon-only on itch.io |
| 7 | OGA "Low Poly Vehicles Pack" (Daniel Quevedo) | CC0 ("Public Domain, do whatever you want") | .blend and FBX only | 590 KB + 74 KB | Very low-poly; Bus, Jeep, Pickup, Sedan, Wagon | Not stated | Yes (colour materials only) | Yes |
| 8 | itch.io Kaytomasu "Randomness A01 Turbo" | "CC0" | OBJ, FBX, GLB in the zip | 138 kB | Single simple car | Not stated | Not stated | Not stated for download; login only for comments |
| 9 | OGA "Sports Car (lowpoly)" Teh_Bucket | CC0 | OBJ only | 38 KB | 358 triangles, untextured, loosely Huracan-like | Not stated | Not stated | Yes |
| 10 | Sketchfab (any) | CC0 or CC-BY items exist | glTF/GLB | n/a | n/a | n/a | n/a | **No. Login required** (see section 1) |

### Poly Pizza as Google Poly successor
Poly Pizza (https://poly.pizza) was built to replace Google Poly ("Poly will cease operation", https://gamefromscratch.com/poly-pizza-a-replacement-to-google-poly/). Its "Poly by Google" models, e.g. https://poly.pizza/m/0-j0ksmXXtz (Police car), are **CC BY 3.0**, so they need attribution. Licences are per model. The site's other licence types (NC, ND, SA) are reported by third parties (UNVERIFIED), so check each model page.

Login: the model pages show a Download button and no login prompt, but I could not confirm that the click works without an account. A third-party API guide says an account is needed for the API key, not for the CDN file (UNVERIFIED). Test one download in a browser before committing.

## 3. Candidate details

### Kenney Car Kit
- Pages: https://kenney.nl/assets/car-kit, https://kenney-assets.itch.io/car-kit, https://opengameart.org/content/car-kit
- Direct link (kenney.nl, no login, from the "Continue without donating" button): https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip
- Direct link (OpenGameArt, 4.8 MB, v3.1): https://opengameart.org/sites/default/files/kenney_car-kit_3.1.zip
- Author: Kenney. Attribution not required; "Kenney.nl" credit is requested but "not mandatory".
- Version history: 3.1 "Fixed character colors", 3.0 "Added kart racers", 2.0 "Completely remade, added debris", 1.0 2022.
- Vehicles (25, from the Cinevva mirror, https://app.cinevva.com/game-assets/free-3d-vehicle-models; the mirror's CC0 labelling is third-party): suv, suv-luxury, sedan, sedan-sports, hatchback-sports, race, race-future, taxi, police, van, ambulance, firetruck, garbage-truck, delivery, delivery-flat, truck, truck-flat, tractor, tractor-police, tractor-shovel, 5 karts (kart-oobi, oodi, ooli, oopi, oozi). The kit also has debris pieces, 45+ files in total.
- Kenney's own Godot racing starter uses the same node convention: `body`, `wheel-front-left`, `wheel-front-right`, `wheel-back-left`, `wheel-back-right` (https://github.com/KenneyNL/Starter-Kit-Racing, MIT, assets CC0).
- Third-party experience (https://github.com/grvermeulen/H3-Teamy/pull/764): each model has a `body` node and four `wheel-*` nodes plus one colour atlas (16x4 swatches) stored outside the GLB. Kenney's police car is US black-and-white. The van is one-box. Wheels scale with height, not length. Source pin: Car Kit 3.1 is 4,814,237 bytes.
- Caveats: Kenney said in a tweet he will remake all Car Kit vehicles ("completely free, for everyone"; I could not open the tweet, only a search snippet quoted it, UNVERIFIED), so the kenney.nl zip could be newer than 3.1.
- Do not confuse with Kenney's separate Toy Car Kit and Retro Urban Kit, which also contain vehicles.

### rgsdev Free Low Poly Vehicles Pack
- Pages: https://opengameart.org/content/free-low-poly-vehicles-pack and https://rgsdev.itch.io/free-low-poly-vehicles-pack
- Direct link (1.4 MB): https://opengameart.org/sites/default/files/free_low_poly_vehicles_pack_by_rgsdev.zip
- Author: rgsdev (OpenGameArt user "rgsdev"). Credit appreciated, not required. Posted 2022-07-12. itch.io status is "In development".
- Vehicles (21): 4 police (Sedan, Sports, Muscle, SUV), 2 Muscle, Sports, Roadster, Sedan, Hatchback, Pickup, SUV, Van, Ambulance, Monster Truck, Taxi, Truck, Truck with trailer, Bus, Firetruck, Limousine.
- Formats are not stated on either page. If it ships .blend or FBX only, convert to GLB in Blender or with `gltf-transform`.
- Livery: US-style police (not described as UK).

### Poly Pizza real-world and traffic models
| Model | URL | Author | Licence | Formats | Notes |
|---|---|---|---|---|---|
| Ferrari F40 | https://poly.pizza/m/RTwim9bhNd | PuKkBuMXDD | Creative Commons Attribution (CC BY 3.0) | FBX/GLTF | "Ferrari F40 Low Poly". Wheel separation UNVERIFIED |
| DREAM FERRARI F40 (and "2.0") | https://poly.pizza/m/6-j7kD0viYB, https://poly.pizza/m/fyZs_FHzM0h | Alexander Schick | CC BY 3.0 | OBJ/GLTF | Tags include #horse, #lotus, so quality UNVERIFIED |
| Nissan GTR | https://poly.pizza/m/a_HKCtYAv2W | David Sirera | CC BY 3.0 | OBJ/GLTF | "Nissan GTR - Sport Car - Low Poly". Generation (R34 vs R35) not stated. UNVERIFIED |
| Police Car | https://poly.pizza/m/Uj7i2vlmir | Kay Lousberg | Public Domain (CC0) | FBX/GLTF | Tags: Emergency. Livery UNVERIFIED |
| Taxi | https://poly.pizza/m/u5PhZQ35XG | Kay Lousberg | Public Domain (CC0) | FBX/GLTF | |
| Police Car | https://poly.pizza/m/BwwnUrWGmV | Quaternius | Public Domain (CC0) | OBJ and GLTF | |
| Bus | https://poly.pizza/m/bsvS0E1eo4R | jeremy | Creative Commons Attribution | OBJ, GLTF | Single-decker. Uploaded 2017 |
| Police car | https://poly.pizza/m/0-j0ksmXXtz | Poly by Google | CC BY 3.0 | OBJ/GLTF | |

More Poly Pizza listings (licence per page UNVERIFIED unless shown above): Kay Lousberg Car Hatchback https://poly.pizza/m/BG0KAhmGDt, Stationwagon https://poly.pizza/m/vTTTjDoxhV; Quaternius Taxi https://poly.pizza/m/x43lOScTpN, SUV https://poly.pizza/m/xsMtZhBkxL, Pickup Truck https://poly.pizza/m/qn4grQgHm8, Sports Car https://poly.pizza/m/1mkmFkAz5v; jeremy Van https://poly.pizza/m/9hUUD2DWk1v, Police car https://poly.pizza/m/3oBDp9Z3OFH; Fire Engine (J-Toastie) https://poly.pizza/m/P4XkeNmBLj.

Poly Pizza searches I ran found no Subaru, Opel, Fiat 126p, Lamborghini or London double-decker (the Countach, Opel and double-decker searches returned unrelated items; the Subaru search returned none titled Subaru).

## 4. Real-world models requested

| Model | Best free + loginless option found | Verdict |
|---|---|---|
| Fiat 126p | Sketchfab "Fiat 126p Maluch" by NETRUNNER_pl, CC BY 4.0, 11.9k tris, three variants. https://sketchfab.com/3d-models/fiat-126p-maluch-free-907fe3ed09694c71b6b0e8b001d25d8d | **Fails login rule** (Sketchfab). Another Maluch (skfb.ly/o8RXM) is CC BY-NC-SA (not allowed). RenderHub copies are editorial-only. Keep procedural |
| Opel/Vauxhall Corsa | Only paid CGTrader/RenderHub/3dcadbrowser listings, BlenderKit asset (licence not seen, UNVERIFIED, BlenderKit also needs an account, UNVERIFIED) | None. Keep procedural (Kenney hatchback-sports is a generic stand-in) |
| Subaru Impreza 22B/GC8 | itch.io "Low Poly JDM Impressa" (designersoup) is paid ($2 min) and custom licence; Sketchfab 22B by DRIVER-FIRE licence UNVERIFIED and login-gated | None. Keep procedural |
| Nissan Skyline GT-R R34 | Poly Pizza "Nissan GTR" (CC BY 3.0), generation UNVERIFIED. Sketchfab "Low Poly Nissan Skyline GT-R R34" (CC BY, 11.2k tris) https://sketchfab.com/3d-models/low-poly-nissan-skyline-gt-r-r34-8ecbe8e4e432439fa7159d2e61f6bc9b | Poly Pizza one only if it turns out to be an R34 (open the model page preview). Sketchfab fails login rule |
| Ferrari F40 | https://poly.pizza/m/RTwim9bhNd (PuKkBuMXDD, CC BY 3.0) | Usable. Note Ferrari trademark/design rights are separate from the licence |
| Lamborghini | OGA "Sports Car (lowpoly)" by Teh_Bucket, CC0, 358 tris, OBJ only, "roughly based on a Lamborghini Huracan"; others are paid, editorial-only, or login-gated | No Countach/Diablo/Aventador. Keep procedural (or use the 358-tri Huracan-like OBJ as a placeholder) |
| Police car (UK) | None UK-liveried. Generic CC0: Kenney `police`, rgsdev (4 police), Kay Lousberg, Quaternius | Use generic and repaint (white body, blue/yellow checks need a texture) |
| Black London taxi | None. Free3D "Classic London Cab" is royalty-free/editorial and not CC; itch.io "Low poly Taxi" (whynomakethings) has no stated CC licence | Use Kenney `taxi`/rgsdev taxi and paint it black. Not a recognisable TX4 shape |
| Ford Transit / van | itch.io "Low Poly Transmit Van" (designersoup) is paid and custom licence | Use Kenney `van` (one-box) or rgsdev Van |
| London double-decker | None free and loginless (Sketchfab Routemaster is login-gated; TurboSquid is paid/editorial) | Keep procedural, or stack a Kenney/rgsdev bus visually. Real Routemaster silhouette needs custom modelling |

## 5. Recommendation

**Primary: Kenney Car Kit (CC0). Secondary: rgsdev pack (CC0).** Optional extras from Poly Pizza (F40, Nissan GTR) with CC-BY attribution.

| Need | Source and model |
|---|---|
| (a) Hero cars | F40: Poly Pizza (CC-BY 3.0). R34: Poly Pizza "Nissan GTR" only if verified as an R34. Everything else procedural (see below). Kenney `sedan-sports` / `race` can stand in as "unnamed" fast cars |
| (b) Traffic cars (3-4) | Kenney `sedan`, `suv`, `hatchback-sports`, `suv-luxury` (or rgsdev Sedan/Hatchback/SUV for a second visual set) |
| (c) Police / emergency (2-3) | Kenney `police`, `ambulance`, `firetruck` (all 3 in one pack). Alternatives: rgsdev 4 police variants |
| (d) Bus / taxi / van | Taxi: Kenney `taxi` painted black. Van: Kenney `van`. Bus: rgsdev Bus (single-decker). Double-decker: procedural |

### Hero cars that must stay procedural
- **Fiat 126p** (only candidate is login-gated on Sketchfab)
- **Opel/Vauxhall Corsa**
- **Subaru Impreza 22B/GC8**
- **Lamborghini Countach/Diablo/Aventador**
- **Nissan R34**: procedural unless the Poly Pizza "Nissan GTR" is checked and found to be an R34

That means 4 of the 6 stay procedural, 5 if the GTR isn't a Skyline, and only the F40 is a confident recognisable model.

### Honest quality tradeoff
- Kenney and rgsdev cars are generic, chunky, stylised toy-like cars. They look coherent together, and have separate wheels and clean node names. They will not read as "a Corsa" or "a 126p". A generic sedan next to a recognisable F40 will look uneven. If you want consistency, either use Kenney for everything and describe hero cars by archetype only, or make the stylised procedural hero cars and give them proper proportions (a 126p is tiny and boxy, an Impreza has the big rear wing, etc.), which will beat a mismatched asset.
- Poly Pizza CC-BY models are individually made and vary in style and quality. The F40 and GTR may not match Kenney's art style, and nothing says their wheels are separate nodes. Keep them as optional extras and check them first.
- Real-brand cars carry trademark/design-right risk beyond licence (a CC0/CC-BY dedication only covers the uploader's copyright). Avoid logos, and maybe avoid brand names in the UI.

### What to download (all small)
| # | What | URL | Licence | Size |
|---|---|---|---|---|
| 1 | Kenney Car Kit 3.1 | https://opengameart.org/sites/default/files/kenney_car-kit_3.1.zip (or kenney.nl link in section 3) | CC0 | 4.8 MB (3.4 MB per itch.io page) |
| 2 | rgsdev Free Low Poly Vehicles Pack | https://opengameart.org/sites/default/files/free_low_poly_vehicles_pack_by_rgsdev.zip | CC0 | 1.4 MB |
| 3 (opt.) | Ferrari F40 | https://poly.pizza/m/RTwim9bhNd | CC BY 3.0 | UNVERIFIED (probably under 1 MB) |
| 4 (opt.) | Nissan GTR | https://poly.pizza/m/a_HKCtYAv2W | CC BY 3.0 | UNVERIFIED |

**Total for the CC0 core: about 6.2 MB (kits 1 + 2).** Optional Poly Pizza models add an UNVERIFIED amount, likely a few MB.

## 6. Attribution text

| Asset | Required? | Text |
|---|---|---|
| Kenney Car Kit | No (CC0). "Not mandatory" credit requested | "Car Kit by Kenney (www.kenney.nl), CC0" |
| rgsdev pack | No (CC0). "Credits are appreciated" | "Free Low Poly Vehicles Pack by rgsdev, CC0" |
| Ferrari F40 | **Yes** (CC BY 3.0) | "Ferrari F40" by PuKkBuMXDD, https://poly.pizza/m/RTwim9bhNd, licensed CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/) |
| Nissan GTR | **Yes** (CC BY 3.0) | "Nissan GTR" by David Sirera, https://poly.pizza/m/a_HKCtYAv2W, licensed CC BY 3.0 |
| Any "Poly by Google" model | **Yes** (CC BY 3.0) | "<Title>" by Poly by Google, <poly.pizza URL>, licensed CC BY 3.0 |
| Kay Lousberg / Quaternius on Poly Pizza | No (CC0) | optional credit |

Put these in a Credits screen and a `CREDITS.md`.

## 7. Loading glTF in Three.js: wheels and recolouring

```js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
// loader.setMeshoptDecoder / DRACOLoader only if you compress the files

export async function loadCar(url, paintHex) {
  const gltf = await loader.loadAsync(url);
  const root = gltf.scene;

  // 1. Find wheels by node name (Kenney: wheel-front-left, wheel-front-right,
  //    wheel-back-left, wheel-back-right; rename-check for rgsdev / Poly Pizza).
  const wheels = {};
  root.traverse(o => {
    if (/^wheel/i.test(o.name)) wheels[o.name.toLowerCase()] = o;
    if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
  });
  // Log node names once to confirm: root.traverse(o => console.log(o.name, o.type));

  // 2. Wheel pivots: the wheel node's origin must be at the axle centre.
  //    Kenney wheels are separate meshes. If the pivot is off, wrap in a Group:
  const steerGroups = [];
  for (const n of ['wheel-front-left', 'wheel-front-right']) {
    const w = wheels[n];
    if (!w) continue;
    const g = new THREE.Group();
    g.position.copy(w.position);
    w.position.set(0, 0, 0);
    w.parent.add(g);
    g.add(w);          // g.rotation.y = steer; w.rotation.x += spin
    steerGroups.push(g);
  }

  // 3. Per-car paint: CLONE materials, otherwise every car shares one colour.
  root.traverse(o => {
    if (o.isMesh) o.material = o.material.clone();
  });
  return { root, wheels, steerGroups };
}

// Per frame:
// steer: group.rotation.y = steerAngle;
// spin:  wheel.rotation.x += speed * dt / wheelRadius;  // axis depends on model; check once
```

Recolouring:
- **Separate body material (rgsdev, many Poly Pizza models):** find the paint material by name, e.g. `root.traverse(o => o.isMesh && o.material.name.toLowerCase().includes('body') && o.material.color.set(hex))`. Log `material.name` first, names will differ.
- **Kenney (atlas/colormap):** UNVERIFIED how the shipped GLB handles it. A third-party game reports a single colour atlas of 16x4 swatches stored outside the GLB, so the GLB may load with a missing texture. Load `colormap.png` yourself and assign it to `material.map` (set `colorSpace = THREE.SRGBColorSpace`, `flipY = false` for GLB). Since paint is just one swatch, either (a) tint the whole material (`material.color`), which tints glass and tyres too, or (b) mask paint faces by UV region and tint only those via `material.onBeforeCompile`, or (c) split the body mesh by swatch in Blender once and keep paint as its own material. (c) is the cleanest and a one-off. The third-party game in section 3 did the equivalent (baked vertex colours, grey paint multiplied at runtime).
- Always `material.clone()` per car instance, and use `SkeletonUtils.clone()` (not `Object3D.clone()`) if any model has skins (none expected here). For many traffic cars, share geometry and use `InstancedMesh` per part, or clone the scene and share only geometry/textures.
- Scale: Kenney wheels scale with height not length (gap fore/aft on sedans reported), so do not rescale non-uniformly; scale the car root uniformly.

## 8. Not checked or unresolved
- Actual file contents (node names, tri counts, materials) of every pack: nothing was downloaded.
- Poly Pizza's no-login download (UNVERIFIED), per-model wheel separation, sizes.
- rgsdev pack file formats (UNVERIFIED glTF).
- Quaternius site link targets for downloads (pages use placeholders, so use OGA/itch.io copies).
- Google's old Poly archive: no official successor exists beyond Poly Pizza (a third party). I did not find another source of Google Poly models.
- Poly Haven, Sketchfab-alternatives like BlenderKit, Fab, CGTrader free sections were not verified for loginless CC0/CC-BY cars. Fab, BlenderKit and CGTrader generally require accounts (UNVERIFIED).
- itch.io CC0 packs seen but not read (low priority): Devil's Work.shop 3D Low Poly Car pack (CC0, FBX/OBJ/DAE, 3 cars + 2 pickups + bus), IceMaan free low poly cars (CC0, FBX), Devil's Work.shop Low Poly Police Car (264 polys, licence not seen).
