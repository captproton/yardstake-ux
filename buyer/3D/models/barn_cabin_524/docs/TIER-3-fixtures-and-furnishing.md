# Tier 3 — Fixtures and furnishing

**Status: footprints measured ([#59](https://github.com/captproton/yardstake-ux/pull/59)); geometry not started.** Section 1a is
built work with gates behind it. Everything else here is still a sketch —
enough to scope and estimate, not enough to build from.
Tiers 1 and 2 have both landed ([#57](https://github.com/captproton/yardstake-ux/pull/57), [#58](https://github.com/captproton/yardstake-ux/pull/58)), so the interior surfaces this
tier sits on exist and are textured. **This is the only substantial work
remaining** — firm it up before building.

**Casework, both sinks, both taps and the bath mirror are built**
([#60](https://github.com/captproton/yardstake-ux/pull/60), [#62](https://github.com/captproton/yardstake-ux/pull/62), [#64](https://github.com/captproton/yardstake-ux/pull/64)).

**The bath door position was corrected in [#64](https://github.com/captproton/yardstake-ux/pull/64).** It carried
`position_confidence: approx_6in` and was wrong by **13.3"** — more than double
its own stated tolerance — putting the doorway across the measured vanity. A1.1
draws the opening plainly: both wall lines break together at x_int 2.52..4.80,
2'-3-5/8" against a 2'-4" callout. **It never needed estimating.** Worth
checking whether any other `approx_` position in the spec is similarly
measurable rather than guessed.
Footprints measured (§1a), then cabinets, counters, backsplash, uppers, hood
and the bath vanity (§1b), then the kitchen sink basin and tap (§1c) — all
parametric from `spec.fixtures`, none from a bought asset.

**What remains is smaller than it was.** Correcting §2's split from *by trade*
to *by shape* moved the basin and the tub off the buy side, so the only items
still needing third-party assets are the **toilet** and the **appliances**.

**Step 1 of 2 is done.** Fixture footprints are measured and in
`spec.fixtures` — 9 footprints, 10/10 gates, verified against the sheet.
See §1a. No geometry is built yet.

**Still to start: licensing.** Every downloaded asset must be CC0 or explicitly
licensed for commercial use before it reaches a homeowner. This is the one
genuine long-lead item in the whole ladder and the only place third-party
assets enter the model at all — tiers 1 and 2 shipped entirely procedural. It
does not depend on anything below, so it can begin immediately.

**Owner:** us. Tiers 1 and 2 are complete, so the floors and walls fixtures
need already exist and carry real materials — see
[The one handoff](README.md#the-one-handoff--to-the-placement-developer) for the
one external interface. Nothing here is blocked; we set the pace.

**No longer blocked.** Tier 1 delivered the floors and walls, so placement and
clearance checks can both proceed. Two pieces are still the sensible starting
point:

- **Extract fixture footprints from A1.1** into a `fixtures:` block in
  `spec.yaml` — the measuring technique is proven and the sheet is in hand.
- **Source and licence-clear the CC0 assets**, and set the decimation budget.
  Licensing has lead time and is a shipping constraint, not a detail.

**Do not break the handoff.** Fixtures are `lod0` only and ship as a separate
on-demand `.glb`. `lod2` must not gain a single triangle.

**Goal.** Make the rooms read as a home rather than as rooms — kitchen
casework, appliances, bath fixtures, and a decision about staging furniture.

---

## 1a. Footprints — DONE

Measured on A1.1 (pdf page 3) at 200 dpi, where 1/4"=1'-0" is exactly
50.0 px/ft, and recorded in `spec.fixtures` with provenance per item.

| Fixture | Measured | Check |
|---|---|---|
| Tub / shower | 5'-0" × 2'-8½" | callout `5'-0" x 2'8"` — exact on the long axis, ½" on the short |
| Toilet | 2'-5¾" proj. × 1'-10⅛" | ordinary floor-mount two-piece |
| Vanity | 2'-6" × 2'-0" | **30" × 24" — stock on both axes** |
| Refrigerator | 2'-5" × 2'-3¾" | 29" reads as a 30" nominal unit |
| Range | 2'-6⅛" × 2'-2⅛" | **30.1" — matches the video's "30 inch range" to ⅛"** |
| Sink cabinet | 2'-9⅜" × 2'-0" | 33.6" reads as a 33" sink base |
| Dishwasher | 2'-2½" × 2'-0" | 26.5" vs 24" stock — see below |
| Stacked W/D | 2'-3¾" × 2'-0" | compact stacked unit |
| Crawl hole | 2'-0" × 2'-0" | callout `24" x 24"` — **exact on both axes** |

The cabinet run has a single front line at **exactly 24"** off the wall — a
stock base cabinet — with the refrigerator projecting to 27¾" and the range to
26⅛", which is how real kitchens draw. That the run is exactly stock, and that
the range independently reproduces the video's "30 inch range", are the two
strongest signs the datum is right.

**Calibration.** Anchored on the *interior* wall faces, not the drawn wall
band. The band measures 29 px (≈7") where the wall is 5½" — the same
line-weight inflation that made the exterior wall read 6½" until P4 corrected
it. Interior faces are also what fixtures physically sit against. Both interior
dimensions reproduce to ⅛".

**Method, and a wrong turn worth recording.** Fixture edges come from the
*drawn lines* — rows and columns whose ink spans most of the fixture. Ink
bounding boxes inside hand-chosen windows were tried first and abandoned: a
window that clips its fixture reports the window, a window inside the fixture
reports the window too, and nothing in the output distinguishes either from a
real measurement. Six of nine fixtures were wrong that way before the method
changed, and every one of them looked like a plausible number.

**One disagreement, recorded not silenced.** The dishwasher opening measures
26½" against a 24" stock appliance — most likely the box is the cabinet opening
rather than the appliance. It is in `spec.discrepancies` as
`dishwasher-width`. Model the appliance at 24" inside the drawn opening; do not
snap the plan's number, the same treatment the loft egress finding got.

### Verification

`verify_fixtures.py` — **10/10, no Blender needed**. It runs on the spec alone,
which is the cheapest moment to catch a bad measurement, before anything is
modelled on top of it.

Envelope containment, pairwise overlap, tub-fits-alcove, kitchen aisle, clear
floor at toilet and vanity, toilet centreline, room assignment, heights-declared-assumed,
and callout reproduction.

Two results worth reading:

- **The toilet centreline clears by 15½" against a 15" IRC minimum.** This
  section predicted the bath clearances would be tight and worth asserting
  rather than assuming. They are.
- **The tub has 1¼" spare** in its 5'-1" alcove. A 5'-0" tub in a 5'-1" room is
  exactly as tight as it sounds.

The relative gates cannot catch a systematic error — a wrong datum would
satisfy all of them. So `tools/tier3/overlay.py` draws the recorded rectangles
back onto the sheet they came from:
[`../renders/tier3_fixture_overlay.png`](../renders/tier3_fixture_overlay.png).
All nine land on their drawn fixtures.

## 1b. Casework — BUILT

`build_casework()` in `build_adu.py`, driven entirely by `spec.fixtures`. This
is the *build* half of §2's build-vs-buy: boxes, spec-driven, and it regenerates
for the next plan set for free.

**Where the cabinets go was not a new measurement.** The base segments are
exactly the gaps left over between the measured appliances and the interior
south wall, so they inherit those measurements and add no new claim — which is
why the spec marks them `derived`, not `measured`. The gaps then land where the
video says cabinets are, and that is the check:

| Gap | Size | What the video shows there |
|---|---|---|
| 10.71–12.37 | 19.9" | base cabinet between refrigerator and range |
| 14.88–16.64 | 21.1" | **the four-drawer stack** |
| 21.65–23.08 | 17.2" | base cabinet at the south end, past the dishwasher |

Built: base carcasses, toe kicks, door and drawer fronts, countertop, 6"
backsplash, upper cabinets, the range hood, and the bath vanity. **8 objects,
240 faces** — `multibox()` keeps the object count down, because trim already
taught us draw calls bite before triangles do. `lod0` mesh count is 59 against
a 120 cap.

**Uppers are cut by what stands under them.** A run is not floated at one
height: the refrigerator and the range hood interrupt it at different levels,
so `spans()` cuts each run at every obstruction edge and gives each piece its
own floor. That is what produces the stepped profile in
[`../renders/tier3_kitchen.jpg`](../renders/tier3_kitchen.jpg), and it matches
the video.

**The sink opening is cut**, and measured rather than assumed: A1.1 draws the
sink as an outer rim and an inner bowl, and the cutout is the **inner bowl** —
2'-4⅛" along the wall by 1'-3¼" off it. The rim spans very nearly the whole 33"
cabinet, so using it would have cut away the counter's own bearing.

It is built as a **frame of four boxes around the hole, not a boolean**.
Booleans on hand-wound geometry are how P2 produced a mesh that looked cut and
kept its full volume; four exact boxes cannot fail that way, and the counter is
axis-aligned so a boolean would buy nothing. Gated by volume anyway — the
counter must equal the solid slab less the hole, exactly.

**Not built here, deliberately:** refrigerator, range, dishwasher, stacked W/D,
toilet, tub, taps, and **the sink basin itself**. Those are the *buy* half and
are gated on licensing, so the render has gaps where they belong — including a
counter opening with nothing in it. That is the honest state: the hole is
right, the fixture is pending.

**The build/buy split in §2 needs amending, and this is why.** It sorted
plumbing by *trade* rather than by *shape*, which swept the sink basin in with
the tap. A basin is a box with a radius and carries no licensing exposure; a
tap is genuinely organic. Same for the vanity basin, and arguably the tub —
already measured to ⅛" against its callout. **The vanity top has the same
missing cutout** and was left alone only to keep this branch to its stated
scope.

**Also outstanding:** the 24"×24" crawl hole is measured and reproduces its
callout exactly, but is not cut into the floor. That is Tier 1 floor geometry
which Tier 3a's measurement pass unblocked, not a Tier 1 regression — the
dimension did not exist until this tier.

### Configurator

The two option sets `spec.variants.not_yet` reserved for this tier now exist:
**cabinet finish** (natural / white / espresso) and **countertop** (white
granite / tan granite / charcoal quartz). The manifest is now **7 sets, 20
options, still 0 extra texture bytes** — both new materials are neutral-albedo,
so the colour rides on `baseColorFactor` exactly as the exterior does.

The first two countertop options are the **two actual filmed units**. The video
showing different stone in different buildings (§7) is precisely why this is a
choice rather than a fact, so both ship.

Two new procedural textures, `cab_wood` and `granite`. `cab_wood` is
deliberately *not* `oak_floor` with a different tint — that generator draws
planks with butt joints and seams, which is right for a floor and reads as a
fault in the joinery on a cabinet door.

### Verification

The manifest gate only checks that targets name real materials, and §6 of
TIER-2 records what that missed last time. So `variant_demo.py` now runs **two
scenes**, and the interior one asserts **isolation as well as separation**:

| Assertion | Result |
|---|---|
| countertop moves when only the countertop changes | **15.0** (limit 8) |
| **cabinets HOLD when only the countertop changes** | **0.0** (limit 1) |
| cabinets move when the cabinet finish changes | **50.7** (limit 20) |

The isolation row is the one that carries weight: it proves a swap addresses
the material it claims to and nothing else. Evidence:
[`../renders/tier3_casework_variants.png`](../renders/tier3_casework_variants.png).

A wrong turn worth recording: the countertop first looked like it barely
moved. That was a bad sample patch straddling the wall and the counter, not a
defect — which is exactly why the patches are now named, fixed in the spec of
the demo, and asserted rather than eyeballed.

`lod1` and `lod2` are byte-identical before and after. The placement handoff is
untouched.

## 1c. Sink and tap — BUILT

Built from **our own sources**, which is the first thing worth saying: the
footprint is the cutout measured off A1.1, and the appearance comes from video
2:40, which shows this unit's sink plainly — an undermount stainless
rectangular bowl with an integrated drain ledge, and a commercial-style
spring-coil pull-down tap.

**Nothing here came from a third-party asset or from another vendor's
configurator.** That matters beyond licensing: every dimension still traces to
the plan set or to a named standard, exactly like the rest of the spec, so
there is no provenance question to answer later.

| | |
|---|---|
| Basin footprint | the measured cutout, plus a 1/4" counter lap on the rim |
| Basin depth | 8-3/4", industry standard — assumed, like every height here |
| Tap | column, half-turn gooseneck, angled spray head |

The tap is this model's **first round primitive**. `tube()` sweeps an n-gon
along a polyline at 8 sides — enough to read as round at configurator distance,
and a third the cost of a smooth one. Everything else in the model is
axis-aligned boxes, which is right for architecture and useless for a tap.

The two filmed units have **different taps** — 2:40 a commercial coil, 1:08 a
plain gooseneck — so like the countertop this is a choice rather than a fact,
and it is modelled generic. The coil itself sits below the fidelity of
everything else here and is deliberately not modelled.

### Two mistakes worth recording

**The tap was on the wrong side of the counter.** "Behind the bowl" means
toward the wall, which is a *smaller* x in this datum; the first version put it
at `cx1 + behind`, standing it on the counter's front lip in the walkway. In a
render it looked merely odd — the kind of thing that survives review.

**The basin was buried inside the cabinet.** A sink base has an open top; ours
was a solid box, so the basin sat entirely within it and the render showed
cabinet through the cutout. That reads as a *missing* basin rather than a
buried one, which is exactly the wrong diagnosis a render invites. The sink
base is now carved: solid below the bowl, a frame around it above.

Both are now gated, because neither would have failed any existing check:

| Gate | Result |
|---|---|
| tap stands between the bowl and the wall | tap at 3", bowl starts 4-3/4" |
| tap spout lands over the bowl | spout at 11", bowl 4-3/4" to 1'-8" |
| basin bottom clears the cabinet interior | floor at 2'-1-3/4", carcass starts 3-1/2" |

`verify_fixtures.py` is now **16/16**, still with no Blender needed. See
[`../renders/tier3_sink.jpg`](../renders/tier3_sink.jpg).

## 1. The good news: sourcing is already solved in principle

This was underestimated in earlier discussion. The inputs split cleanly three
ways, and all three exist:

| What | Source | Confidence |
|---|---|---|
| **Where things sit** | A1.1 plan, measurable at 50 px/ft | ±1", same technique as the windows |
| **How tall they are** | Industry standards | High — these are stock items the builder repeats across units |
| **What they look like** | Video, kitchen chapter 2:11 and bath 2:52 | Good for CASEWORK; **finishes differ between units — see [§7](#7-the-video-shows-more-than-one-unit)** |

Every fixture is drawn to scale on A1.1, and all of them are now measured —
see §1a for the full table and the gates.

**What the plan does not contain: any vertical dimension.** The set has no
interior elevations — sheets are A0.0, A0.1, A1.0, A1.1, A2.0, A3.0, A4.0, N-1,
and not one shows a vertical interior surface. Heights come from standards.

## 2. Build vs. buy

**Build parametrically** — box-like, belongs in `build_adu.py` driven by a new
`fixtures:` block in `spec.yaml`:

- Base and upper cabinet runs, with door/drawer faces
- Countertops and backsplash
- Vanity cabinet
- Shelving, the closet rod and shelf

These are boxes. They inherit every advantage the rest of the pipeline has —
spec-driven, verifiable, and they regenerate for the next plan set for free.

**Buy or download** — organic or mechanically complex, not worth authoring:

- Appliances: range, refrigerator, dishwasher, stacked W/D, mini-split head
- Plumbing: **toilet** — and taps, optionally
- Light fittings

**AMENDED.** This list originally read "Plumbing: toilet, sink, tub/shower,
taps", which sorted by **trade** rather than by **shape** — and shape is the
only thing the split is actually about. A basin is a box with a rim; a tub is a
box with radii, already measured to 1/8" against its callout. Neither is
organic, neither is mechanically complex, and putting them on the buy side
gated them behind asset licensing for no reason at all. The **kitchen sink and
its tap are now built** (section 1c). The toilet stays on the buy side, where
it belongs.

CC0 sources: Poly Haven, ambientCG, Blender's own asset library. **Licensing is
a shipping constraint** — this reaches homeowners. Record source and licence
per asset in the spec, same as everything else.

## 3. Payload — the real constraint

This is where the model stops being small. `lod0` is 419 KB with Tier 2
complete, against a 4 MB ceiling; fixtures are the next big step up and will
consume most of the headroom.

Downloaded assets routinely arrive at 50k–500k triangles each. Fifteen of them
naively imported would be tens of megabytes, which destroys the configurator on
a phone.

**Two rules:**

1. **Decimate on the way in.** Budget ~2–5k triangles per fixture. At
   configurator viewing distance nobody counts the polygons on a tap.
2. **Ship fixtures as a separate `.glb`, loaded on demand.** The interior view
   is a deliberate user action ("Show Interior"). Load `barn_cabin_524_fixtures.glb`
   then, and never on the siting path.

This keeps the exterior and siting payloads exactly as light as they are today.
`lod2` in particular must not gain a single triangle from this tier.

Rough budget: fixtures glb ≤ 3 MB compressed, on top of the current 419 KB
`lod0`. If it exceeds that, decimate harder before dropping items.

## 4. Furniture and appliances — DECIDED

**Both are shown. Neither is included in the price.** Studio-Home displays
default appliances the same way.

The furniture is **architectural, fill-in-the-space** — schematic, neutral,
unbranded. It exists to let a buyer read scale and circulation, not to depict a
product. That framing is doing real work:

- It is **cheaper**. Simplified forms, no photoreal detail, small triangle
  budget.
- It is **safer**. A generic grey sofa does not imply a specific sofa on
  delivery the way a photoreal branded one does.
- It **sidesteps most licensing risk**, which is the long-lead item in §2.

So: build furniture as simple architectural masses in the manner of the
Studio-Home reference, not as furniture-catalogue assets. Appliances need more
fidelity than furniture — a range should read as a range — but the same
restraint applies.

**Three build consequences:**

1. **Separate `.glb`, separate name prefixes.** Furniture and appliances get
   their own prefixes (`Furn_`, `Appl_`) and ship outside the shell model, so
   either group toggles in one line — consistent with the existing display-mode
   switching.
2. **Disclosure is a UI requirement, not a modelling one.** "Furniture and
   appliances shown for scale; not included" needs to appear wherever a price
   does. Worth stating to whoever builds the configurator UI, because nothing in
   the model can enforce it.
3. **Default them on** for marketing and configurator views. The toggle exists
   so they can be turned *off* for any view that must show only what is
   supplied.

## 5. Verification

The same discipline. Fixtures are easy to place plausibly and wrong.

1. **Footprint gate** — every fixture's plan footprint matches the measured
   value from A1.1 within tolerance, checked by the same volume/bounds method
   `verify_openings.py` uses.
2. **Intersection check** — no fixture intersects a wall, partition, or door
   swing. Cheap with bounding boxes, and it will catch real errors.
3. **Clearance check** — the one that actually matters for credibility:
   - kitchen aisle ≥ 36" (NKBA; 42" preferred)
   - clear floor space in front of the toilet and vanity
   - the bath is 5'-1" × 8'-0" with a 5' tub, so clearances are genuinely tight
     and worth asserting rather than assuming
4. **Payload gate** — per §3.

A failing clearance check is a finding about the *plan*, not necessarily a bug
in the model — record it in `spec.yaml → discrepancies` the way the loft egress
issue was, rather than quietly adjusting geometry to make it fit.

## 7. The video shows more than one unit

**Established by looking, not inferred.** The kitchen chapter cuts between two
different built units of the same floor plan, 26 seconds apart:

| | 2:14 | 2:40 |
|---|---|---|
| Countertop | tan / beige granite | white / grey granite |
| Refrigerator | white | stainless |

Granite is not swapped between takes. These are different buildings, not the
same room restaged. Side by side:
[`../refs/video_two_units_2-14_vs_2-40.jpg`](../refs/video_two_units_2-14_vs_2-40.jpg).

**What this costs.** A finish sampled from the video describes *one* of those
units, not "the" unit, and two finishes taken from different timestamps may not
belong together. Every finish citation must carry its timestamp — the existing
ones do — and finishes must never be averaged across timestamps. Recorded in
`spec.video_sources`, positioned immediately above `spec.fixtures` so anyone
sampling for Tier 3 hits it first.

**What survives intact, and it is most of what this tier needs.** The
*casework* is identical across both units:

- Shaker doors, natural wood
- **Upper cabinets present** — which settles the §2 assumption
- An under-cabinet range hood, which is on neither the plan nor this document
- A sink base with doors, a four-drawer stack to its right, dishwasher at the
  south end

The clearest single frame is
[`../refs/video_kitchen_2-40.jpg`](../refs/video_kitchen_2-40.jpg) — build the
casework against that one, and take finishes from it only with the timestamp
attached.

Both units also reproduce the A1.1 appliance **order** — dishwasher, sink,
range, refrigerator running south to north. That is an independent check on the
Tier 3 footprint datum, from a source that had no part in the measurement.

**The exterior citations were re-checked** against 0:00, 6:56 and 7:50 and are
consistent with one another — warm off-white lap siding, grey composition roof,
white trim. `materials.provenance` stands and nothing shipped needs revisiting.

## 6. Open questions

- ~~Which appliances are included in the price?~~ **Settled** — appliances and
  furniture are both shown and neither is included. See §4.
- **Model as-built or as-configurable? — now decided by Tier 2.** The finishes
  picker is real and shipped, so fixtures must be authored for material
  swapping: **neutral albedo maps, colour on `baseColorFactor`, one named
  material per swappable surface.** `spec.variants.not_yet` already reserves
  countertops and cabinets as the two sets waiting on this tier. Follow the
  pattern in [TIER-2 §6](TIER-2-materials-and-textures.md#6-configurator-hooks--done)
  and the options cost nothing; ignore it and each finish becomes another
  texture in the payload. This applies to *fixtures* (cabinets, counters),
  which are part of the unit — not to the furniture and appliances settled
  above, which are not configurable because they are not sold.
- ~~Loft ladder ownership~~ **Settled** — Tier 1 built it, at the measured
  20° heel cut (verified 20.07°), and it lands on the loft subfloor within
  ¼". Nothing left here.
- ~~Some video frames are a different project.~~ **Confirmed and worse than
  suspected — see [§7](#7-the-video-shows-more-than-one-unit).** The video
  intercuts at least two different built units of this plan, inside the kitchen
  chapter itself.
