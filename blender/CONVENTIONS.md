# Blender → game conventions (read before modelling)

Tool: `/opt/homebrew/bin/blender -b --python your_script.py` (Blender 5.2, headless; Python `bpy`). Write scripts into
`~/Projects/master-racer/blender/` (one script per model, re-runnable, idempotent: start from an empty scene).
Output GLB (binary glTF) into `~/Projects/master-racer/public/models/{cars|landmarks}/<id>.glb`.
Do NOT download assets, textures or models. Everything is built procedurally in the script.

## Units & axes
- 1 Blender unit = 1 metre, REAL-WORLD SIZE. Blender is Z-up. The game is Three.js (Y-up).
- Export with `bpy.ops.export_scene.gltf(filepath=..., export_format='GLB', export_apply=True, export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False)`.
- **Front of the model faces -Y in Blender** (the side you see in Blender's Front numpad-1 view). After export this is +Z in Three.js, which is the game's "forward".
- Origin = centre of the footprint at ground level (Z=0 is the ground; nothing below it). Cars: origin on the ground, midway between front and rear axles, centred left/right.

## Look
- Smooth shading on curved bodies (shade auto-smooth / use Subdivision Surface then apply), crisp edges on architecture (bevel small edges 2-5 cm for light catching).
- Materials: Principled BSDF with plain colours only (no image textures). Use real PBR values (roughness/metallic). Use **Emission** (strength ~3-6) for anything that glows at night (lit windows, signs, lamps, lights).
- Keep it light: **cars <= 25k triangles, landmarks <= 60k triangles**. Merge static pieces per material where easy, but keep the named separate objects listed below.
- The scene is a dusk/night city with bloom: emissive windows/signs read very well. Do not rely on lighting in Blender to look good; check with the preview renders below.

## Verify visually (required)
Render previews with Eevee or Cycles (few samples) from at least 4 cameras (front-3/4, rear-3/4, side, top-ish) to
`~/Projects/master-racer/blender/previews/<id>_*.png` and LOOK at them (Read tool shows images). Compare against what the real
thing looks like and iterate until it is clearly recognisable, not a box. Also confirm the exported GLB re-imports and its
bounding box matches the real dimensions (print it).

## CARS: required object / material names
Objects: `body` (paint panels, bumpers, sills), `glass` (windows), `wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr`
(each wheel = tyre+rim+brake disc as ONE object whose ORIGIN is the hub centre, so rotating about its local X axis spins it; front wheels must be
steerable about the vertical axis through the hub), optional extras `spoiler`, `lights`, `trim`, `interior`, `mirrors`.
Materials (exact names): `Paint` (default colour of the real car, glossy: roughness 0.25, metallic 0.5), `Glass` (dark tinted, roughness 0.05),
`Tyre`, `Rim`, `Chrome`, `Trim` (black plastic), `Interior`, `HeadLight` (emissive white-warm), `TailLight` (emissive red), `Plate`.
Only the `Paint` material gets recoloured in game, so put EVERY painted panel on `Paint` and nothing else.

## LANDMARKS
One object per material is fine. Front façade (the side facing the street) faces -Y. Real size. Give lit windows/signs/lamps an
Emission material (`Emit_Window`, `Emit_Sign`, ...). Put the real signage text on signs as geometry (text objects converted to mesh) where it helps recognition.
Origin at the centre of the footprint on the ground. Also write `<id>.json` next to the GLB: {"footprint":[width_x, depth_y], "height": H, "notes": "..."}.
