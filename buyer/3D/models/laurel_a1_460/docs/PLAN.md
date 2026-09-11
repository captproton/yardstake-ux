# laurel_a1_460 — build plan

Second ADU model. Subject: **Sacramento County Permit Ready ADU, Model A1
"Laurel", 460 sf**, from
[`../../../example plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf`](../../../example%20plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf)
(20 sheets, Laura Miller Design, El Dorado Hills CA; drawn 2024-04-04;
2022 California Residential Code).

This plan assumes the ladder, the gates and the ground rules from
[`../../barn_cabin_524/docs/README.md`](../../barn_cabin_524/docs/README.md).
Read rules 1–33 there before writing anything here. Nothing below repeats them.

---

## Why this model, and what is different

Laurel was chosen as model two because it shares almost no typology with the
barn cabin and therefore forces an honest split between the kit and the
building. It is **single storey, slab on grade, no loft, no dormers, no
crawlspace, no porch**. Every barn-cabin module for those features is simply
not called.

Two differences change the method, not just the geometry.

**1. The sheets carry live text.** The barn cabin PDF is raster — text
extraction returns 7 bytes, so all 2,927 lines of its spec were read off images
by eye. Laurel extracts 86 KB of text, and `pdftotext -bbox-layout` returns
every string with page coordinates. Dimension strings can therefore be
harvested and *positioned*, not transcribed. P1 becomes a review of machine
output rather than a manual reading. This is the single biggest saving in the
whole plan and it must be built as a kit tool, because Richmond and all six
Concord sets extract the same way.

**2. There is a published rendering.** `a1-laurel-rendering.jpg` is the
designer's own image of the finished building. The barn cabin had only video
frames, which rule 5 restricts to appearance evidence. The rendering is still
appearance evidence and never geometry, but it is a far better colour and
material reference than a compressed video still.

There is no tour video, so there is **no footage-derived position** the way the
porch sconce was placed in the barn cabin. Anything not on a sheet is either
omitted or declared `confidence: assumed` and gated as such.

---

## What the sheets already say

Confirmed from extracted text. Every one of these still needs a sheet citation
in `spec.yaml` before it is used.

| Fact | Value | Source |
|---|---|---|
| Floor area | 460 sf | A-0.0 project data |
| Foundation | slab on grade | A-0.0 project data |
| Occupancy / construction | R-3 / Type V-B | A-0.0 project data |
| Exterior wall | 2x6 framing, stucco **or** fibre-cement lap siding | A-0.0, wall legend on A-1.0 |
| Interior wall | 2x4, gypsum board both sides | wall legend on A-1.0 |
| Roofing | standing seam metal | A-2.0 roof plan notes |
| Top of plate 1 | 8'-0" | A-2.0 |
| Top of plate 2 | 9'-7 1/2" | A-2.0 |
| Roof overhang | 1'-6" | A-2.0 |
| Elevation scale | 1/4" = 1'-0" | A-2.0 front elevation title |
| Ceilings | follow the roof line (vaulted) | A-1.0 note |
| Entry canopy | optional, 2x6 cedar frame, 1x6 trim | A-3.4 |
| Windows | vinyl, SHGC 0.21 | A-0.0, window notes |

**Two top-plate heights and an upper/lower roof split.** A-2.0 sizes attic
ventilation separately for an "upper roof" and a "bottom roof", 110.16 square
inches each. That, plus T.P. 1 and T.P. 2, means the roof is **two planes at
different plate heights**, not a symmetric gable. Resolving exactly which form
(offset gable, split shed, or clerestory) is the first job of P1 and the thing
most likely to be got wrong, so it gets its own gate in P3.

**There is an option split, as there was for the barn cabin.** A-1.0 carries a
"1 bedroom floor plan option", and the Willow A2 cover sheet lists a second
area of 122 sf beside the 460. Decide and record the chosen option in
`spec.yaml` under `option_selection` with the same reasoning format used for
the barn cabin's Option B, and note that the unchosen option is a candidate for
the variants manifest later, not a second model.

**Sheet map** (already extracted, to be recorded verbatim in `spec.yaml`):

