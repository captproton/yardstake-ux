# Tier 3 — Fixtures and furnishing

**Status: sketch.** Enough to scope and estimate; not enough to build from.
Tiers 1 and 2 have both landed, so the interior surfaces this tier sits on now
exist and are textured. **This is the only substantial work remaining** — firm
it up before building.

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

## 1. The good news: sourcing is already solved in principle

This was underestimated in earlier discussion. The inputs split cleanly three
ways, and all three exist:

| What | Source | Confidence |
|---|---|---|
| **Where things sit** | A1.1 plan, measurable at 50 px/ft | ±1", same technique as the windows |
| **How tall they are** | Industry standards | High — these are stock items the builder repeats across units |
| **What they look like** | Video, kitchen chapter 2:11 and bath 2:52 | Good; hue reliable, luminance not |

Every fixture is drawn to scale on A1.1. Spot-measurements already taken:

| Fixture | Plan | Measured |
|---|---|---|
| Tub / shower | callout `5'-0" x 2'8"` | 2.66 ft = **2'-8"** ✓ |
| Electric range | drawn, no callout | **29.9"** — matches the video's "30 inch range" |
| Counter run | drawn | east edge **2.29 ft** off the wall |
| Crawl hole | callout `24" x 24"` | dimensioned |

Also drawn and measurable: toilet, vanity with sink and faucet, dishwasher
(dashed, under-counter), refrigerator, stacked W/D, and the bath ceiling
fan/light.

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
- **Some video frames are a different project.** There is a sequence of a
  concrete countertop being poured outdoors that is not this unit. Verify frame
  contents before using them as reference — a colour sample earlier in this work
  turned out to be the pollinator garden.
