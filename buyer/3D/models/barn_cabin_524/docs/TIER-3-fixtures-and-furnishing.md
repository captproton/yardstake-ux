# Tier 3 — Fixtures and furnishing

**Status: footprints measured ([#59](https://github.com/captproton/yardstake-ux/pull/59)); geometry not started.** Section 1a is
built work with gates behind it. Everything else here is still a sketch —
enough to scope and estimate, not enough to build from.
Tiers 1 and 2 have both landed ([#57](https://github.com/captproton/yardstake-ux/pull/57), [#58](https://github.com/captproton/yardstake-ux/pull/58)), so the interior surfaces this
tier sits on exist and are textured. **This is the only substantial work
remaining** — firm it up before building.

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
- Plumbing: toilet, sink, tub/shower, taps
- Light fittings

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