| PDF page | Sheet | Carries |
|---|---|---|
| 1 | A-0.0 | Cover, project data, sheet index |
| 2–3 | A-0.1, A-0.2 | Notes |
| 4 | A-1.0 | Floor plan, wall legend, window and door schedules |
| 5 | A-1.1 | Electrical / reflected plan |
| 6 | A-2.0 | Roof plan **and** elevations |
| 7–12 | A-3.0 … A-3.5 | Wall assemblies, window and door details, canopy |
| 13–16 | S1.0 | Structural |
| 17–20 | T24-1…4 | Title 24 energy |

Geometry authority is **A-1.0 and A-2.0**. A-3.x governs assembly thickness
only. S1.0 and T24 carry no massing.

---

## P0 — extract the kit (prerequisite, own PR)

Nothing model-specific ships in this phase. Move only what already contains
zero barn-cabin knowledge.

Target layout:

```
buyer/3D/adu_kit/
  kernel.py        box, weld, multibox, tube, loft, ellipse_ring, prism,
                   uv_project, mark_reveals, difference, world_bbox, ft
  verify_lib.py    moved as-is
  textures.py      from make_textures.py
  export.py        to_metres, export_glb, Draco, base-colour patch,
                   variants manifest emission, glb_info
  views.py         camera presets and the sidebar panel
  sheets.py        NEW — the coordinate-aware PDF harvester (see P1)
  schema/          spec schema, manifest schema, the lod2 contract
buyer/3D/models/barn_cabin_524/   spec.yaml + typology build + its own gates
buyer/3D/models/laurel_a1_460/    same shape
```

Two rules for this PR.

- **The barn cabin must build byte-identical after the move.** Its three
  exported levels, its manifest and all its gates are the regression test. If
  `lod2` changes, the extraction was not a move.
- **Leave the gates where they are.** Several `verify_*.py` scripts embed
  barn-cabin expectations inside otherwise generic checks. They get promoted
  one at a time, in P2 and P3 below, when Laurel proves which assertion was
  about buildings and which was about that building. Rule 29 applies: a gate
  generalised against a typology it has seen once cannot disagree with it.

**Fix the lod2 contract in the same PR.** It currently encodes a concrete
bounding-box floor, which moved when the crawlspace replaced the slab. Laurel
is slab on grade and will not match. The contract must assert *per model* that
origin, axes, units and the declared floor datum have not moved since the
recorded baseline, and carry that baseline in the model directory rather than
in shared code.

---

## P1 — spec with a machine-read first draft

**Build the harvester first** (`adu_kit/sheets.py`). It should:

1. Read `pdftotext -bbox-layout` output for a given page.
2. Parse every feet-and-inches string into decimal feet, keeping the raw string.
3. Keep each string's page rectangle.
4. Emit a YAML fragment of candidate dimensions with page, sheet id and
   position.

It must **never** write `spec.yaml` directly. It produces candidates; a human
accepts each one with a `source:` citation. Rule 25 applies to its own output:
anything read from disk is untrusted input, including files this project wrote.

**Then write `spec.yaml`** in the barn cabin's shape and order — `meta`,
`option_selection`, `sheet_index`, `envelope`, `levels`, `roof`,
`construction`, `openings`, `partitions`, `fixtures`, `finishes`, `variants`,
`discrepancies`. Keep the authority rule at the top, naming A-1.0 and A-2.0.

Specific unknowns P1 must settle, in order of risk:

- The **roof form** implied by T.P. 1, T.P. 2 and the upper/lower vent split.
- The **overall footprint**, which 460 sf does not determine on its own. A
  24'-0" dimension and a 13'-2" dimension both appear on A-1.0; neither is
  confirmed as an overall.
- The **height datum**. Slab on grade means finished floor sits near grade, so
  the barn cabin's finished-floor-versus-grade ambiguity should not recur, but
  it must be stated explicitly rather than assumed absent.
- The **window and door schedules** on A-1.0. Both exist as tables; page
  coordinates are what will reconstruct their rows, since reading order alone
  scrambles them.
- **Wall assembly thickness** for 2x6 exterior and 2x4 interior, from A-3.x.

Exit gate: every numeric value has a `source:`, and a spec-lint gate rejects
any key that carries a number without one.

---

## P2 — massing and openings

Write `build.py` for this typology only. It calls the kit kernel and reads
`spec.yaml`. No dimension appears in the file.

Scope: slab, exterior and interior walls, the two-plane roof with 1'-6"
overhangs, vaulted ceilings that follow the roof line, window and door
openings cut from the schedule, and the optional entry canopy as a separate
switchable collection.

