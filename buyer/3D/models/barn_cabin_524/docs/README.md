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
| **Tier 1** | Ceilings, floors, closet wall, doors, trim, reveals, ladder, guardrail, crawl hole | **done**, 16/16 gates — the crawl hole was cut in [#65](https://github.com/captproton/yardstake-ux/pull/65) |
| **Tier 2a** | UVs at 128 px/ft, exterior textures | **done**, 4/4 gates |
| **Tier 2b** | Interior textures, neutral albedos, configurator manifest | **done**, 5/5 + 4/4 gates |
| **Tier 3a** | Fixture footprints measured from A1.1 | **done**, 16/16 gates |
| **Tier 3b** | Casework, both sinks, both taps, mirror | **done**, 29/29 fixture gates |
| **Tier 3c** | Toilet | **done** ([#66](https://github.com/captproton/yardstake-ux/pull/66)) — built, not bought |
| **Tier 3d** | Appliances | **done** ([#67](https://github.com/captproton/yardstake-ux/pull/67)) — built, not bought |
| **Tier 3e** | Tub/shower, stacked W/D, geometry gate | **done** ([#68](https://github.com/captproton/yardstake-ux/pull/68)) — both were measured and never built |

Merged to `main` in [#57](https://github.com/captproton/yardstake-ux/pull/57), [#58](https://github.com/captproton/yardstake-ux/pull/58), [#59](https://github.com/captproton/yardstake-ux/pull/59), [#60](https://github.com/captproton/yardstake-ux/pull/60),
[#61](https://github.com/captproton/yardstake-ux/pull/61), [#62](https://github.com/captproton/yardstake-ux/pull/62), [#64](https://github.com/captproton/yardstake-ux/pull/64), [#65](https://github.com/captproton/yardstake-ux/pull/65), [#66](https://github.com/captproton/yardstake-ux/pull/66),
[#67](https://github.com/captproton/yardstake-ux/pull/67) and [#68](https://github.com/captproton/yardstake-ux/pull/68). The placement developer is unblocked — `lod2`
and their handoff are on `main`, and **byte-identical at 24.1 KB through all
eleven**. That is the constraint the whole ladder was designed around, and it
has never moved.

**Tier 3's build half is complete** — casework, both sinks, both taps, the
mirror, the toilet, the tub/shower, the crawl hole, the stacked W/D and all
three appliances. 93 meshes, `lod0` **889.5 KB** against a 4 MB ceiling,
40/40 fixture gates and 10/10 geometry gates.

**That claim was made once before and was wrong.** After [#67](https://github.com/captproton/yardstake-ux/pull/67) the plan
said the build half was complete while the tub/shower and the stacked washer/
dryer were both measured and unbuilt. `verify_geometry.py` exists so the claim
is checkable rather than asserted — **run it before ever saying "complete"
again.**

**Tiers 1 and 2 are complete bar KTX2 compression**, which is optimisation
rather than necessity. Tier 3's *build* half is done: cabinets, counters,
backsplash, uppers, hood, the kitchen sink and tap, and the bath vanity with
its basin, three-hole tap and mirror. `lod0` is now **870 KB** against a 4 MB
ceiling.

**The model has three primitives now**, not one. `box`/`multibox` for
architecture, `tube()` for swept round stock (taps), and `loft()` +
`ellipse_ring()` for revolved forms. Building `loft()` generic **paid for
itself**: the toilet used it unchanged, and the buy list shrank from four items
to three.

**Every "this must be bought" assumption turned out to be wrong** — the basin,
the tub, the toilet, and all three appliances. Each was buildable from the
primitives already here, and **nothing in Tier 3 needed a third-party asset**.

The licensing decision sat in the critical path for most of this work and never
had to be made. The model contains **no third-party content at all**: textures
are procedural, geometry is spec-driven. That is worth protecting — it is a
property that is easy to lose and hard to recover.

What remains of Tier 3 is the *buy* half — appliances and the toilet — plus two
small omissions listed under [What remains](#what-remains).

The **exterior is finished work**. Silhouette, both pitches, ridge height,
overhangs, and every opening are validated against the sheet. Nothing in this
ladder should require touching exterior geometry.

The **interior is built and textured**. Tier 1 delivered ceilings, floor
planes, the closet wall, six door leaves, casing, baseboard, tagged window
reveals, the loft ladder and its guardrail; Tier 2 gave them oak, slate, carpet
and drywall. What is missing from the interior now is *contents* — that is
Tier 3.

The model is also **configurable**: 5 option sets and 14 finishes swap at
runtime from `export/variants.json`, adding zero bytes to the download. See
[TIER-2 §6](TIER-2-materials-and-textures.md#6-configurator-hooks--done) and
[`../renders/tier2_variants.png`](../renders/tier2_variants.png).

For the progression, compare
[`../renders/fpv_interior_asis.png`](../renders/fpv_interior_asis.png),
[`../renders/tier1_trim_ladder.png`](../renders/tier1_trim_ladder.png) and
[`../renders/tier2_interior.png`](../renders/tier2_interior.png).

## Looking at the model

Three artefacts, and it matters which one you open:

| To do this | Open |
|---|---|
| Inspect or edit in Blender | **`barn_cabin_524_textured.blend`** |
| Load in a viewer or the web app | `export/barn_cabin_524.glb` |
| Placement / siting | `export/barn_cabin_524_lod2.glb` |

**Not `barn_cabin_524.blend`.** That is `build_adu.py`'s output — geometry
only, no materials — and opening it shows a grey model that looks like the
texturing failed. It has not; there is nothing in that file to see. The
textured file is written by `finish_adu.py`. Both are gitignored and are
regenerated by a normal build.

For the interior, run [`../views.py`](../views.py) from Blender's Scripting
tab and call `dollhouse()`, `cutaway()`, `walkthrough()` or `interior_only()`;
`full()` restores. It changes visibility only, never geometry or materials, so
it cannot affect an export. Or skip it entirely and press **Shift+`** in the
viewport to walk around with W/A/S/D.

`walkthrough()` deliberately hides nothing — standing in a room you want the
ceiling above you. Hiding the roof and ceilings is right for looking *down*
into the model and wrong for walking through it.

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
| **2** | Materially real — UVs, texel density, tileable maps, KTX2 compression, configurator-swappable finishes | [TIER-2](TIER-2-materials-and-textures.md) — **done bar KTX2**, which is optimisation only. [#58](https://github.com/captproton/yardstake-ux/pull/58) |
| **3** | Furnished — kitchen casework, appliances, bath fixtures, furniture | [TIER-3](TIER-3-fixtures-and-furnishing.md) — **casework, both sinks, both taps and the mirror built** ([#60](https://github.com/captproton/yardstake-ux/pull/60), [#62](https://github.com/captproton/yardstake-ux/pull/62), [#64](https://github.com/captproton/yardstake-ux/pull/64)); appliances and toilet remain |

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

**Use `barn_cabin_524_lod2.glb`** (28.4 KB). It is the massing: no openings, no
glazing, no interior. A gate in `finish_adu.py` fails the build if it exceeds
200 KB — which has already caught one regression, when texturing took it to
239 KB.

> ⚠️ **CHANGED — the first time in twelve merged PRs.** `lod2` used to carry
> `Floor_slab`, a concrete slab under the whole building. A2.0 draws **two**
> foundations and this model is the **crawlspace** one, so that slab was the
> wrong variant. It is replaced by `Found_stemwall`: the building now stands on
> a **2'-0" stemwall** carrying a rim band for the floor build-up, not flat on
> a slab. The porch slab, which used to float, now bears on four piers, and
> the stemwall carries the **eight foundation vents A2.0 draws** (two north,
> three each side, none on the porch wall) as openings through it.
>
> **The bbox floor moves from −0.101 m to −0.972 m.** If you were treating the
> bottom of the model as the bearing plane, that plane has dropped 0.871 m.
> Everything above finished floor is unchanged. See [#69](https://github.com/captproton/yardstake-ux/issues/69).

**Units and axes.** glTF standard — **metres**, **Y-up**. The scene is authored
at 1 unit = 1 foot and converted on export; do not apply a further scale.

**Origin is not the bounding-box corner.** `(0,0,0)` sits at:

| Axis | Location |
|---|---|
| `X = 0` | west exterior wall face |
| `Y = 0` | main finished floor |
| `Z = 0` | porch outer (south) edge |

The building extends toward **−Z**. Overhangs and the foundation go negative
on several axes, so the bbox is `min (−0.457, −0.972, −9.601)` to
`max (7.163, 5.428, 0.457)` m. **0.972 m of that sits below the finished
floor: 0.362 m of floor build-up (subfloor + joists + mud sill) resting on a
0.610 m stemwall.**

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

**Grade is still not modelled, and the plan set declines to fix it.** `Y = 0`
is the finished floor. A4.0's pony wall detail dimensions the below-floor zone
as *"VARIES WITH GRADE, 18" MIN"* — there is no plan dimension to hand you.
**No LOD draws a ground plane.** `spec.foundation.grade` assumes 1'-6" of
exposed stemwall (`confidence: assumed`), but it exists only so verification can
check that the vents clear grade — no geometry expresses it, so do not read a
bearing plane off the model. **Placement still owns the grade-to-floor offset**,
and now has a real 2'-0" stemwall to bed into the ground.

**Stability guarantee.** Origin, axes and units are frozen and have never
moved. `lod2` contents changed **once**, in [#69](https://github.com/captproton/yardstake-ux/issues/69), for the foundation
variant above — and that was a conversation first and a commit second, which is
what this guarantee asks for.

---

## Tier 1 build rules

Written as handoff conditions while Tier 1 was expected to be delegated. They
hold as our own constraints — they exist to keep tiers 2 and 3 cheap.

1. **Follow the object-name prefixes.** Display-mode switching keys off names
   (`Wall_`, `Roof_`, `Part_`, `Glazing_`, …) because glTF export flattens
   collections — verified: 35 nodes, zero with children. New prefixes are fine
   but must be declared in `spec.yaml`, or the dollhouse toggle silently breaks.
2. **Build UV-ready.** Adopt the texel density from
   [TIER-2 §2](TIER-2-materials-and-textures.md) — **128 px/ft, in-plane cube
   projection, unwrapped after booleans** — while the geometry is being made.
   *In-plane*, not world-axis: a world-axis projection foreshortens sloped
   faces and stretched the 9:12 roof by ~20% against the walls.
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

Tiers 1 and 2 are complete bar one optimisation. **Tier 3's build half is
done** and verified by `verify_geometry.py`. In order of value:

| Work | Notes |
|---|---|
| **T3:** furniture | The last unbuilt item in the tier, and the only one with `status: not_yet_placed`. Architectural fill-in-the-space per §4 — schematic masses, no licensing exposure |
| **T3:** appliance finish variant | The two filmed units differ (white fridge at 2:11, stainless at 2:27), so finish is a choice. Bodies and fronts are already on one material, so this is a `spec.variants` entry and no geometry |
| **Foundation:** fix the variant mix | **[#69](https://github.com/captproton/yardstake-ux/issues/69)** — A2.0 has been read and the question is settled. It draws TWO foundations, as A1.0/A1.1 draw two roofs: a crawlspace (stem walls, centre girder, **the crawl hole**) and a slab (no crawl hole). The MAIN FLOOR FRAMING plan and A1.1 both carry the crawl hole, so this model is the **crawlspace** variant — and `Floor_slab` is slabbing the main body from a callout that applies to the **porch**. The crawl hole is right; the slab is wrong. Still the only open item that could **invalidate** geometry rather than add to it |
| **T2:** KTX2 compression | Optimisation, not necessity — `lod0` is 889.5 KB against a 4 MB ceiling. Confirm `gltf-transform` is installed first |
| **UI:** wire the finishes picker | The manifest and the material names are frozen and gated; nothing in the model blocks it |

Two prerequisites are long discharged: **texel density is fixed at 128 px/ft**
in `spec.texturing`, and the **window reveals are tagged and verified through
export** — that one needed a fix, because `materials.clear()` was silently
resetting every polygon's material index and stripping them.

**The material names are now a public API.** The configurator manifest
addresses materials by name (`adu_siding`, `adu_roof`, …) exactly as the
display modes address objects by name prefix. Renaming one breaks the picker,
so both are gated: `finish_adu.py` fails the build if a manifest target names a
material that does not exist.

**Asset licensing never became real, and that is the headline.** It was
flagged as the long-lead item and sat in the critical path for most of this
work. Every fixture it gated — the basin, the tub, the toilet, the fridge, the
range, the dishwasher — turned out to be buildable from `box`, `tube` and
`loft`. Nothing was ever downloaded.

**The model contains no third-party content at all.** Textures are procedural,
generated by `make_textures.py`; geometry is spec-driven. That property is easy
to lose and hard to recover, so protect it: before accepting a licensing
dependency, try the primitives first.

**Fixture heights are assumed, and that is permanent.** The plan set contains
no interior elevations on any sheet, so every height in `spec.fixtures` is an
industry standard rather than a measurement, and a gate fails the build if one
is ever presented otherwise. Unlike the exterior luminance problem, no
photograph fixes this — only a dimensioned interior elevation would.

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
6. **A gate that checks names does not check behaviour.** The configurator
   manifest passed its "every target is a real material" gate while the swap
   itself was a silent no-op, and three colour themes rendered identically.
   When something is meant to *change* an output, assert the change.
7. **Relative gates cannot catch a systematic error.** Every Tier 3 footprint
   check — overlap, clearance, containment — would pass just as happily on a
   wrong datum, because they all measure fixtures against each other. Only
   drawing the results back onto the source sheet proves the anchor. The same
   reasoning is why P3's overlay caught a mirrored building that four
   isometrics had not.
8. **A measurement window that can report itself is not a measurement.** Ink
   bounding boxes inside hand-chosen windows gave six wrong fixtures out of
   nine, and every one looked plausible, because a window that clips its
   subject and a window inside its subject both just report the window.
   Measure the drawn lines.
9. **A gate must report the threshold it enforces, not just its inputs.** The
   basin clearance check compared against `toe + 0.25` while printing only
   "carcass starts 3-1/2\"", so a failure would have read as a contradiction
   rather than a near miss.
10. **Some defects are invisible to a render, and this keeps happening.** P2's
    boolean kept its full volume while looking cut. The configurator manifest
    passed its gate while the swap did nothing. The faucet's duplicated path
    point produced eight twisted slivers that `validate()` did not strip and no
    picture would ever show. Counting — volume, vertices, face areas, pixel
    separation — is what finds these. Looking is not.
11. **Check the reviews before merging.** Copilot reviewed every PR in this
    series and twelve comments went unread while "all green" was being reported
    from a local gate sweep. A green sweep is evidence about the code, not
    about whether anyone has looked at it. It also has to be REQUESTED from the
    PR page each time — it does not watch the repo, and a PR with no review is
    usually one nobody asked about, not one waiting on a slow bot.
12. **A gate that names a container must test the EXTENT, not the corner.**
    The room-assignment check compared a fixture's origin against the
    partition, so the vanity sitting 7" across the bath doorway was invisible
    to it. The same bug appeared twice more in one sitting: the door-blocking
    gate first tested only a fixture's far edge, skipping every kitchen fixture
    against the wall it shares, and the tap gate tested "inside the rim" when
    the bowl opening is also inside the rim.
13. **Correct beats literal.** A true mirror reflects whatever environment it
    is handed, so it put foliage inside the bathroom — in the shipped model,
    not just the preview. A flat grey panel reads as a mirror by context in
    every renderer. Same reasoning that keeps drywall untextured.
14. **A lit render is not evidence.** Two "defects" reported here — vanity
    doors with no division, and a texture blotch — were a washed-out reveal and
    a patch of daylight. One flat-shaded render settled both. Rule 3 applies to
    your own observations, not only to other people's.
15. **"This must be bought" has been wrong every time it was tested.** The
    basin, the tub and the toilet were each assumed to need a third-party
    asset; each turned out to be buildable from the primitives already here.
    The pattern is that *organic* is confused with *unfamiliar*. Test before
    accepting a licensing dependency — it is the most expensive kind to take on
    and the easiest to assume.
16. **Coplanar capped faces z-fight, and no gate sees them.** The toilet lid
    started exactly at the bowl's rim: identical centre, identical area,
    opposite normals. Every gate passed. When two lofted or capped solids meet
    at a shared plane, offset them by something physically meaningful — the
    seat ring, in that case — rather than leaving them coincident.

    **Writing this rule did not stop it happening again.** The dishwasher's
    handle recess reintroduced the same defect one PR later, and a check for
    it returned CLEAR because it required the two faces to have equal *area*.
    They do not need equal area: a small face lying on a large one overlaps
    just as badly. Test coplanar + same normal, and nothing else.
17. **A gate keyed to a NAME can be theatre.** `verify_geometry` first mapped
    each fixture to an object-name prefix, but appliances share `Appl_body` /
    `Appl_front` / `Appl_dark`, so four fixtures passed on the same three
    meshes — six of ten checks would have passed with one appliance built.
    That is the defect the gate exists to catch, reproduced inside the gate.
    Test POSITION: is there geometry inside this fixture's measured footprint,
    within its own height?
18. **A box's vertices all lie ON its boundary.** Shrinking a test volume
    inward to exclude neighbours excluded the stacked W/D's own geometry and
    failed a correctly built fixture. Test FACE CENTRES — a box's top and
    bottom centres are strictly inside its footprint, a neighbour's are not.
19. **A red test that moves the spec proves nothing.** Perturbing a fixture's
    position moves the build with it, so the gate passes and the test is a
    tautology. To prove a build-completeness gate, disable the BUILD and leave
    the spec intact — that is the actual defect being simulated.
