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
| **Tier 3f** | Porch sconce, `fixtures.mounted` anchor, `verify_mounted` | **done** ([#74](https://github.com/captproton/yardstake-ux/pull/74)) — the first position taken from footage, because there is no electrical sheet |
| **Foundation** | Crawlspace stemwall, footing, rim, piers, the eight vents A2.0 draws | **done** ([#70](https://github.com/captproton/yardstake-ux/pull/70)) — the first `lod2` change in twelve PRs |
| **Tier 3g** | Furniture, in switchable arrangements | **done** ([#77](https://github.com/captproton/yardstake-ux/pull/77)) — Tier 3's last unbuilt item; merging deliberately stops at the arrangement boundary |
| **Configurator** | Presence-swap variants — bedroom / office / unfurnished | **done** ([#78](https://github.com/captproton/yardstake-ux/pull/78)) — a sibling of `sets`, purely additive |
| **Tooling** | Camera presets + ADU sidebar panel, framing gated | **done** ([#71](https://github.com/captproton/yardstake-ux/pull/71)) — tooling only, cannot reach a `.glb` |
| **Tooling** | `views.py` honours `presence`; manifest treated as untrusted | **done** ([#81](https://github.com/captproton/yardstake-ux/pull/81)) — our own panel put the desk through the bed; seven review findings across three passes |
| **Tooling** | `inside_mesh` deduped into `verify_lib.py`, with a known-answer gate | **done** ([#82](https://github.com/captproton/yardstake-ux/pull/82)) — one bug that had to be fixed twice, and two dead leftovers the extraction itself created |
| **Front elevation** | Gable window, half-lite entry door, projecting ridge beam | **done** ([#83](https://github.com/captproton/yardstake-ux/pull/83)) — the sheet's third calibration attempt, and a door that had glazing all along |
| **Gates** | UV gate says which meshes may skip UVs, and why | **done** ([#86](https://github.com/captproton/yardstake-ux/pull/86)) — the obvious fix would have silently dropped 74 meshes out of the gate |
| **Gates** | `front_elevation` refuses a scene it cannot test; one finding retracted | **done** ([#87](https://github.com/captproton/yardstake-ux/pull/87)) — a misrun could look exactly like the defect [#83](https://github.com/captproton/yardstake-ux/pull/83) fixed |
| **Openings** | Window sash built from the declared type; exterior casing on all eleven openings | **done** ([#89](https://github.com/captproton/yardstake-ux/pull/89)) — every window was one flat pane while the spec typed all ten, and every `Trim_` was on the inside of the wall |
| **Openings** | Sash visible from indoors; a stool and apron under every window | **done** ([#90](https://github.com/captproton/yardstake-ux/pull/90)) — #89's sash was a decal on the outside face, and no window had a ledge; both found by looking, neither by a gate |
| **Tier 3h** | The stacked W/D gets a drum and a control panel | **done** ([#91](https://github.com/captproton/yardstake-ux/pull/91)) — built since #68 and shaped like a cupboard; built from primitives, not downloaded |
| **Loft access** | The ladder rebuilt from the builder's own transcript | **done** ([#96](https://github.com/captproton/yardstake-ux/pull/96)) — nine rungs at 12" on a 20° rake, dadoed into 1"×3½" rails that run 3 ft over the loft as handles |
| **Loft access** | The ladder laid out on the rail, dadoed, hung on real hardware, and moved out of the wall | **done** ([#100](https://github.com/captproton/yardstake-ux/pull/100)) — all of [#97](https://github.com/captproton/yardstake-ux/issues/97), plus a trim board the source describes and the model never had, plus the discovery that **the top 10" of both rails ran inside the loft floor slab**. Four review rounds, and the last two changed no geometry at all |
| **Export** | Five welds for mesh headroom, and #92's arithmetic corrected | **done** ([#98](https://github.com/captproton/yardstake-ux/pull/98)) — 119 → 112, and **three of the five were a mistake**; see the row below |
| **Handoff** | The three `lod2` welds reverted, and the contract gated | **done** ([#99](https://github.com/captproton/yardstake-ux/pull/99)) — #98 changed the placement developer's file while its PR body said it had not; `lod2` is byte-identical again and the promise is now a build gate rather than a sentence |
| **Doors** | The closet ships OPEN on the laundry half | **done** ([#93](https://github.com/captproton/yardstake-ux/pull/93)) — `default_state.bypass` had been inert for eight tiers; fourteen review findings, every one in the gates and none in the geometry |

Merged to `main` in [#57](https://github.com/captproton/yardstake-ux/pull/57), [#58](https://github.com/captproton/yardstake-ux/pull/58), [#59](https://github.com/captproton/yardstake-ux/pull/59), [#60](https://github.com/captproton/yardstake-ux/pull/60),
[#61](https://github.com/captproton/yardstake-ux/pull/61), [#62](https://github.com/captproton/yardstake-ux/pull/62), [#64](https://github.com/captproton/yardstake-ux/pull/64), [#65](https://github.com/captproton/yardstake-ux/pull/65), [#66](https://github.com/captproton/yardstake-ux/pull/66),
[#67](https://github.com/captproton/yardstake-ux/pull/67), [#68](https://github.com/captproton/yardstake-ux/pull/68), [#70](https://github.com/captproton/yardstake-ux/pull/70), [#71](https://github.com/captproton/yardstake-ux/pull/71) and
[#74](https://github.com/captproton/yardstake-ux/pull/74). The placement developer is unblocked — `lod2` and their
handoff are on `main`.

**`lod2` was byte-identical at 24.1 KB through eleven PRs, and changed in the
twelfth.** [#70](https://github.com/captproton/yardstake-ux/pull/70) replaced the wrong-variant `Floor_slab` with the
crawlspace stemwall, so `lod2` is now **29.6 KB** and its bbox floor moved from
−0.101 m to −0.972 m. That was a conversation before it was a commit, which is
what the stability guarantee actually asks for. Origin, axes and units have
still never moved.

**Tier 3 is complete** — casework, both sinks, both taps, the mirror, the
toilet, the tub/shower, the crawl hole, the stacked W/D, all three appliances,
the porch sconce and, last, the furniture — **and the building stands on a real
foundation.** 117 meshes, all of them shipped in `lod0` at **960.2 KB** against
a 4 MB ceiling, with 49/49 fixture gates, 12/12 geometry gates and 11/11
furniture gates.

**The model is also configurable in layout, not only in finish.** Two bedroom
arrangements share the floor and are alternatives — a bed and a home office,
staged twenty seconds apart in the tour video — and [#78](https://github.com/captproton/yardstake-ux/pull/78) added a
`presence` block to the manifest so the runtime can switch between them, or to
unfurnished. A runtime can only toggle what is in the file, so **`lod0` carries
the bedroom twice**, and a viewer that ignores `presence` renders a desk through
a bed. That obligation is spelled out in
[TIER-2 §presence](TIER-2-materials-and-textures.md#presence--a-second-block-not-a-second-meaning-for-sets).

**The viewer obligation was one we were failing ourselves.** `presence` tells
runtimes that `lod0` carries the bedroom twice and that ignoring the block
renders a desk through a bed — and our own sidebar did exactly that, because
`_show()` blanket-unhid every mesh it was not told to hide. [#81](https://github.com/captproton/yardstake-ux/pull/81)
made `views.py` read the manifest and honour it, and now gates that **exactly
one arrangement is visible per set** in all five visibility modes. The warning
we wrote for other people's runtimes was reproduced by a button in our own
panel, which is the cheapest possible place to have found it.

**That PR took three review passes and produced seven findings, all ours.**
Every one was a version of the same thing — the manifest might not be what I
expect — and the last was the sharpest: `_presence()` claimed *"validated, not
assumed"* while still indexing two keys it never checked. Rules 24, 25 and 26
below all come out of it. It is the most-reviewed PR in this ladder and the one
worth reading before writing the next gate.

**A gate can be right and still not cover the failure.** The office rug
shipped **invisible** — 1/2" thick, resting at zero, under a 3/4" floor finish,
so the floor closed over it ([#79](https://github.com/captproton/yardstake-ux/pull/79)). Eleven gates missed it, and the two
that look like they should have caught it were each correct: the clearance gate
deliberately excludes `Floor_`, because every piece of furniture rests on the
floor and treating that as a clash would fail all forty; and the
floor-to-ceiling gate only asks whether `z0` is above zero, which `0.000` is.
The real failure mode was narrower than either — a piece **thinner than the
finish** — and needed its own gate rather than a widening of theirs. Found by
opening Blender and noticing something was not there.

**A gate that has never failed is a claim, not a check.** [#74](https://github.com/captproton/yardstake-ux/pull/74) shipped
`verify_mounted.py` with two checks that **could not fail** — one compared the
declared height against the fixture's whole bounding box, a span of nearly a
foot; the other tested the lens against a set that already contained the lens.
Review caught both. They are now bounded against the canopy mesh and the shade
mouth, and the repair was **proved by perturbation**: a canopy moved 4" and a
lens dropped a foot both pass the old gates and fail the new ones. Do that to
any gate you are tempted to trust.

**That claim was made once before and was wrong.** After [#67](https://github.com/captproton/yardstake-ux/pull/67) the plan
said the build half was complete while the tub/shower and the stacked washer/
dryer were both measured and unbuilt. `verify_geometry.py` exists so the claim
is checkable rather than asserted — **run it before ever saying "complete"
again.**

**Tiers 1 and 2 are complete bar KTX2 compression**, which is optimisation
rather than necessity. Tier 3's *build* half is done: cabinets, counters,
backsplash, uppers, hood, the kitchen sink and tap, and the bath vanity with
its basin, three-hole tap and mirror. `lod0` is now **907.2 KB** against a 4 MB
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

**Nothing in Tier 3 was ever bought.** The appliances and the toilet, once
listed here as the *buy* half, were built from the same primitives as
everything else. What is left is furniture and an appliance-finish variant —
see [What remains](#what-remains).

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

Run [`../views.py`](../views.py) once from Blender's Scripting tab:

```python
exec(open("/full/path/to/views.py").read())
```

That registers a **sidebar panel** — press **N** in the 3D viewport and pick the
**ADU** tab. Eight buttons:

| Camera | Visibility |
|---|---|
| `kitchen()` · `bathroom()` · `front()` | `full()` · `dollhouse()` · `cutaway()` · `walkthrough()` · `interior_only()` |

The three camera presets ([#71](https://github.com/captproton/yardstake-ux/pull/71)) **measure the model** rather than
carrying coordinates — the bath from the `Floor_bath` footprint, the kitchen
from the room plus counter depth, `front()` from the model bbox and the render
aspect — so they follow the building instead of rotting when a partition moves.
Each also leaves a scene camera called `View_preset`, so **Numpad 0** looks
through it and the framing can be rendered rather than nudged. `front()` is the
one worth doing that with: the viewport is a different shape from the render, so
the building looks smaller in the viewport than in the frame.

None of it touches geometry or materials, so **none of it can affect an
export**. Or skip it entirely and press **Shift+`** in the viewport to walk
around with W/A/S/D.

`walkthrough()` deliberately hides nothing — standing in a room you want the
ceiling above you. Hiding the roof and ceilings is right for looking *down*
into the model and wrong for walking through it.

## Running the gates

**It matters which runner and which scene, exactly as it matters which file you
open.** Every script names its own in its docstring; this table is here so no
one has to open nine files to find out, and because getting it wrong has
already produced two false reports about working code.

| Script | Run it with | Against |
|---|---|---|
| `verify_fixtures.py` | **`python3`** — spec only, no Blender | *(no scene)* |
| `verify_front_elevation.py` | `blender --background` | **`barn_cabin_524_textured.blend`** |
| `verify_tier1` `tier2` `openings` `geometry` `mounted` `furniture` `views` | `blender --background` | `barn_cabin_524.blend` |

Two traps, both sprung for real:

- **`verify_fixtures.py` is not a Blender script.** Its `import yaml` is
  correct for `python3` and fails under Blender, whose bundled Python has no
  PyYAML. Run it the wrong way and a **passing 49-gate suite looks broken** —
  which is exactly how it got filed as a defect in this plan, and retracted in
  [#87](https://github.com/captproton/yardstake-ux/pull/87).
- **`verify_front_elevation.py` needs the textured blend**, because glazing
  does not exist until `finish_adu.py` runs. Against the base file it used to
  report `Glazing_D-FRONT_lites missing` — indistinguishable from the entry
  door having regressed to a slab. It now refuses that scene with `[ABSENT]`
  and **exit code 2**, distinct from a real failure's **1**.

A green suite means all nine, each run its own way. Anything else is a claim.

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

**Use `barn_cabin_524_lod2.glb`** (29.6 KB, 24 nodes). It is the massing: no openings, no
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

**Stability guarantee, and it has now been broken once.** Origin, axes and
units are frozen and have never moved. `lod2` contents changed deliberately
**once**, in [#69](https://github.com/captproton/yardstake-ux/issues/69), for the foundation variant above — a
conversation first and a commit second, which is what this guarantee asks for.

> ⚠️ **And accidentally once, in [#98](https://github.com/captproton/yardstake-ux/pull/98).** Welding five pairs of
> objects for mesh headroom, three of the five turned out to live in the
> `shell` and `roof` collections `lod2` keeps: `Dormer_cheek_`, `Roof_dormer_`
> and `Eave_band_`. **Your file went from 24 nodes to 21, and three names you
> may address went away**, while that PR's body said `lod2` was untouched. The
> massing never differed — 1464 verts, 744 tris, identical bbox — but the
> interface did, and the interface is the part with the promise on it.
>
> **Reverted in [#99](https://github.com/captproton/yardstake-ux/pull/99).** `lod2` is byte-identical to its pre-#98
> state, sha `44276d83` before and after. **Nothing you hold needs changing.**

**The promise is now a gate.** `spec.export.lod2_contract` declares all 24 node
names; `finish_adu.py` compares the exported list against it and **fails the
build** on any difference, naming what went and what arrived. It **fails
closed** — a missing or empty contract is a failure, not a skip — and it runs
**before anything is written**, which is why `lod2` is built first of the three
levels. A rejected build leaves every file in `export/` exactly as it was.

What #98 and #99 cost, in one line each: the first changed your file with
nothing objecting, and the second made "nothing objecting" impossible. Changing
`lod2` is still allowed, and still a conversation first — but now it is a
conversation, then `spec.export.lod2_contract`, then the commit, in that order,
because the build refuses the other orders.

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

Tiers 1 and 2 are complete bar one optimisation, the foundation is built and
measured ([#70](https://github.com/captproton/yardstake-ux/pull/70)), and
**TIER 3 IS COMPLETE** — furniture was the last unbuilt item and shipped in
[#77](https://github.com/captproton/yardstake-ux/pull/77).

That sentence has been wrong before. After [#67](https://github.com/captproton/yardstake-ux/pull/67) this plan said the build half
was done while the tub/shower and the stacked washer/dryer were both measured
and unbuilt. It is safe to write now only because `verify_geometry.py` and
`verify_furniture.py` both pass, and both test POSITION rather than names.
**Next, in order.** Two small items came out of [#81](https://github.com/captproton/yardstake-ux/pull/81)
and were deliberately held out of it rather than widening a PR that was already
on its third review:

1. ~~**Dedupe `inside_mesh`.**~~ Shipped in
   [#82](https://github.com/captproton/yardstake-ux/pull/82). Two copies, one
   bug, two fixes — the only case this session where the *structure*
   manufactured a second defect rather than merely failing to prevent one. The
   extraction then manufactured two more of its own, both dead: an import the
   move had orphaned, and a parameter the table never read. Neither was caught
   by running anything; both were caught by reading, once by a peer session and
   once by the reviewer. **`grep` reported the orphaned import as used**,
   because `__import__("mathutils").Vector` contains the string — it took
   parsing the file to see that no bare name was referenced. When a symbol
   looks alive, check what is actually referencing it.
2. ~~**[#80](https://github.com/captproton/yardstake-ux/issues/80) — the front
   elevation.**~~ Shipped in
   [#83](https://github.com/captproton/yardstake-ux/pull/83). The measurement that had failed twice landed on
   50.000 px/ft at the third attempt, and the reason it kept failing is worth
   more than the number: every opening on that sheet is drawn as a NEST of
   symmetric rectangles, and WHICH one is the size callout depends on the
   type. A window's callout is the second level in; a door's is the third,
   because a 3'-0" leaf sits inside a 3'-3" frame inside the casing. Reading
   the door by the window rule gives 39", and one level further out gives 46"
   — which is 44.3 px/ft, the exact figure the earlier attempt published. The
   two readers are now deliberately opposite and say so.
   The door turned out not to be missing a feature: it had a working glazing
   slot that a single ternary blanked by renaming the pane. And the front
   gable, the face `views.front()` frames, had no window in it for eleven PRs.
   Review then caught the same mistake being made a second time, quieter: the
   new code chose the half-lite builder by asking whether a `construction`
   block was PRESENT rather than what the opening's `type` SAID. Both call
   sites now dispatch on the declared type, and a half-lite typed with nothing
   to build it from raises instead of falling back to a slab — a silent
   fallback is how that door spent eleven PRs as two flat boxes.
**Both are shipped, so the queue is now the backlog below** — with three items
found while building [#83](https://github.com/captproton/yardstake-ux/pull/83)
and deliberately left out of it:

- ~~**`verify_tier2`'s UV gate has been failing on `main`.**~~ Fixed in
  [#86](https://github.com/captproton/yardstake-ux/pull/86), and **the entry
  above was wrong in three ways** — worth recording, because each error came
  from describing a gate rather than running it.
  It never failed in its **documented invocation**: `verify_tier2.py` says to
  run against `barn_cabin_524.blend`, and that passes on 105 meshes. It failed
  only against a scene carrying glazing, which `finish_adu.py` adds. So the
  gate was not chronically red — it was **pointed at a file holding none of the
  objects it trips on**, which is a coverage hole and a worse problem. It was
  **11 meshes, not sixteen**; that figure reproduces in neither file. And
  nothing was hiding behind the red: no mesh lacked UVs while carrying a
  texture.
  **The obvious fix was a trap, and this is the part worth keeping.** "Exempt
  anything untextured" is the natural repair. Eleven meshes lack UVs — and
  **74 meshes carry UVs while using untextured materials**, so that rule drops
  all 74 out of the gate. A visible false alarm traded for invisible lost
  coverage. Only checking the INVERSE case showed it.
  One gate is now three, and the exemption is declared in
  `spec.texturing.uv_exempt_materials` rather than inferred: every
  image-textured mesh must carry UVs; a mesh may skip them only if every
  material on it is listed; and the list must name real `materials.library`
  keys. Naming the **material** rather than the `Glazing_` prefix is the point
  — the exemption ends the day glass gains a texture.
- **RETRACTED — `verify_fixtures.py` runs perfectly well.** The entry here
  claimed it "cannot run in Blender at all" because of a bare `import yaml`.
  It was **wrong, and the error was mine**: `verify_fixtures.py` is not a
  Blender script. Its docstring says so in plain words — *"Run it with plain
  Python; Blender is not needed"* — and `python3 verify_fixtures.py` gives
  **49/49 ALL PASS**. I ran it under Blender, watched it fail on an import that
  is correct for its actual runner, and reported a working suite as broken.
  That claim reached [#86](https://github.com/captproton/yardstake-ux/pull/86)'s
  body and this plan before it was checked.
  **This is rule 28, committed by the person who had just written rule 28** —
  a right question asked of the wrong environment, an hour after recording that
  exact trap. It also wrongly cast doubt on
  [#85](https://github.com/captproton/yardstake-ux/pull/85)'s claim that
  fixtures passes 49/49; that claim was correct. Kept here rather than deleted,
  because a retracted finding is evidence about how findings get made.
- ~~**`verify_front_elevation` only passes against a scene with glazing.**~~
  Fixed in [#87](https://github.com/captproton/yardstake-ux/pull/87). This half
  was real: the docstring named `barn_cabin_524.blend`, where glazing does not
  exist — `finish_adu.py` adds it — so the suite reported
  `Glazing_D-FRONT_lites missing`, which reads exactly like the door having
  regressed to a slab. The docstring now names the blend that can answer, and
  `main()` **refuses the wrong scene** with an `[ABSENT]` notice and exit code
  2, distinct from a real failure's 1.
  **The guard's discriminator is deliberately narrow**, and that is the part
  worth reading. Aborting whenever the door's lites are missing would have
  silently destroyed the gate that catches a door with no glass — the exact
  defect [#83](https://github.com/captproton/yardstake-ux/pull/83) fixed. So it
  tests for **no glazing anywhere**: none means `finish_adu.py` never ran here;
  some, but not the door's, is a real finding and falls through. Both proved by
  lesion — deleting only the door's lites still FAILS, deleting all glazing
  reports ABSENT.
- ~~**Exterior casing is modelled on no window at all, and on no door
  either.**~~ Shipped in
  [#89](https://github.com/captproton/yardstake-ux/pull/89), together with the
  sash divisions every window's `type` had declared and nothing built. Both
  halves of [#88](https://github.com/captproton/yardstake-ux/issues/88).
  **The measurement corrected the issue that raised it.** #88 predicted the
  sash split would need `confidence: assumed`, from a tour photo that read
  "nearer 60/40 than an even split" by eye. A1.1 draws the rail, and the
  reader that calibrated the sheet resolves it at **50.3%, 50.2% and 50.0%**
  on windows 36", 60" and 36" tall. Three heights agreeing to a third of a
  percent is the evidence; the eyeball was wrong and the sheet is not vague.
  The mullion measurement then **confirmed the declared types from a sheet
  that did not set them** — `W-LIVING-S1` shows a vertical on its centreline,
  both single-hungs show none — which also reconciles the photo: the left
  window reads two-wide-by-two-high because it is two single-hung units each
  split 50/50, not one unit with an off-centre rail.
  Casing came off the same sheet, and one number could not: a sill's
  PROJECTION points at the viewer, so an elevation foreshortens it to nothing.
  It is `confidence: assumed` at 1 1/2" with `what_would_settle_it` naming the
  section drawing that would fix it.
  **The mesh cap held.** Eleven casing objects took `lod0` from 116 to 126
  against a cap of 120 — set in this model's first commit, unmoved for twelve
  PRs. [#84](https://github.com/captproton/yardstake-ux/pull/84) kept a
  doorknob inside it by welding rather than raising it, so #89 welded too:
  one `Trim_ext` run, and the number in the gate did not move.
- **The rear gable has NO window, and that is now checked rather than assumed.**
  Asked directly whether the model was missing one, the REAR ELEVATION was read
  off the sheet: plain lap siding to the ridge, no opening. The only window on
  that face is the main-floor egress slider, which is built. This plan
  previously asserted it inside the ridge-beam note, on no stated evidence.
- **The gable window: the sheet contradicts itself.** A1.1's LOFT plan labels
  it `2'0" X 3'0" FXD` — fixed, so no meeting rail — while A1.1's FRONT
  ELEVATION draws that same window WITH a rail, and the tour frame shows it
  built with one. Two of three sources say divided, so the model follows the
  elevation and the as-built. Filed as
  `discrepancies.gable-window-fixed-on-the-plan-operable-on-the-elevation`,
  because `spec.openings` carries `raw: 2'-0" x 3'-0" S.H.` sourced to the
  elevation with nothing saying the plan disagrees. **Turned up by asking about
  the rear gable** — the question that had nothing to do with it.
- **The loft egress casement is confirmed on screen, not only in the
  narration.** `discrepancies.loft-egress-window` rested on the 6:26 audio.
  Loft frames now show the unit as a single tall light with no mullion and no
  rail, with crank hardware on the stool — an outswing casement. They also show
  what the audio did not: **the two dormer walls do not match.** One carries a
  band of two divided units, consistent with the plan's paired X/O sliders; the
  other carries the single casement. The swap was made on one side, for egress,
  where the plan draws four identical units.
  A casement is NOT a slider with the mullion removed — it swings, so an open
  state needs a hinge axis and a sash that leaves the opening plane. That is
  why `spec.windows.types` has no `casement` entry rather than a half-built one.
- **The drawn front door and the built one disagree.** A1.1 gives six lites in
  two columns by three rows over one square panel; the tour shows three columns
  by two rows over two tall panels, in mustard yellow. Same building — the 0:13
  frame carries the shingled gable, the gable window, the porch and the sconce.
  Filed as `discrepancies.front-door-face-differs-from-the-built-unit` and
  resolved the way this project already resolved the bedroom door the plans do
  not have: **model the plans**, keep the as-built face as a candidate
  `presence` option. The gates test the DRAWN arrangement on purpose.
- **The sheet contradicts itself at the ridge, and the model is right.** A1.1's
  dash-dot "TOP OF ROOF" leader sits at z 17.32 while its own drawn apex is at
  z 17.91 — seven inches apart. P3 chose the apex on independent evidence and
  the build follows it. Recorded in `tools/tier3/front_elev.py` so the next
  reader does not re-derive it as a defect. **No action wanted.**

- **The loft ladder is built from the builder's own transcript, and five
  refinements are open.** [#95](https://github.com/captproton/yardstake-ux/issues/95) said it did not look real, and
  it did not: two bare stringers with boxes floating between them. The rebuild
  in [#96](https://github.com/captproton/yardstake-ux/pull/96) follows `example plans/thataduguy/Loft Ladder.rtf`
  step for step — 1"×3½" clear vertical grain Douglas fir, **20° for both the
  heel cut and the dados**, nine rungs at 12", top tread level with the loft
  floor, rails running 3 ft past it as handles with 1" radius tops, and a ½"
  slide rod on an elbow and flange.
  **The rake gate had to stop measuring the bbox.** A ladder with a flat foot
  and a radiused top has a bounding box whose diagonal is not its rake, and
  the topmost vertex is on the radius. It now measures the **straight back
  edge** and reads 19.98°.
  ~~[#97](https://github.com/captproton/yardstake-ux/issues/97) carries what review found and the mesh cap
  deferred.~~ **Shipped in [#100](https://github.com/captproton/yardstake-ux/pull/100)**, and it grew well past its
  six items.
  **The rungs were laid out on the wall, not the board.** `zz = loft_sf - k*rs`
  steps a foot of HEIGHT, which at 20° is 12.77" along the rail; the top rung
  is pinned, so the error accumulated downward and the bottom rung finished
  about 6" low. The tape in the video is clamped to the rail.
  **The top tread then went wrong in the mirror.** #97 said it was level by
  its CENTRE, leaving the face 11/16" proud; the fix moved it to the top face
  but onto the SUBFLOOR, leaving it 3/4" below the surface you step on. Review
  caught that. It is `Floor_loft`'s own top face now — read off the object,
  not recomputed.
  **The rungs are the same 1"×3½" fir as the rails**, so they are treads and
  not sticks. Sourced to the project owner and said so: the transcript
  dimensions only the RAIL stock at 0:44 and never dimensions the rungs, and
  attributing it to the footage would have invented a line that is not there.
  **The dado is a recess now**, two laminations with the inner one interrupted
  at every rung, clipped Sutherland-Hodgman so the flat foot and the radiused
  top survive.
  **And the ladder was inside the building.** A person found it by looking at a
  render: the top 10" of both rails ran inside the loft floor slab, 3.84" past
  its face on a board 3.5" deep. Two errors pushing the same way — the ladder
  was placed by putting the rail's CENTRE LINE on the partition face, and the
  loft floor overhangs that wall by 1 3/4". **Every ladder gate measured the
  ladder against itself**, so a perfectly built ladder buried to its shoulders
  passed all of them. That is rule 31, and it is now a gate.
- **`spec.yaml` has no CODEOWNERS protection, and the `lod2` contract asks for
  it.** Copilot's second pass on [#99](https://github.com/captproton/yardstake-ux/pull/99) made a fair point: the
  contract's baseline and the thing it gates live in the same editable file, so
  a commit that welds a node and updates `lod2_contract.nodes` together passes.
  That is by design — **no gate can stop a deliberate edit to its own
  baseline**; what it guarantees is that the edit must EXIST, be visible in the
  diff, and be refusable. #98 changed the handoff while touching neither.
  Making it unforgeable wants CODEOWNERS or branch protection on `spec.yaml`,
  which is a repo-settings decision rather than a code one. **Not taken
  unilaterally; it is @captproton's call.**

**Deferred, with the reason recorded so it stays a decision rather than an
omission:** the `main()` split in the verify scripts and a `Box` value object.
Both are genuine improvements to code that will be read for a long time, but
classifying this session's twenty-five defects put only three in the
duplication bucket — neither refactor would have prevented what actually bit
us, and doing them now means a large no-behaviour-change diff across every
verify file. Revisit when a third caller needs one of them.

**Next, and it is not close.** Every opening item is now shipped, so the
largest remaining piece of work is also the only one a homeowner would ever
see: **wire the pickers.** `variants.json` already carries both kinds — 8
material `sets` and 3 `presence` sets — with a working `applyChoice()` and
`applyLayout()` written out in TIER-2. Nothing in the model blocks it. It is
the step where twenty PRs of geometry become something a buyer can click.

**Two gate issues are now open and should be read before the next gate is
written**, because both came out of work that looked finished:

- [#92](https://github.com/captproton/yardstake-ux/issues/92) — `lod0` is at
  **117 of 120 meshes**, and instancing will NOT help: the cap counts objects.
  Welding is the only lever, its constraint is naming rather than geometry —
  **and naming is not the only constraint.** See the corrected entry below:
  #98 took five welds on a naming analysis alone and three of them were in
  `lod2`, which no amount of name-scanning would have revealed.
- [#94](https://github.com/captproton/yardstake-ux/issues/94) — the bypass
  gates ask a two-dimensional question one axis at a time, which is why
  [#93](https://github.com/captproton/yardstake-ux/pull/93) needed five review
  passes for fourteen findings. It carries the nine lesions those passes
  produced as a regression suite; a rewrite that does not fail all nine is not
  a replacement.

Two smaller items are worth naming because they are now more interesting than
when they were filed:

- **The mesh cap is at 117 of 120, and it is now its own issue:**
  [#92](https://github.com/captproton/yardstake-ux/issues/92).
  **CORRECTION — this entry previously said instancing "buys the headroom the
  next fixture will need". IT BUYS NONE.** The gate counts OBJECTS:
  `len([o for o in bpy.data.objects if o.type == "MESH"])`. Instancing shares
  one mesh datablock between several objects; the datablock count falls and
  the object count does not move. Measured **at the time, when the count was
  118: 118 objects, 118 datablocks** — nothing was shared, and sharing
  everything shareable would still have left 118 objects. The argument does not
  depend on the number and the number has moved since. The claim was written from what instancing is *for* rather than
  from what the gate *counts*, which is rule 29's mistake in prose.
  Instancing is still worth doing for file size and GPU memory — there are 12
  groups of geometrically identical meshes — but **welding is the only lever
  that moves this cap.**
  **SECOND CORRECTION, from [#98](https://github.com/captproton/yardstake-ux/pull/98): the "three genuinely safe
  welds" this entry used to recommend were not safe, and the "40 free slots"
  was not 40.** That analysis classified an object as free if no gate named it
  exactly or built it with an f-string, and missed two things — gates match
  distinguishing SUBSTRINGS (`verify_mounted` finds the sconce's canopy by
  looking inside names), and nine whole families are addressed individually by
  f-string. Re-measured, the genuinely free welds were worth **8 slots, not
  40**.
  **Then #98 took its own advice and got it wrong a third way.** Three of the
  five welds it shipped were in `shell` and `roof` — collections `lod2` keeps —
  so it changed the placement developer's handoff to save two slots. Reverted
  in [#99](https://github.com/captproton/yardstake-ux/pull/99).
  The lesson is not "scan harder". It is that **the constraints on a weld are
  not all in the names**: a name-scan cannot see collection membership, cannot
  see that a mesh spans two rooms, and cannot see a stability guarantee. The
  remaining welds want a judgement per group. At 117 of 120 there are three
  slots, and [#94](https://github.com/captproton/yardstake-ux/issues/94) carries the nine in `Win_` — the only large
  win left, and it is locked behind the same rectangle-vs-projection gate
  redesign.
- **The loft casement**, now that the frames confirm it. It is the second half
  of a recorded discrepancy and exactly the kind of as-built alternative the
  picker work would want to offer — but see the warning above about what a
  casement actually requires.

In order of value:

| Work | Notes |
|---|---|
| **T3:** appliance finish variant | The two filmed units differ (white fridge at 2:11, stainless at 2:27), so finish is a choice. Bodies and fronts are already on one material, so this is a `spec.variants` entry and no geometry |
| **T3:** mounted fixtures beyond the sconce | The porch light landed the `spec.fixtures.mounted` anchor and a `_lib`-candidate form ([#74](https://github.com/captproton/yardstake-ux/pull/74)). The mini-split head, meter panel, tankless heater and heat pump are all wall- or ground-mounted and all sit in `fixtures.not_measured` — they now have somewhere to go, but not one of them is drawn with a height |
| **Export:** mesh instancing | **For file size and GPU memory, NOT for the mesh cap — see [#92](https://github.com/captproton/yardstake-ux/issues/92).** The cap counts objects, and instancing does not change the object count. `lod0` is 117 scene objects and **117 distinct meshes** — nothing is shared, so `Porch_post_1`/`_2`, the closet door pair and all four loft windows are each paid for twice or more. glTF supports many nodes to one mesh natively and Blender does it with linked duplicates. A win on geometry *already shipped*, and the thing that makes a fixture catalogue cheap. Held out of [#74](https://github.com/captproton/yardstake-ux/pull/74) deliberately: no payoff for one sconce, and it would have hidden an exporter change inside a lighting PR. Belongs with the `_lib` split |
| **T2:** KTX2 compression | Optimisation, not necessity — `lod0` is 960.2 KB against a 4 MB ceiling. Confirm `gltf-transform` is installed first |
| **Foundation:** vent height | The only part of the foundation still assumed. A2.0 draws the vents in *plan*, so it cannot give their height; A1.1's elevations draw no vents at all and show 5-3/4" of exposed concrete, which is schematic since an 8" vent does not fit in it. The 8" height and 4" drop below the top of foundation are ours, labelled `confidence: assumed` |
| **Foundation:** vents in `lod2` | `Found_stemwall` is in the porch collection, so the placement developer's massing carries eight openings through it. Accurate, and harmless at 29.6 KB against a 200 KB ceiling, but it is detail they did not ask for. Filling them in `lod2` is a two-line change to the `cut_openings` branch that already strips windows and doors |
| **UI:** wire the pickers | **The largest open item, and the only one a homeowner would notice.** `variants.json` now carries both kinds: 8 material `sets` and 3 `presence` sets, with a working `applyChoice()` and `applyLayout()` in TIER-2. Nothing in the model blocks it — and `presence` is the half that *must* be honoured, since ignoring it renders a desk through a bed ([#78](https://github.com/captproton/yardstake-ux/pull/78)) |

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
20. **Tooling needs gates too, and a gate is code that can be wrong.** Every
    defect in the camera presets ([#71](https://github.com/captproton/yardstake-ux/pull/71)) was found by LOOKING AT A
    RENDER — a cropped foundation, a camera inside the vanity, a "kitchen"
    spanning three rooms. None announced itself; all three looked plausible.
    Worse, two of the gates written to catch them were themselves wrong first
    and failed on CORRECT behaviour: one trusted a merged mesh's bounding box,
    the other started from a mode that only changes visibility, so nothing
    moved. Write the gate, then make it fail on purpose.
21. **A house convention can be the wrong answer.** `build_adu` merges by
    material across the whole building, which is right for anything always
    present and wrong for anything switchable: `Appl_body` is ONE mesh holding
    the fridge, the range, the dishwasher and the bedroom-closet washer/dryer,
    and furniture built that way could never be hidden one arrangement at a
    time. Furniture therefore merges only WITHIN an arrangement ([#77](https://github.com/captproton/yardstake-ux/pull/77)).
    That same shared-mesh property has now cost this project three times — a
    tautological geometry gate, a camera framing three rooms, and nearly an
    unswitchable furniture set. When a convention meets a requirement it cannot
    serve, break it deliberately and gate the break.
22. **Extend a schema beside itself, not through itself.** `variants.sets`
    swaps materials, with `targets` at set level; a presence swap needs its
    targets PER OPTION. Folding it in would have made `targets` mean
    "materials, unless the property is visible, in which case ignore this" --
    an overload that reads as a bug later. A sibling `presence` block kept both
    shapes honest and made the change purely additive: a runtime that knows
    only `sets` still works ([#78](https://github.com/captproton/yardstake-ux/pull/78)). The cost of the sibling is one more
    concept; the cost of the overload is every future reader.
23. **A correct gate can still leave the hole uncovered.** The office rug
    shipped invisible, buried inside the floor finish, past ELEVEN furniture
    gates ([#79](https://github.com/captproton/yardstake-ux/pull/79)). The two that look like they should have caught it were
    each right to behave as they did — the clearance gate excludes `Floor_`
    because everything rests on the floor, and the floor-to-ceiling gate only
    asks whether `z0` clears zero. Widening either would have broken it. When a
    defect slips a suite, ask whether the existing gates were WRONG or merely
    aimed elsewhere; if elsewhere, the answer is a new gate written against the
    failure mode — here, thickness against the finish — not a looser old one.
24. **Write the gate against the failure mode, not the healthy state.** These
    all passed while the thing they named was broken: *has glazing* passes on a
    single pane where six lites are drawn; *is a subset of what is visible*
    passes on the empty set, and then FAILS on a correctly chosen "unfurnished";
    *furniture sits above z=0* passes on a rug buried inside the floor finish.
    Each predicate described **a** correct state rather than **the** thing that
    could go wrong. Say aloud what breaking looks like, write the predicate to
    reject exactly that, then break that exact line to prove it — a red test
    aimed at the wrong line is indistinguishable from a gate that cannot fail,
    and one of those in [#81](https://github.com/captproton/yardstake-ux/pull/81)
    reported ALL PASS on code written to be broken.
    *Applies to the gate's own fixtures too.* The schema gate manufactures
    malformed manifests, and its duplicate-id case was built by copying an
    option — which copies the `default` flag as well, so the case was caught by
    the exactly-one-default rule while the duplicate-id rule it was named for
    never ran. **A fixture broken in two ways only tests the first.** Break one
    property at a time, or the gate reports on a rule it never reached.
25. **Anything read from disk is untrusted input, including files this project
    writes.** `views.py` reads `export/variants.json`, which `finish_adu.py`
    produces — and every one of six findings in
    [#81](https://github.com/captproton/yardstake-ux/pull/81) was some form of
    "the manifest might not be what I expect": no schema check, no option-id
    validation, a warning that fired on every redraw, a re-parse inside the UI
    loop, an assumed `sets[0]`. The docstring said *degrades gracefully* while
    the code handled only the failures its author had imagined. Validate the
    shape, degrade WHOLE rather than partially — a half-applied config is worse
    than none — and treat "we generated this file ourselves" as no guarantee at
    all.
26. **Derive the schema from what the code indexes; do not list the keys you
    happen to think of.** Rule 25 was applied and still got this wrong one
    level down: `_presence()` validated `id`, `options` and `show`, carried the
    comment **"VALIDATED, NOT ASSUMED"**, and left `label` and `default`
    subscripted unconditionally — so a manifest missing either raised out of
    the panel's `draw()` and left the sidebar blank. The fix was mechanical
    rather than clever: grep every unconditional subscript across the consumers
    and require exactly that set. Three things follow.
    *A key can carry an invariant, not just a type.* Three call sites did
    `next(o for o in options if o["default"])` with a bare `next()`; zero
    defaults raises `StopIteration` mid-redraw and two silently take whichever
    came first. Checking **exactly one** once, in the validator, is what makes
    all three safe — cardinality belongs with the schema, not at each use.
    *The silent malformations are the dangerous ones.* Of twelve cases, the
    nine that raise are the benign half: a blank sidebar is loud and gets
    fixed. Two defaults, or duplicate ids, raise nothing at all and simply
    apply one arrangement while reporting another — the wrong-answer-reported-
    as-right failure this file had already shipped once.
    *A false claim in a comment is worse than no comment.* "Validated, not
    assumed" is what the next reader trusts instead of re-checking. If the
    docstring makes a promise, the gate must be able to break it.
27. **When you relax a gate, measure what the relaxation excuses — not what it
    was going to fix.** `verify_tier2`'s UV gate was red on eleven glazing
    meshes, and the natural repair was *exempt anything untextured*. Correct
    for those eleven, and it would have dropped **74 more** out of the gate,
    because 74 meshes carry UVs while using untextured materials. A visible
    false alarm traded for invisible lost coverage — strictly the worse of the
    two, since nobody comes back to check a gate that went green. **Count the
    inverse set before you widen a predicate**; the number that matters is not
    how many failures the change silences but how many passes it stops
    testing. Then declare the exemption where a reader will find it
    ([#86](https://github.com/captproton/yardstake-ux/pull/86) puts it in
    `spec.texturing`) and tie it to the MATERIAL rather than the name prefix,
    so the exemption expires the day its premise does.
28. **A gate aimed at a scene that cannot contain its subject passes
    vacuously.** Two of these on `main` at once. `verify_tier2`'s UV gate was
    described in this plan as "failing on `main`", but in its documented
    invocation — against `barn_cabin_524.blend` — it PASSED, because glazing is
    added later by `finish_adu.py`; it only failed when pointed at a different
    file. `verify_front_elevation` has the mirror problem: it can only pass
    against a scene *with* glazing, and reports `Glazing_D-FRONT_lites missing`
    on the base `.blend`. Neither is a wrong predicate; both are right
    questions asked of the wrong file. **Every verify script must name the
    scene it targets in its docstring, and a gate whose subject is absent
    should say ABSENT rather than pass or fail** — an empty subject is the same
    trap as the empty set in rule 24. Related: three of the numbers in this
    plan's own backlog were wrong because the entry was written from reading
    the gate instead of running it.
    *The rule caught its own author within the hour.* `verify_fixtures.py` was
    filed in the backlog as unrunnable, because it was run under Blender — when
    its docstring says plainly to run it with `python3`, where it passes 49/49.
    A right question asked of the wrong ENVIRONMENT is the same error as the
    wrong scene, and it produced a false report about a working suite. **Before
    filing a gate as broken, run it the way its docstring says.**
    *An absent subject now has its own exit code.*
    [#87](https://github.com/captproton/yardstake-ux/pull/87) gives
    `verify_front_elevation` exit 2 for "wrong scene" against 1 for a real
    failure — a distinction the suite could not previously express, and the
    reason a misrun could masquerade as a defect. Its guard tests for **no
    glazing anywhere**, never for the one object it is about to gate on;
    aborting on the latter would have deleted the gate that catches a door with
    no glass.
29. **A gate derived from the build's own expression cannot disagree with the
    build.** [#89](https://github.com/captproton/yardstake-ux/pull/89) placed
    the gable window's sash on the WALL datum when its gable is a prism at
    y 0..t — six feet from its own glass, floating inside the porch — and
    **every sash gate passed it.** Two reasons, and both generalise. The
    composition checks sampled at the object's OWN mid-depth, so a sash on the
    wrong datum is internally perfect: correct jambs, correct rail, correct
    lights. And `sash_targets()` mirrored `build_adu`'s call sites for
    tidiness, so it inherited the identical wrong plane. A gate that asks only
    *is this well-formed* can never answer *is this in the right place*, and a
    gate that recomputes the build's arithmetic tests only that Python is
    deterministic. **Check placement against something the build did not hand
    you** — here the HOST solid the opening is cut into, which #89's gate now
    reports on every pass line rather than only on failure. `verify_openings`
    already knew this: its own header says the volume test earns its keep
    because "these three levels are re-derived here rather than imported".
    *And the same PR shows the cheap half of the lesson.* Two further defects
    were mine and both were caught within minutes: a DOOR given a window sill,
    running to z -0.47 buried in the porch slab, because casing was shared
    between doors and windows and what sits UNDER an opening is not; and a
    mullion sampled at mid-height, which is where a meeting rail crosses it —
    a degenerate point for a surface test and, worse, a point a rail ALONE
    could satisfy. Sample a member where it is the only explanation.
    *Rule 29 then held for a third and fourth time, in
    [#90](https://github.com/captproton/yardstake-ux/pull/90).* The sash was
    built entirely OUTBOARD of the glazing plane, so the divisions read from
    the garden and the same window was one flat pane from the sofa — glass is
    drawn before whatever sits behind it. Every gate in #89 passed it, because
    all of them ask what the members ARE and none asked which SIDE of the glass
    they are on. Then the stool and apron landed a casing-depth off the wall on
    every wall whose room lies in the negative direction, and the stool gate
    passed that too, because it asked only whether anything sat below the sill.
    **Four placement defects in two PRs, every one of them through a
    composition gate.** In this codebase, if a gate checks what a thing is,
    assume nothing checks where it is.
    *A shared helper is where orientation bugs hide.* The root cause of the
    stool defect was that `plane` means the wall FACE on a +Y room and the face
    minus `cd_` on a −Y room. Every member that spans `plane .. plane + cd_`
    is immune whatever the orientation; only the two placed RELATIVE to the
    face broke. When a helper serves both orientations, the parameter that
    looks symmetric is the one to check.
30. **When a fixture and the thing it tests are the same shape, counting
    proves nothing.** A `single_hung` is four frame members plus a meeting
    rail. A `slider_XO` is four plus a mullion. **Both are five boxes and
    forty vertices**, so a vertex-count gate passes on either built as the
    other — the exact confusion this work could produce. #89's gate samples
    the POSITION of every member the type implies, and the centre of every
    light, requiring solid and air respectively; its `swap_type` lesion fails
    in BOTH directions, which is what proves the two types are distinguishable
    at all. Before counting anything, ask what else has that count.
    *A note can be written against the expected state too.* The same PR
    recorded that the apron is "narrower than the 3 1/2" casing", two lines
    below the measurements 3.60", 3.60" and 3.84" — all WIDER. The sentence
    survived because it was reasoning toward the conclusion its author
    expected, that the apron is the same 1x4 stock as the casing. Rule 24
    applies to prose: **a note that agrees with your expectation instead of
    your measurement is the one to re-read.**
31. **A gate that keeps its own copy of where something is cannot notice the
    thing moving.** [#91](https://github.com/captproton/yardstake-ux/pull/91)
    found the washer's control panel with `x > 8.0` — a number true of this
    layout and of nothing else. Move the closet and the gate quietly starts
    reading the KITCHEN's dark panels, and still passes. It now filters by the
    spec's own footprint through the same datum mapping the surrounding loop
    already uses, so the filter moves when the fixture does.
    **This is the fifth variant of one mistake in three PRs** — the gable sash
    on the wrong datum, the stool and apron off the wall, a gate mirroring the
    build's call sites, and now a gate carrying a hard-coded coordinate. Rule
    29 says a gate must check placement against something the build did not
    hand it; this says the gate must not invent that something either.
    *And a gate must not vanish with its subject.* The same PR guarded the
    control-panel half with `if dark is not None:`, so the moment `Appl_dark`
    disappeared — the exact regression worth catching — the check disappeared
    with it and the suite stayed green. **A missing subject is a failure, not a
    skip.** Compare rule 28, where an absent subject reports ABSENT: the
    difference is whether the subject is meant to be in this scene at all.
32. **Reach for the primitives before the download.** Asked to model a stacked
    washer/dryer, the offer on the table was to find a similar model or image
    online. This model contains NO third-party content: textures are
    procedural, geometry is spec-driven, and that property is easy to lose and
    impossible to recover quietly. Every "this must be bought" assumption in
    Tier 3 — the basin, the tub, the toilet, all three appliances — turned out
    to be `box`, `tube` and `loft`. A front-load stack is a box and two tubes.
    *When footage is the only reference, take PROPORTIONS from it and not
    dimensions.* The frames for this one came from a different video and may
    show a different unit, so every number is a fraction of the drawn box —
    drum diameter 0.68 of unit width, centre 0.46 of unit height — and the box
    still comes from the sheet. Change the box and the form follows it.
33. **When a gate is wrong because it measures a PROXY, find the property —
    do not hunt for a better proxy.**
    [#93](https://github.com/captproton/yardstake-ux/pull/93) took five review
    passes and produced **fourteen findings, every one in the gates and none in
    the geometry**. Two predicates absorbed nearly all of them, and each fix
    was the next-strongest measurement rather than the thing meant:
    *"the open bypass covers half its opening"* went hull → total length →
    contiguity → identity, and each earlier version passed a state the next one
    caught — a gap between the leaves, two strips at opposite ends, a
    contiguous run in the middle of the opening.
    *"the closed door conceals the laundry"* went Y-overlap → Y-overlap plus
    the X side of the partition. That second one is the sharper lesson: Y
    overlap was never a WEAKER form of the right question, it was a DIFFERENT
    question that happened to agree for the geometry that existed. **A test
    correct only because nothing has moved yet survives every review until
    something moves.**
    The shape underneath is one fault, not six oversights: a relationship
    between two RECTANGLES was being checked by comparing their
    one-dimensional projections separately, so every round found another
    projection nobody had checked. Asked as *does this rectangle cover that
    one*, there is no second axis to forget.
    [#94](https://github.com/captproton/yardstake-ux/issues/94) carries the
    redesign, with the nine lesions from those five passes as its regression
    suite — **if the rewrite does not fail all nine it is not a replacement.**
    *And know when to stop patching.* #93 began as a one-line behaviour change
    and ended at +359 lines across six files, nearly all gate repair, with the
    passes still finding real things. Merging a correct model and filing the
    redesign beat a sixth pass on a diff that size. When review findings stop
    being *wrong* and start being *incomplete in a new place each time*, that
    is the signal to change the shape rather than add another clause.

34. **A guarantee nothing checks is not a guarantee, and the commit message is
    not the check.** This plan said for twelve PRs that `lod2` must not change
    without a conversation. [#98](https://github.com/captproton/yardstake-ux/pull/98) changed it anyway — welding
    three objects that happened to live in the collections `lod2` keeps — and
    **every gate passed, because no gate was looking.** The only thing standing
    between the placement developer and a silently altered handoff was a
    sentence in a document and my assertion in a PR body that `lod2` was
    untouched. Both were wrong at the same time, which is what a guarantee
    without a check looks like from the inside: nothing objects.
    The promise is now `spec.export.lod2_contract` and a build gate.
    [#99](https://github.com/captproton/yardstake-ux/pull/99) reverted the welds and added it. **Three properties, and
    each was won by a review finding rather than by design:**
    *It fails CLOSED.* The first version guarded the comparison with
    `if contract:`, so deleting the spec block would switch the gate off
    silently — the same shape of mistake one level up. A missing contract is
    now a failure, not a skip.
    *It runs BEFORE the write.* The second version ran in the export report,
    by which time the handoff file had already been overwritten with the very
    node list the gate was about to reject. A gate that fires after publishing
    is not a gate. `lod2` is now built first of the three levels, so a rejected
    build leaves **every** file in `export/` as it was.
    *Its failure message had to be RED-tested too.* The third version's message
    said "the files on disk are still the last ones that passed" — true of two
    files, not the directory, because `lod0` and `lod1` had already been
    written. **I overclaimed in prose inside the very commit that existed
    because prose had been trusted over a check.** The RED test now fingerprints
    the whole directory rather than the two files I expected to matter.
    *And the RED test found a real bug the gate would have hidden.* Deleting
    the contract block leaves `export:` present and **null**, and
    `spec.get("export", {})` returns `None` for a key that exists and is null
    — the default only fires on a MISSING key. The gate crashed instead of
    failing. A traceback does stop a build, but it reports a broken script
    rather than a broken promise.
    **The general form: when you write down a guarantee, ask what would happen
    if someone broke it today.** If the honest answer is "the suite would pass
    and I would say so in the PR", the guarantee is prose. And when you then
    build the check, the check's own failure path — its default, its ordering,
    and the words it prints — is code that has never run, so break it
    deliberately before believing any of it.

35. **A LESION HAS TO BREAK THE BUILD WITHOUT TELLING THE GATE.** Rule 24 says
    break the line that makes each gate pass. [#100](https://github.com/captproton/yardstake-ux/pull/100) found the
    way that goes wrong: **three times in one PR I wrote a lesion that changed
    the SPEC**, and the spec is the gate's half of the comparison, so the
    expectation moved with the build and the gate passed. Each time the
    conclusion looked like "this gate cannot be broken", which is the most
    dangerous false reassurance a gate can give.
    *Rung count.* Set `rung_count` to 1 in the spec: one rung built, one rung
    wanted, PASS. The real lesion builds one while the spec still says nine.
    *Dado depth.* Set `dado_depth` to 3/16": the rail is cut shallow and the
    gate wants shallow, PASS. The real lesion halves it in the BUILDER.
    *Flange.* Same shape, caught before it shipped.
    **And a lesion can fail for the wrong reason, which is just as useless.**
    The gate for *"the ladder clears the loft floor edge"* was rewritten to
    test EDGES rather than vertices, because a rail's long edge spans from the
    main floor to the overrun and can cross the floor slab with no vertex
    inside it. The obvious lesion — move the ladder north — did fail, but it
    failed the OLD gate too: the dado laminations leave vertices all along the
    run, so eight of them landed in the slab. Proving the new gate needed a
    rail with no vertices in the band at all: remove the dado interruptions
    first, THEN move it. Old gate: 0 vertices flagged, on a rail 0.72" inside
    the slab. New gate: caught.
    **The general form: a lesion is an experiment, and an experiment needs a
    control.** Before believing a gate is strong, ask what the PREVIOUS
    version of it would have said about the same lesion. If the answer is
    "also failed", the lesion has not tested the change — and if the answer is
    "passed", write that number down, because it is the only evidence the
    rewrite was worth doing.

36. **A GATE THAT RECOMPUTES THE BUILD'S ARITHMETIC CANNOT DISAGREE WITH IT,
    and this repo now has four instances.** Rule 29 said it about expressions;
    [#100](https://github.com/captproton/yardstake-ux/pull/100) shows the shape it actually takes — a gate comparing
    a built object against a SUM the builder used, rather than against the
    OBJECT that sum produced.
    `loft_sf + ff` is the top of the loft's finished floor. Three gates
    computed it: the tread's target height, the ledger's hang point, and the
    slab's own extent. Move `Floor_loft` and every one of them goes on
    measuring against a surface that is no longer there. Reviewers caught two
    of the three one round apart, and the third only because the second was
    fixed and the asymmetry showed.
    They read `bounds("Floor_loft")` now, and the difference is not cosmetic:
    the RED test moves the floor 5/8" while the spec's sum stays put, and four
    gates fail that previously could not.
    **Ask of every gate: what would have to be true for this to fail? If the
    only answer involves the gate's own arithmetic being wrong, it is
    checking itself.** The fix is always the same — find the object the claim
    is about and measure that.