Promote from the barn cabin, unchanged where possible: the opening cutter,
sash construction from the declared window type, exterior casing, interior
stools and aprons, and reveal marking. These were the subject of four PRs and
are the most battle-tested code in the project.

Do **not** call: dormers, knee walls, loft subfloor, ladder, guardrail,
crawlspace stemwall, vents, piers, porch posts.

Exit gate: the geometry gates pass, and the opening gate confirms every
schedule row produced a cut opening with a sash.

---

## P3 — overlay calibration against A-2.0

Same method that settled the barn cabin ridge, and it is the phase that will
catch a wrong roof reading.

Render the model orthographically, trace the A-2.0 front elevation at the
sheet's stated 1/4" = 1'-0", and compare silhouettes. The barn cabin landed at
−0.18" mean and 0.21" standard deviation; hold Laurel to the same.

Add one gate this model needs and the barn cabin did not: **the two roof
planes must meet the two declared plate heights**. Prove it can fail by moving
T.P. 2 an inch and confirming the gate goes red. Rule 19 — a red test that
moves the spec proves nothing — means perturb the *build*, not the spec.

---

## P4 — materials, levels of detail, export

Kit code does nearly all of this.

Model-specific work is the material set: standing seam metal roofing, and the
two declared exterior finishes. **Stucco and fibre-cement lap siding are a
finish variant, not a decision** — the sheet offers both, so ship both in the
manifest as a material swap. That is exactly what the configurator's `sets`
block is for and it costs no extra geometry.

Check the rendering for colour only, then confirm any sampled colour against a
second source before trusting it. Rule 4 exists because a "siding" colour patch
was once something else entirely.

Exit gate: three levels exported with Draco, manifest validates against the
kit schema, the lod2 baseline is recorded, and the mesh budget gate passes.

---

## Tiers 1–3

Same ladder, smaller building. The order that worked before still applies:
finishes and trim, then textures and the configurator manifest, then fixtures
measured before anything is built.

Fixture inventory visible in the sheets so far: kitchen with dishwasher,
refrigerator and pantry; bathroom with a 36" vanity and a tub or shower; a
washer/dryer closet with its own louvred door requirement; a heat-pump water
heater, named on the energy sheet as a Rheem PROPH 40T2R H37515; and a
mini-split condenser with an exterior pad.

Two of these are new and worth flagging. The **water heater and the mini-split
are named equipment**, which the barn cabin never had — build them from
primitives at the published dimensions rather than downloading, per rule 32.
The mini-split condenser is the first **exterior ground-mounted** object in the
project and will need its own placement rule relative to the slab.

Furniture reuses the barn cabin's arrangements through the `presence` block.
The bedroom-versus-office swap transfers directly.

---

## Risks

- **The roof form is the one real unknown.** Everything else is dimensioned
  text. If P1 cannot settle it from A-2.0 and the sections, stop and say so
  rather than picking the reading that makes the arithmetic close — that is
  precisely how the barn cabin's ridge datum went wrong twice.
- **The harvester will look more trustworthy than it is.** Machine-read
  dimensions that land in a spec without a human citation are worse than hand
  reading, because they carry false confidence. The lint gate is not optional.
- **Generalising a gate too early.** Resist folding barn-cabin gates into the
  kit until Laurel has duplicated them in fact. Two examples is the minimum
  evidence for a shared abstraction.
- **Scope creep from Willow.** A2 Willow shares this sheet set's conventions
  and is an obvious third model. It is not part of this plan.

---

## Sequence

Each line is one pull request.

1. Extract the kit; barn cabin builds byte-identical; lod2 contract made per-model.
2. `sheets.py` harvester plus a known-answer test against barn-cabin values already verified by hand.
3. `spec.yaml` P1, with the roof form settled and cited.
4. `build.py` P2 massing and openings.
5. P3 overlay, plus the plate-height gate, proved by perturbation.
6. P4 materials, the stucco/siding swap, three levels, manifest, baseline.
7. Tier 1 finishes and trim.
8. Tier 2 textures and configurator.
9. Tier 3 fixtures, including the water heater and the mini-split.
10. Furniture and arrangements.

Steps 1 and 2 are the ones that pay for themselves across Richmond and the six
Concord sets. Everything from 3 onward is this building only.
