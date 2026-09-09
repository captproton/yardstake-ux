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

Merged to `main` in [#57](https://github.com/captproton/yardstake-ux/pull/57), [#58](https://github.com/captproton/yardstake-ux/pull/58), [#59](https://github.com/captproton/yardstake-ux/pull/59), [#60](https://github.com/captproton/yardstake-ux/pull/60),
[#61](https://github.com/captproton/yardstake-ux/pull/61), [#62](https://github.com/captproton/yardstake-ux/pull/62), [#64](https://github.com/captproton/yardstake-ux/pull/64), [#65](https://github.com/captproton/yardstake-ux/pull/65), [#66](https://github.com/captproton/yardstake-ux/pull/66),
[#67](https://github.com/captproton/yardstake-ux/pull/67), [#68](https://github.com/captproton/yardstake-ux/pull/68), [#70](https://github.com/captproton/yardstake-ux/pull/70), [#71](https://github.com/captproton/yardstake-ux/pull/71) and
[#74](https://github.com/captproton/yardstake-ux/pull/74). The placement developer is unblocked — `lod2` and their
handoff are on `main`.

**`lod2` was byte-identical at 24.1 KB through eleven PRs, and changed in the
twelfth.** [#70](https://github.com/captproton/yardstake-ux/pull/70) replaced the wrong-variant `Floor_slab` with the
crawlspace stemwall, so `lod2` is now **28.4 KB** and its bbox floor moved from
−0.101 m to −0.972 m. That was a conversation before it was a commit, which is
what the stability guarantee actually asks for. Origin, axes and units have
still never moved.

**Tier 3 is complete** — casework, both sinks, both taps, the mirror, the
toilet, the tub/shower, the crawl hole, the stacked W/D, all three appliances,
the porch sconce and, last, the furniture — **and the building stands on a real
foundation.** 113 meshes, all of them shipped in `lod0` at **922.0 KB** against
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

1. **Dedupe `inside_mesh`.** Two copies, one bug, two fixes — the only case
   this session where the *structure* manufactured a second defect rather than
   merely failing to prevent one. Its own small PR, now unblocked because
   `verify_views.py` is free.
2. **[#80](https://github.com/captproton/yardstake-ux/issues/80) — the front
   elevation**: gable window, front-door glazing, ridge beam. Starts with the
   measurement that has already been got wrong twice, so take it from the
   sheet, not from the model. Carries the `Door_`/`Glazing_` ternary fix, which
   belongs there because that conditional-on-type is what shipped the defect.

**Deferred, with the reason recorded so it stays a decision rather than an
omission:** the `main()` split in the verify scripts and a `Box` value object.
Both are genuine improvements to code that will be read for a long time, but
classifying this session's twenty-five defects put only three in the
duplication bucket — neither refactor would have prevented what actually bit
us, and doing them now means a large no-behaviour-change diff across every
verify file. Revisit when a third caller needs one of them.

In order of value:

| Work | Notes |
|---|---|
| **T3:** appliance finish variant | The two filmed units differ (white fridge at 2:11, stainless at 2:27), so finish is a choice. Bodies and fronts are already on one material, so this is a `spec.variants` entry and no geometry |
| **T3:** mounted fixtures beyond the sconce | The porch light landed the `spec.fixtures.mounted` anchor and a `_lib`-candidate form ([#74](https://github.com/captproton/yardstake-ux/pull/74)). The mini-split head, meter panel, tankless heater and heat pump are all wall- or ground-mounted and all sit in `fixtures.not_measured` — they now have somewhere to go, but not one of them is drawn with a height |
| **Export:** mesh instancing | `lod0` is 113 nodes and **113 distinct meshes** — nothing is shared, so `Porch_post_1`/`_2` and the closet door pair are each paid for twice. glTF supports many nodes to one mesh natively and Blender does it with linked duplicates. A win on geometry *already shipped*, and the thing that makes a fixture catalogue cheap. Held out of [#74](https://github.com/captproton/yardstake-ux/pull/74) deliberately: no payoff for one sconce, and it would have hidden an exporter change inside a lighting PR. Belongs with the `_lib` split |
| **T2:** KTX2 compression | Optimisation, not necessity — `lod0` is 922.0 KB against a 4 MB ceiling. Confirm `gltf-transform` is installed first |
| **Foundation:** vent height | The only part of the foundation still assumed. A2.0 draws the vents in *plan*, so it cannot give their height; A1.1's elevations draw no vents at all and show 5-3/4" of exposed concrete, which is schematic since an 8" vent does not fit in it. The 8" height and 4" drop below the top of foundation are ours, labelled `confidence: assumed` |
| **Foundation:** vents in `lod2` | `Found_stemwall` is in the porch collection, so the placement developer's massing carries eight openings through it. Accurate, and harmless at 28.4 KB against a 200 KB ceiling, but it is detail they did not ask for. Filling them in `lod2` is a two-line change to the `cut_openings` branch that already strips windows and doors |
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
