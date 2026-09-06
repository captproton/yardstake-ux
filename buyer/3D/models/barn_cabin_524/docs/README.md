# barn_cabin_524 — interior finish ladder

Context for anyone picking up work on this model. The model itself, its
provenance and its verification history live in [`../spec.yaml`](../spec.yaml);
this directory only covers what comes *next*.

## Where the model stands

Phases P1–P4 are complete and gated:

| Phase | Output | State |
|---|---|---|
| P1 | `spec.yaml` — every dimension with a sheet citation | done |
| P2 | `build_adu.py` — massing + openings, no hardcoded dimensions | done |
| P3 | Overlay against A1.1 at true 1/4"=1'-0" | done, −0.18" mean / 0.21" sd |
| P4 | Materials, glazing, 3 LODs, Draco `.glb` | done |
| **Tier 1** | Ceilings, floors, closet wall, doors, trim, reveals, ladder, guardrail | **done**, 14/14 gates |
| **Tier 2a** | UVs at 128 px/ft, exterior textures | **done**, 4/4 gates |

Merged to `main` in [#57](https://github.com/captproton/yardstake-ux/pull/57).
The placement developer is unblocked — `lod2` and their handoff are on `main`.

The **exterior is finished work**. Silhouette, both pitches, ridge height,
overhangs, and every opening are validated against the sheet. Nothing in this
ladder should require touching exterior geometry.

The **interior is built but untextured**. Tier 1 delivered ceilings, floor
planes, the closet wall, six door leaves, casing, baseboard, tagged window
reveals, the loft ladder and its guardrail. What is missing is materials:
interior surfaces still carry flat colour while the exterior is textured.

For the before/after, compare
[`../renders/fpv_interior_asis.png`](../renders/fpv_interior_asis.png) with
[`../renders/tier1_trim_ladder.png`](../renders/tier1_trim_ladder.png).

## Ownership

| Work | Owner |
|---|---|
| Placement in the buildable envelope | **the placement developer** — this and nothing else |
| Tier 1 — schematic interior | us |
| Tier 2 — materials and textures | us |
| Tier 3 — fixtures and furnishing | us |

All three tiers are ours, and all three are needed.

**This is simpler than it looks.** There is exactly one external interface — the
`.glb` we hand the placement developer — and it is already stable. Everything
else is our own sequencing, which means nothing in this ladder is blocked on
another party. We set the pace.

## The ladder

| Tier | Scope | Plan |
|---|---|---|
| **1** | Schematic interior — door leaves, trim, casing, ceiling planes, distinct floor surfaces, closet walls, loft ladder + guardrail | [TIER-1](TIER-1-schematic-interior.md) — **DONE** |
| **2** | Materially real — UVs, texel density, tileable maps, KTX2 compression, configurator-swappable finishes | [TIER-2](TIER-2-materials-and-textures.md) — **exterior done; interior, KTX2 and configurator hooks remain** |
| **3** | Furnished — kitchen casework, appliances, bath fixtures, furniture | [TIER-3](TIER-3-fixtures-and-furnishing.md) — sketch, not started |

> **Note on numbering.** In earlier conversation these tiers were described
> once with fixtures folded into tier 1. That was a slip. The definitions above
> are authoritative: tier 1 is *schematic geometry only* and carries no fixtures.

**Settled:** furniture and appliances are both **shown but not included in the
price**, matching how Studio-Home presents default appliances. The furniture is
architectural fill-in-the-space — schematic and unbranded, there to read scale.
Disclosure alongside any price is a UI requirement the model cannot enforce.
See [TIER-3 §4](TIER-3-fixtures-and-furnishing.md#4-furniture-and-appliances--decided).

---

## The one handoff — to the placement developer

Their scope is placement in the buildable envelope, and nothing else. They take
the exported `.glb`; nothing in tiers 1–3 may break it. All figures verified
against the current export.

**Use `barn_cabin_524_lod2.glb`** (17.0 KB). It is the massing: no openings, no
glazing, no interior. Nothing in tiers 1–3 lands in it.

**Units and axes.** glTF standard — **metres**, **Y-up**. The scene is authored
at 1 unit = 1 foot and converted on export; do not apply a further scale.

**Origin is not the bounding-box corner.** `(0,0,0)` sits at:

| Axis | Location |
|---|---|
| `X = 0` | west exterior wall face |
| `Y = 0` | main finished floor |
| `Z = 0` | porch outer (south) edge |

The building extends toward **−Z**. Overhangs and the slab go negative on
several axes, so the bbox is `min (−0.457, −0.101, −9.601)` to
`max (7.163, 5.428, 0.457)` m.

**Dimensions for envelope maths:**

| Measure | Feet | Metres |
|---|---|---|
| Wall footprint | 22'-0" × 30'-0" | 6.706 × 9.144 |
| Including overhangs | 25'-0" × 33'-0" | 7.620 × 10.058 |
| Height, finished floor to top of roof | 17'-9 11/16" | 5.428 |

> **Setback warning.** The eave and rake project **18" (0.457 m) beyond every
> wall face**, on all four sides. Many jurisdictions measure setbacks to the
> wall but cap eave projection under a separate rule, so the envelope check
> needs *both* footprints, not one. Using 25' × 33' everywhere will
> over-constrain siting; using 22' × 30' everywhere may under-report the
> encroachment.

**Grade is not modelled.** `Y = 0` is the finished floor, not grade. The
stemwall reveal is not in the plan set and the slab bottom sits at −0.101 m.
Placement owns the grade-to-floor offset.

**Stability guarantee.** Origin, axes, units and `lod2` contents are frozen. If
any tier needs to change them, that is a conversation with them, not a commit.

---

## Tier 1 build rules

Written as handoff conditions while Tier 1 was expected to be delegated. They
hold as our own constraints — they exist to keep tiers 2 and 3 cheap.

1. **Follow the object-name prefixes.** Display-mode switching keys off names
   (`Wall_`, `Roof_`, `Part_`, `Glazing_`, …) because glTF export flattens
   collections — verified: 35 nodes, zero with children. New prefixes are fine
   but must be declared in `spec.yaml`, or the dollhouse toggle silently breaks.
2. **Build UV-ready.** Adopt the texel density from
   [TIER-2 §2](TIER-2-materials-and-textures.md) — **128 px/ft, world-axis cube
   projection, unwrapped after booleans** — while the geometry is being made.
   Retrofitting UVs onto finished trim and ceilings is far more expensive than
   generating them in place. **Because tiers 1 and 2 are both ours, decide this
   once, at the start of Tier 1, and use it throughout.**
3. **`lod0` only.** Nothing added here may appear in `lod1` or `lod2` — the
   placement developer's model depends on it.
4. **Spec-driven.** Dimensions and positions in `spec.yaml` with a `source:` and
   a confidence, never hardcoded. Exterior openings are measured to ±⅝";
   interior door *positions* are ±6" and labelled as such. Do not let a new
   guess inherit the credibility of a measurement.
5. **All gates still pass.** `build_adu.py` clean, `verify_openings.py`
   ALL PASS, `finish_adu.py` both gates — from a clean rebuild, not incrementally.

**Scope boundary with Tier 2.** Tier 1 lists "floor material" and Tier 2 lists
textures, which overlap. The split: **Tier 1 delivers the floor and ceiling
*planes* with a flat material slot each; Tier 2 replaces the flat colour with
textured oak, slate and drywall.**

**The loft ladder** is the one Tier 1 item with real dimensional data already in
hand — 5/4×4 clear vertical grain Douglas fir, 20° heel cut, flange-bolted
(video 5:02–5:20). Use it rather than inventing one.

## What remains

Tier 1 is complete, so nothing is blocked any more. In order of value:

| Work | Notes |
|---|---|
| **T2:** interior materials — drywall, white oak, slate, carpet | Unblocked. Biggest visible gain, since the interior is the only flat-coloured part left |
| **T2:** configurator hooks | [TIER-2 §6](TIER-2-materials-and-textures.md#6-configurator-hooks). What makes a Studio-Home style finishes picker possible |
| **T2:** KTX2 compression | Optimisation, not necessity — `lod0` is 285 KB against a 4 MB ceiling. Confirm `gltf-transform` is installed first |
| **T3:** fixtures and furniture | Sketch; firm it up before building |

Two prerequisites are already discharged: **texel density is fixed at 128 px/ft**
in `spec.texturing`, and the **window reveals are tagged and verified through
export** — that one needed a fix, because `materials.clear()` was silently
resetting every polygon's material index and stripping them.

Asset licensing, flagged earlier as the long-lead item, is moot for everything
built so far: the exterior textures are procedural, generated by
`make_textures.py`, with no third-party assets. It returns as a real constraint
only in Tier 3, where appliances and fittings get downloaded.

## Ground rules inherited from P1–P4

Keep these — they caught real errors:

1. **The spec is the source of truth.** No dimensions, colours or positions
   hardcoded in scripts. Everything flows from `spec.yaml`. When P4 changed the
   exterior wall from 6½" to 5½", every opening volume re-derived itself and
   all ten checks still passed with no code edits.
2. **State provenance and confidence.** Exterior openings are measured to
   ±⅝"; interior door *positions* are ±6" and labelled as such. Don't let a
   guess inherit the credibility of a measurement.
3. **Verify geometrically, not visually.** A render that looks right can be
   wrong. P2's booleans imprinted edges without removing material — face counts
   went up, corners existed, and only a volume check caught it. P3's overlay
   caught a mirrored building that four isometric renders had hidden.
4. **Confirm a sample before trusting it.** A "siding" colour patch turned out
   to be the pollinator garden. Crop and look before you measure.
5. **Video is appearance evidence, never geometry.** Hue is reliable; luminance
   from an auto-exposing camera is not.
