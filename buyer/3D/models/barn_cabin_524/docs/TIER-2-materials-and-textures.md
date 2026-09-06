# Tier 2 — Materials and textures

**Goal.** Replace flat PBR colours with real, tiling materials at a controlled
texel density, compressed for the web, and swappable at runtime so the
configurator's finishes picker has something to pick.

**Owner:** us — as are Tiers 1 and 3. The placement developer's scope is
placement only, and that is the sole external interface — see
[The one handoff](README.md#the-one-handoff--to-the-placement-developer).
Nothing here is blocked on another party; we set the pace.

**Partly blocked.** Interior materials (drywall, oak floor, slate) need Tier 1's
surfaces to exist. Everything else can start now: all exterior materials, the
texel density decision, the UV strategy, the KTX2 toolchain and the size gates.

**Settle §2 before Tier 1 geometry is built.** Texel density constrains how
Tier 1 must be authored. Since both tiers are ours, decide it once at the start
of Tier 1 and use it throughout — retrofitting UVs onto finished trim and
ceilings costs far more than generating them in place.

**Do not break the handoff.** `lod2` is the placement developer's model. If
texturing inflates it past ~100 KB that is a bug, not a tradeoff.

**Does not depend on:** Tier 3.

---

## 1. Where things stand

`spec.yaml → materials.library` defines eight materials, all flat colour, no
maps, no UVs:

```
siding  shingle_gable  roof  trim  glass  concrete  post  soffit
```

Their **hue** was sampled from verified video frames (6:56 and 7:50). Their
**luminance was not measured** and is set to plausible albedo — see
`materials.provenance`. That limitation carries forward into tier 2 and should
be resolved here if it is ever going to be, because a texture bakes it in.

Total `lod0` payload today: **29 KB**. This is the number tier 2 will move most.

## 2. Texel density — decide this first

Everything downstream depends on one number, and it belongs in `spec.yaml`, not
in a script.

**Recommendation: 128 px/ft (≈420 px/m), uniform across the model.**

Rationale: the tightest detail that must read crisply is the 6" lap siding
exposure. At 128 px/ft that's 64 px per course — comfortably sharp at the 2–6 ft
viewing distance a walkthrough implies, and still legible at configurator
orbit distance. A 22 ft wall maps to ~2816 px, so a 4K tile covers the longest
wall without repeating visibly.

Add to spec:

```yaml
texturing:
  texel_density_px_per_ft: 128
  projection: cube            # all geometry here is box-like
  tile_size_px: 1024          # per-material tile, repeated
  uv_channel: 0
```

**Verification gate:** a script that reports actual px/ft per object and fails
if any is more than ±15% off target. Without this, hand-unwrapped objects drift
and the siding scale visibly jumps between walls.

## 3. UV generation

The geometry is box-like, so cube projection is close to free — but three
details will bite:

**Unwrap after the booleans, never before.** Wall meshes are boolean results.
Openings introduce new faces that no pre-boolean UV layout accounts for.
Generate UVs as the last step in `build_adu.py`, after `difference()`.

**Project on world axes, not local.** Objects are axis-aligned so world-space
cube projection gives consistent, seam-free tiling across adjacent walls —
siding courses will line up around a corner instead of stepping.

**Openings will produce seams at the reveals.** The jamb faces inside each
window cut are perpendicular to the wall face and will take a different
projection axis. Acceptable for lap siding (the reveal is trim in reality, not
siding), but it means the reveals want the `trim` material, not `siding`. That
implies a per-face material assignment on wall meshes, which is a change from
the current one-material-per-object model. **Flag this early — it's the single
most likely source of scope creep in tier 2.**

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
| **`floor_oak`** *(new)* | albedo, normal, roughness | CC0 + video calibration | White oak, per transcript 0:31 |
| **`drywall`** *(new)* | roughness, subtle normal | procedural | Painted interior walls |
| **`slate_bath`** *(new)* | albedo, normal, roughness | CC0 | Per transcript 1:17 |

**Prefer procedural-then-baked over photographic** for siding, shingle and
drywall. They're regular patterns, they tile perfectly, they carry no licensing
risk, and the texel density can be dialled to match spec exactly. Photographic
scans are better for slate and oak, where irregularity is the point.

**Licensing is a shipping constraint, not a detail.** Anything that reaches a
homeowner-facing configurator must be CC0 or explicitly commercially licensed.
Poly Haven and ambientCG are CC0. Record the source and licence per material in
`spec.yaml` alongside the maps — the same provenance discipline the dimensions
already get.

## 5. Compression and budget

This is where 29 KB becomes megabytes if nobody is watching.

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

| Level | Today | Tier 2 target | Ceiling |
|---|---|---|---|
| `lod0` | 29 KB | ≤ 2.5 MB | 4 MB |
| `lod1` | 26 KB | ≤ 1.5 MB | — |
| `lod2` | 17 KB | **≤ 100 KB** | 200 KB |

`lod2` is the siting model. It must stay tiny — plausibly several instances on
screen at once, on a homeowner's phone. **If texturing inflates `lod2`, that is
a bug, not a tradeoff.** Give it a single low-res atlas or leave it flat-shaded.

**Add both as gates**, in the manner of the existing export gates: fail the
build if a level exceeds its ceiling.

## 6. Configurator hooks

The finishes picker (countertops / cabinets / fixtures / flooring in the
Studio-Home reference) needs runtime material swapping. Two viable routes:

**A. `KHR_materials_variants`** — the glTF-native mechanism. Variants are
declared in the file; the viewer switches by index. Clean, portable, and the
file carries its own options. Cost: every variant's textures ship in the
payload whether or not the user picks them.

**B. Runtime swap in Three.js** — keep one material set, swap `map` /
`normalMap` / `roughnessMap` on materials found by name, with textures loaded
on demand from a manifest. Larger initial code, much smaller initial payload,
and new finishes can be added without re-exporting the model.

**Recommendation: B**, with a `materials.variants` block in `spec.yaml` that
generates the manifest. It matches how the pipeline already works (spec →
artefact) and keeps the initial load light, which matters more for a
homeowner on a phone than portability does.

Either way the material *names* are the API — same as the object-name prefixes
that drive the display modes. Freeze the naming before building UI against it.

## 7. Verification

Following the pattern that has caught every real error so far, prefer
measurable gates over looking at renders:

1. **Texel density check** — computed px/ft per object within ±15% of spec.
2. **Map completeness** — every material in `spec.yaml` has every map it
   declares; no silent fallback to flat colour.
3. **Size gates** — per-level ceilings from §5.
4. **UV sanity** — no UVs outside [0,1] where tiling is not intended; no
   zero-area UV faces (a classic boolean artefact).
5. **Round-trip** — re-import the compressed `.glb` into a clean session and
   confirm material count, map presence, and bbox, exactly as `finish_adu.py`
   already does.
6. **Only then**, close-up renders at ~3 ft for human judgement.

## 8. Open risks

**The luminance problem is still unresolved.** Hue is measured; brightness is
invented. Texturing bakes it in and makes it much more expensive to change
later. If a controlled photo of the actual unit is ever obtainable — flat light,
a grey card in frame — that is the moment to use it. Otherwise, document that
the levels remain unmeasured and move on; do not let a texture launder a guess
into apparent fact.

**Per-face materials on wall meshes** (§3) is a real architectural change to
`build_adu.py`. Scope it explicitly rather than discovering it mid-build.

**Transmission plus textures** needs testing in Three.js. `KHR_materials_transmission`
requires a transmission render pass; combined with KTX2 and many materials it is
the most likely place for a platform-specific surprise. Test on a mid-range
Android phone early, not at the end.
