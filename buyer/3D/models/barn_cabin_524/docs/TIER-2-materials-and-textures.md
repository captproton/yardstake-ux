# Tier 2 — Materials and textures

**Goal.** Replace flat PBR colours with real, tiling materials at a controlled
texel density, compressed for the web, and swappable at runtime so the
configurator's finishes picker has something to pick.

**Status: DONE bar one optimisation.** The exterior half merged in [#57](https://github.com/captproton/yardstake-ux/pull/57);
interior materials and the configurator hooks merged in [#58](https://github.com/captproton/yardstake-ux/pull/58). UVs, seven textures, neutral
albedos, size budgets, the reveal materials and the variants manifest are all
shipped and gated — 5/5 in `verify_tier2.py`, 4/4 in `finish_adu.py`.
**Remaining: KTX2 compression only**, and that is an optimisation rather than a
necessity — `lod0` is 419 KB against a 4 MB ceiling.

**Owner:** us — as are Tiers 1 and 3. The placement developer's scope is
placement only, and that is the sole external interface — see
[The one handoff](README.md#the-one-handoff--to-the-placement-developer).
Tier 1 is complete, so nothing here is blocked; we set the pace.

**Do not break the handoff.** `lod2` is the placement developer's model. This
already bit once: texturing took it from 17 KB to 239 KB, past its ceiling. It
now ships flat-shaded at **28.4 KB**, and the budgets are gated in
`finish_adu.py` rather than left to inspection. (It sat at 24.1 KB through
eleven PRs; [#70](https://github.com/captproton/yardstake-ux/pull/70) replaced the wrong-variant slab with the crawlspace
stemwall — see the handoff section of the [plan](README.md).)

**Does not depend on:** Tier 3.

---

## 1. Where things stand

`spec.yaml → materials.library` defines **13 materials**. Every mesh is
unwrapped, and seven carry maps:

```
TEXTURED   siding  shingle_gable  roof  concrete       <- exterior
           floor_oak  slate_bath  carpet_loft          <- interior
FLAT       trim  glass  post  soffit  fir_ladder  drywall
```

`drywall` is deliberately flat. Painted gypsum has no pattern to carry at any
texel density this model will ever be viewed at, and a map for it would be
several hundred KB of noise.

Six of the seven albedos are **neutral** — they carry luminance only, with
colour supplied by `baseColorFactor`. That is what makes the configurator's 14
options free (§6). `concrete` is the exception: it is not a configurable
surface, so it keeps its colour in the map.

Their **hue** was sampled from verified video frames (6:56 and 7:50) and the
transcript. Their **luminance was not measured** and is set to plausible
albedo — see `materials.provenance` and §8, which the neutral-albedo change
makes cheaper to revisit than it was, since a level correction is now a factor
edit rather than a re-bake.

`lod0` was 29 KB before texturing and is **419.1 KB** now — see §5.

## 2. Texel density — DECIDED: 128 px/ft

Everything downstream depends on one number, and it belongs in `spec.yaml`, not
in a script.

**128 px/ft (≈420 px/m), uniform across the model.** Fixed in
`spec.texturing`.

Rationale: the tightest detail that must read crisply is the 6" lap siding
exposure. At 128 px/ft that's 64 px per course — comfortably sharp at the 2–6 ft
viewing distance a walkthrough implies, and still legible at configurator
orbit distance. A 22 ft wall maps to ~2816 px, so a 4K tile covers the longest
wall without repeating visibly.

As it stands in the spec:

```yaml
texturing:
  texel_density_px_per_ft: 128
  projection: cube            # all geometry here is box-like
  tile_size_px: 1024          # per-material tile, repeated
  uv_channel: 0
```

**Verification gate:** implemented in `verify_tier2.py`. Result on the shipped
model: **3290 of 3290 edges at exactly 128.0 px/ft, 0.0% off.**

## 3. UV generation — DONE

The geometry is box-like, so cube projection is close to free — but three
details will bite:

**Unwrap after the booleans, never before.** Wall meshes are boolean results.
Openings introduce new faces that no pre-boolean UV layout accounts for.
Generate UVs as the last step in `build_adu.py`, after `difference()`.

**Do NOT project on world axes.** This was the original recommendation here and
it is wrong: a world-axis projection foreshortens any sloped face, and the 9:12
roof came out ~20% stretched against the walls. See the projection note below
for what shipped instead.

**Openings produce seams at the reveals — RESOLVED.** The jamb, head and sill
faces want `trim`, not `siding`, which meant per-face material assignment on
wall meshes. Done in Tier 1 while the openings were being detailed anyway,
which was far cheaper than retrofitting.

It did not work first time. `materials.clear()` resets every polygon's
`material_index` to 0, so the tagging was silently discarded and every wall
exported as a single siding primitive. Only checking the exported bytes caught
it. Now gated in `verify_tier2.py`.

**On the projection.** A naive world-axis cube projection foreshortens sloped
faces — the 9:12 roof came out ~20% stretched against the walls. The shipped
version gives each face a basis in its own plane: *u* level along the face,
*v* up the true slope. That also keeps lap courses horizontal on walls and
shingle courses running true up the roof.

## 4. Material list

| Material | Maps needed | Source | Notes |
|---|---|---|---|
| `siding` | albedo, normal, roughness | procedural | 6" lap. Geometry is flat; the courses are texture, not modelled |
| `shingle_gable` | albedo, normal, roughness | procedural | Front gable only — rear gable is lap, confirmed in P3 |
| `roof` | albedo, normal, roughness | procedural or CC0 | Composition shingle, light-mid grey |
| `trim` | roughness variation only | — | Painted; flat albedo is genuinely correct here |
| `concrete` | albedo, normal, roughness | CC0 | Broom-finish slab |
| `glass` | none | — | Already correct; do not texture |
| `post`, `soffit` | roughness only | — | Painted |
| `floor_oak` | albedo, normal, roughness | CC0 + video calibration | White oak, per transcript 0:31 |
| `drywall` | none — deliberately flat | — | Painted gypsum has no pattern worth a map |
| `carpet_loft` | albedo, normal, roughness | procedural | Carpet over pad, per transcript 6:46 |
| `slate_bath` | albedo, normal, roughness | CC0 | Per transcript 1:17 |

**Everything shipped is procedural**, generated by `make_textures.py`, and
that includes the slate and oak this section originally expected to source from
CC0 scans. Regular patterns tile perfectly, the texel density can be dialled to
match spec exactly, and the maps stay small. Photographic scans would be better
where irregularity is the point, but not enough better to pay for them here.

The practical consequence: **licensing is moot for the whole of tier 2.** No
third-party assets are in the model. It returns as a real constraint in tier 3,
where appliances and fittings get downloaded — and it has lead time, so it is a
shipping constraint there and not a detail.

One texturing lesson worth carrying forward, learned twice: **per-pixel noise
is invisible at these contrasts and destroys PNG compression.** It took the
exterior set from 2492 KB to 192 KB, and the interior set from 3491 KB to
435 KB, to replace it with low-frequency variation. `make_textures.py` has a
`lowfreq()` helper for exactly this reason.

## 5. Compression and budget

This is where a 29 KB model becomes megabytes if nobody is watching.

**Still to do**, and the only outstanding item in this tier. Everything below is
the plan, not the shipped state: the model currently ships PNG maps and comes in
well inside budget anyway.

**Do not ship PNG or JPEG.** Use **KTX2 / Basis Universal**
(`KHR_texture_basisu`) — GPU-compressed, stays compressed in VRAM, and Three.js
supports it via `KTX2Loader`.

Blender's exporter does not produce KTX2 directly. Post-process:

```bash
gltf-transform optimize lod0.glb lod0.ktx2.glb \
  --texture-compress ktx2 --texture-size 1024
```

`gltf-transform` also re-applies Draco, so run it after the Blender export and
treat the Blender `.glb` as an intermediate.

**Budget targets:**

| Level | Shipped | Ceiling | |
|---|---|---|---|
| `lod0` | **897.6 KB** | 4 MB | textured, interior included |
| `lod1` | **231.4 KB** | 1.5 MB | textured, no interior |
| `lod2` | **28.4 KB** | 200 KB | flat, deliberately untextured |

Sizes as of [#70](https://github.com/captproton/yardstake-ux/pull/70). `lod0`
grew with Tier 3's contents and the foundation; the ceilings have not moved.

Texture directory: **332 KB** across 7 materials. Making six albedos neutral
took it from 435 KB, since a map carrying no colour compresses better.

Gated in `finish_adu.py`: the export fails if a level exceeds its ceiling.

`lod2` is the siting model and must stay tiny — plausibly several instances on
screen at once, on a homeowner's phone. Texturing pushed it to 239 KB before it
was caught; it now ships flat-shaded, which at 20–100 ft costs nothing visible.

## 6. Configurator hooks — DONE

The finishes picker (the colour, roof and flooring choices in the Studio-Home
reference) needs runtime material swapping. Two routes were weighed:

**A. `KHR_materials_variants`** — the glTF-native mechanism. Variants are
declared in the file; the viewer switches by index. Clean, portable, and the
file carries its own options. Cost: every variant's textures ship in the
payload whether or not the user picks them.

**B. Runtime swap in Three.js** — keep one material set and change materials
found by name, with any extra textures loaded on demand from a manifest.
Larger initial code, much smaller initial payload, and new finishes can be
added without re-exporting the model.

**B shipped**, with a `variants:` block in `spec.yaml` that generates
`export/variants.json`. It matches how the pipeline already works
(spec → artefact) and keeps the initial load light, which matters more for a
homeowner on a phone than portability does.

### What shipped

**5 sets, 14 options, zero extra bytes in the payload.**

| Set | Targets | Options |
|---|---|---|
| `color_theme` | `adu_siding`, `adu_shingle_gable` | Sandstone\*, Cloud, Sage, Charcoal |
| `roof_colour` | `adu_roof` | Weathered grey\*, Charcoal, Driftwood |
| `trim_colour` | `adu_trim`, `adu_post`, `adu_soffit` | White\*, Almond |
| `main_flooring` | `adu_floor_oak` | Natural oak\*, Light oak, Walnut |
| `bath_flooring` | `adu_slate_bath` | Slate\*, Limestone |

\* default. Every default is the as-built condition sampled from the video or
transcript, so the model out of the box is still the unit that was filmed —
the options are additions, not a re-colouring of the evidence.

Body and gable move together under `color_theme`: the front gable is painted
cedar shingle in the same colour as the lap siding, confirmed in P3.

**Why it costs nothing.** Six albedo maps are authored **neutral** — they carry
the luminance pattern (lap shadow lines, shingle courses, oak grain) and no
colour at all. Colour rides entirely on `baseColorFactor`. So an option is
three floats rather than a texture, the whole set adds **0 bytes** to the
download, and a new colour is a `spec.yaml` edit with no re-export. Going
neutral also took the texture directory from 435 KB to 314 KB, because a
neutral map compresses better.

Getting the factor into the file needed a workaround worth knowing about.
Blender's glTF exporter does not recognise a multiply node feeding Base Color,
so it writes `baseColorTexture` with **no factor** — which would have shipped
every model untinted. Two node types were tried first: `ShaderNodeMixRGB` is
ignored by the exporter, and `ShaderNodeMix` raised on the Vector socket. What
shipped is `patch_base_color_factors()` in `finish_adu.py`, which rewrites the
GLB's JSON chunk directly after export and re-pads it to a 4-byte boundary.

### Runtime — Three.js

The manifest is deliberately dumb. `sets[].targets` are material names,
`options[].value` is a linear RGBA. Nothing has to re-read the glTF.

```js
// Load once, alongside the model.
const manifest = await (await fetch('/models/barn_cabin_524/variants.json')).json();

// Index every material by name. glTF export flattens the scene graph, so a
// plain traverse finds all of them — the same reason display-mode switching
// keys off object-name prefixes rather than collections.
const byName = new Map();
model.traverse((o) => {
  if (!o.isMesh) return;
  for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
    if (m) byName.set(m.name, m);
  }
});

// Three.js maps baseColorFactor onto material.color. The manifest values are
// LINEAR, as glTF requires, so set them with setRGB in linear space — NOT with
// .set('#rrggbb'), which converts from sRGB and washes every colour out.
function applyChoice(setId, optionId) {
  const set = manifest.sets.find((s) => s.id === setId);
  const opt = set.options.find((o) => o.id === optionId);
  for (const name of set.targets) {
    const mat = byName.get(name);
    if (!mat) { console.warn(`variant target missing: ${name}`); continue; }
    mat.color.setRGB(opt.value[0], opt.value[1], opt.value[2],
                     THREE.LinearSRGBColorSpace);
  }
  // No needsUpdate — .color is a uniform, not a shader recompile.
}

// The defaults are already baked into the file, so this is only needed when
// restoring a saved configuration.
for (const set of manifest.sets) {
  const def = set.options.find((o) => o.default);
  if (def) applyChoice(set.id, def.id);
}
```

Two things that will bite whoever wires the UI:

- **The values are linear, not sRGB.** Passing them to `color.set()` applies an
  sRGB→linear conversion they have already had, and everything renders pale.
- **Swatch colours are not these numbers.** A UI chip needs the sRGB encoding
  of the same value, or the chip and the building disagree — which reads as a
  bug in the model rather than in the picker.

### Verification

Gated in `finish_adu.py`: **every manifest target must name a material that
exists in the export.** Renaming a material now breaks the build instead of
silently breaking the picker in front of a homeowner.

That gate is necessary and not sufficient, so `variant_demo.py` re-imports the
exported `.glb`, applies the manifest exactly as the runtime does, and renders
three themes — [`../renders/tier2_variants.png`](../renders/tier2_variants.png),
sandstone / sage / charcoal.

**It earned its place on the first run, which produced three identical
images.** Blender's importer represents `baseColorFactor` as a `MIX` node — not
the `MIX_RGB` the demo was looking for — so the swap fell through to setting
Base Color directly, and that socket was already linked. A silent no-op, and
the name gate passed the whole time.

So the demo asserts a number rather than inviting a look: mean wall colour per
theme, and a hard failure if the widest separation is under 20/255. Current
result **166.2 / 138.7 / 96.2, separation 70.0**. The lap courses and shingle
detail survive the tint in all three, which is the neutral-albedo claim holding
up under a render rather than in principle.

One deliberate change along the way: the demo's first lighting was bright
enough that a 0.15 charcoal read as mid-grey. That flatters the mechanism by
hiding how dark the dark options actually are, so the exposure came down.

### Not covered by a colour swap

Recorded in `spec.variants.not_yet`, so the limits are explicit rather than
discovered by whoever builds the picker:

- **Countertops and cabinets** — need Tier 3 fixtures to exist first.
- **Roof material** (metal vs composition shingle) — a factor change cannot do
  it; the pattern is in the map, so it needs a second texture.
- **Styles and floor-plan variants** — geometry, not materials.

## 7. Verification

**Implemented in `verify_tier2.py` (5/5) and `finish_adu.py` (4/4).** Following
the pattern that has caught every real error so far, prefer measurable gates
over looking at renders:

1. **Texel density check** — computed px/ft per object within ±15% of spec.
   Result: **3290 of 3290 edges at exactly 128.0 px/ft**.
2. **Map completeness** — every material in `spec.yaml` has every map it
   declares; no silent fallback to flat colour.
3. **Size gates** — per-level ceilings from §5.
4. **UV sanity** — no UVs outside [0,1] where tiling is not intended; no
   zero-area UV faces (a classic boolean artefact).
5. **Round-trip** — re-import the compressed `.glb` into a clean session and
   confirm material count, map presence, and bbox, exactly as `finish_adu.py`
   already does.
6. **Configurator manifest targets real materials** — added with §6, so a
   renamed material breaks the build rather than the picker.
7. **Only then**, close-up renders at ~3 ft for human judgement.

Two of these were added *after* a defect got past the others, which is the
usual way. The reveal-slot check exists because `materials.clear()` was
silently stripping the tagging on export; the variant demo exists because a
name-only gate passed while the swap did nothing at all.

## 8. Open risks

**The luminance problem is still unresolved.** Hue is measured; brightness is
invented. This section warned that texturing would bake it in — the
neutral-albedo work for §6 has, as a side effect, largely undone that. The maps
now carry pattern and the colour lives in `baseColorFactor`, so correcting a
level is a three-float edit in `spec.yaml` rather than a re-bake. If a
controlled photo of the actual unit is ever obtainable — flat light, a grey card
in frame — it is now cheap to act on. Until then the levels remain unmeasured
and are labelled as such; do not let a texture launder a guess into apparent
fact.

**Per-face materials on wall meshes** (§3) is **done** — three slots per wall,
cladding / trim / drywall, gated. It was indeed a real architectural change to
`build_adu.py`, and doing it in Tier 1 while the openings were open was the
right call.

**Transmission plus textures** needs testing in Three.js. `KHR_materials_transmission`
requires a transmission render pass; combined with KTX2 and many materials it is
the most likely place for a platform-specific surprise. Test on a mid-range
Android phone early, not at the end.
