# laurel_a1_460 — build plan

Second ADU model. Subject: **Sacramento County Permit Ready ADU, Model A1
"Laurel", 460 sf**, from
[`../../../example plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf`](../../../example%20plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf)
(20 sheets, Laura Miller Design, El Dorado Hills CA; drawn 2024-04-04;
2022 California Residential Code).

**The sheet set is not in git.** `example plans/sacramento_adus/` is ignored
(`buyer/3D/.gitignore`), so the PDF (13.6 MB) and `a1-laurel-rendering.jpg`
exist only in the main working tree. The link above works there, and not on
GitHub or in a separate worktree. Point tools at the main tree's copy.

This plan assumes the ladder, the gates and the ground rules from
[`../../barn_cabin_524/docs/README.md`](../../barn_cabin_524/docs/README.md).
Read rules 1–33 there before writing anything here. Nothing below repeats them.

**Updated 2026-09-13, after the configurator page (#106–#112).** This plan was
written before the page existed. The page now reads every exported model
through an index and a manifest, and it refuses what does not meet the
contract. Laurel is the first model built *for* that page. The section
"What the configurator page requires" below lists what that adds, and the
sequence now includes the two page issues a second real model needs:
[#117](https://github.com/captproton/yardstake-ux/issues/117) (the front) and
[#119](https://github.com/captproton/yardstake-ux/issues/119) (footprint positions).
Laurel's export also closes the last box of
[#111](https://github.com/captproton/yardstake-ux/issues/111).

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

## What the configurator page requires

The page ([`../../../docs/PAGE-PLAN.md`](../../../docs/PAGE-PLAN.md)) names no
building. Everything it shows comes from `prototype/models.json`, written by
`build_index.py`, and from each model's `export/variants.json`. So Laurel
reaches the page only through that contract, and **the page's code may not
change to show it**: `prototype/index.html` and `prototype/app.js` stay as they
are. The generated index `prototype/models.json` does change, by gaining
Laurel's row, and `build_index.py --check` holds it to a fresh scan.
`verify_prototype.py` gate 1 fails if the page names anything Laurel
publishes.

What the export must carry, and what checks it:

| requirement | from | checked by |
|---|---|---|
| identity: `id`, `name`, `area_sf`, `area_key`, `area_source`, `storeys` | #106 | `model_contract.identity_problems()` in `finish_adu.py`; `verify_index.py` |
| `front`: which end of the box is the building's front (`+x`, `-x`, `+z`, `-z`, in the glTF frame), in the `model` block and the index row, and checked at export: the entry door must sit at that end | #117 (step 6) | `identity_problems()` and `row_problems()`; `finish_adu.py`'s geometry check; `verify_index.py` |
| `views`, `dimensions`, `sets`, `presence`, `disclosure` **whole or refused**: a malformed block renders no control at all | #108, #109 | `model_contract.display_problems()` |
| finish colours **linear** `baseColorFactor`, alpha 1 | #109 | `display_problems()`; the page swatches them in sRGB |
| a `disclosure` whenever `presence` shows furniture, at most 200 characters | #109 | `display_problems()` |
| every material a set tints and every node a layout or view names **exists in the .glb** | #106 | `verify_index.py` |
| dimension `units` the page knows | #108 | `display_problems()`; gate 4 keeps the page and contract agreeing |

What the page **assumes** today, which Laurel may break:

- **The front faces +Z.** A model exported another way opens showing its
  back. [#117](https://github.com/captproton/yardstake-ux/issues/117) declares
  the front in the manifest. It is step 6 below, just before Laurel's export
  in step 7.
- **A footprint is centred on the building.** The manifest gives sizes, not
  positions, so the overlay centres the footprint it draws. Laurel has no
  porch, so it has no `with_porch`, and the overlay falls back to the next
  footprint. That is exact only if the footprint is symmetric within the
  bounding box; overhangs and the optional entry canopy may not be.
  [#119](https://github.com/captproton/yardstake-ux/issues/119) declares
  positions. It is step 9, before the configurator work in step 10.

What Laurel **proves** for the page: the last box of
[#111](https://github.com/captproton/yardstake-ux/issues/111), that a second
exported model lands as an index row with no page code. The generated
fixtures could not prove it, because `make_fixtures.py` writes its own index
instead of going through `build_index.py`.

What the page does **not** need from Laurel: prices. The estimate and quote
slots ([`../../../docs/COMMERCE.md`](../../../docs/COMMERCE.md)) are the Rails
app's, joined on option ids.

---

## P0 — extract the kit (prerequisite, own PR)

**Done, 2026-09-14** ([#126](https://github.com/captproton/yardstake-ux/issues/126)): PR A,
[#137](https://github.com/captproton/yardstake-ux/pull/137), moved the kernel, the
export helpers and `inside_mesh()`; PR B,
[#138](https://github.com/captproton/yardstake-ux/pull/138), moved `model_contract.py`
into `adu_kit/schema/`. Both proved the barn cabin byte-identical and every gate and
probe reporting what it did before. The checks that need no Blender now also run in
CI on every PR ([#139](https://github.com/captproton/yardstake-ux/issues/139)); the
Blender gates and the byte-identical check are still run by hand.

Nothing model-specific ships in this phase. Move only what already contains
zero barn-cabin knowledge.

Target layout:

```
buyer/3D/adu_kit/
  kernel.py        box, weld, multibox, tube, loft, ellipse_ring, prism,
                   uv_project, mark_reveals, difference, world_bbox, ft
  verify_lib.py    inside_mesh() only
  export.py        to_metres, export_glb, glb_info
  sheets.py        NEW — the coordinate-aware PDF harvester (step 2, #127)
  schema/          model_contract.py (#138)
buyer/3D/models/barn_cabin_524/   spec.yaml + typology build + its own gates
buyer/3D/models/laurel_a1_460/    same shape
```

**Narrowed against the code for #126, by this phase's own rule.** The
first draft listed more; reading it showed some of that knows the barn
cabin, so it stays with the barn cabin until Laurel proves what is generic:

- `verify_lib.py`'s known-answer cases (`inside_mesh_cases`) name barn-cabin
  objects and coordinates. Only `inside_mesh()` moves.
- `views.py` names this building's rooms (`Floor_bath`, the kitchen) in its
  camera presets.
- `make_textures.py`: the generators are generic, but `main()` names the
  barn cabin's materials. The generators move when Laurel's textures use
  them (step 10, #133).
- The base-colour patch and the variants manifest emission read the barn
  cabin's spec shape. They move when Laurel's export shows which parts are
  generic (step 7, #131).

It is **two PRs**, so a problem shows up as the page's or the kernel's, not
both: **A** moves the kernel, the export helpers and `inside_mesh()`; **B**
moves `model_contract.py` into `schema/`. Three rules for both.

- **The barn cabin must build byte-identical after the move.** Its three
  exported levels, its manifest and all its gates are the regression test. If
  `lod2` changes, the extraction was not a move.
- **The page and its probes must not notice.** `model_contract.py` moved into
  `adu_kit/schema/`, and six places reached it by location:
  `build_index.py`, `verify_index.py`, `verify_prototype.py`, `finish_adu.py`,
  `prototype/fixtures/make_fixtures.py`, and the probe suite, which copied it
  by path (`probes/suite.py` `ROOT_FILES`) and loaded it from that path for
  contract cases. **Those references were updated in the same PR.** The five
  scripts now `from adu_kit.schema import model_contract`; the suite no longer
  lists it in `ROOT_FILES`, because `make_base()` copies `adu_kit/` whole, and
  its loader reads `suite.CONTRACT`, the new path. A move cannot leave them
  pointing at a file that is gone. What must not change is behaviour: `build_index.py
  --check`, both verify scripts, `make_fixtures.py --check`, every probe case
  and `run_probes.py --self-check` pass and report what they did before. A
  probe **case** (its setup, what it runs, or the message it expects) that has
  to be edited to pass is a behaviour change, and it gets its own PR.
- **Leave the gates where they are.** Several `verify_*.py` scripts embed
  barn-cabin expectations inside otherwise generic checks. They get promoted
  one at a time, in P2 and P3 below, when Laurel proves which assertion was
  about buildings and which was about that building. Rule 29 applies: a gate
  generalised against a typology it has seen once cannot disagree with it.

**The lod2 contract: checked for #126, and only half there.** The lod2
**node** contract is declared per model, in the barn cabin's
`spec.export.lod2_contract`, and `finish_adu.py` compares the export against
it. But nothing asserts origin, axes or the floor datum against a per-model
baseline: besides the node contract, `finish_adu.py` checks only that the
export's width matches the spec (its scale gate). The bounding-box floor
moved when the crawlspace replaced the slab (the page's fixtures record
−0.972 m), and Laurel is slab on grade, so no shared constant can hold it.
Adding that assertion is a new gate, not a move, so it is **not** part of
step 1. It lands with Laurel's export (step 7, #131), which is the first
model whose floor differs.

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

Exit gate: three levels exported with Draco, the lod2 baseline is recorded
**and asserted per model** (origin, axes, units, floor datum; see P0), the
mesh budget gate passes, and **the page takes Laurel with no page code**:

- the manifest passes `identity_problems()` and `display_problems()` (the
  requirements table above), which `finish_adu.py` runs before writing it
- `build_index.py` adds Laurel as a second row of the generated
  `prototype/models.json`, and `build_index.py --check`, `verify_index.py`
  and `verify_prototype.py` pass with **no change to the page's code**
  (`prototype/index.html`, `prototype/app.js`)
- Laurel opens from its front (#117) and loads, frames and orbits in the
  browser, chosen from the model picker
- the probe suite passes. Its cases break the barn cabin deliberately; a
  second row must not change what any of them report.

That closes [#111](https://github.com/captproton/yardstake-ux/issues/111).

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

For the configurator (Tier 2): the stucco / fibre-cement swap is a `sets`
group with linear colours; every layout ships in the file and `presence`
names each node it shows; and a furnished manifest carries a `disclosure`.
Laurel has no loft and no porch, so it has **no** porch layout group and no
`with_porch` footprint. That is not a gap to fill: the page renders the
groups a model has (#111). Its dimensions footprints need positions (#119)
before the overlay is trusted for it.

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

1. [#126](https://github.com/captproton/yardstake-ux/issues/126) **Done** ([#137](https://github.com/captproton/yardstake-ux/pull/137), [#138](https://github.com/captproton/yardstake-ux/pull/138)). Extract the kit, in two PRs: **A** the kernel, export helpers and `inside_mesh()`, with the barn cabin byte-identical and every gate unchanged; **B** `model_contract.py` into `schema/`, its imports, copy list and loader updated, and the page, its fixtures and every probe reporting what they did before.
2. [#127](https://github.com/captproton/yardstake-ux/issues/127) `sheets.py` harvester plus a known-answer test against barn-cabin values already verified by hand.
3. [#128](https://github.com/captproton/yardstake-ux/issues/128) `spec.yaml` P1, with the roof form settled and cited.
4. [#129](https://github.com/captproton/yardstake-ux/issues/129) `build.py` P2 massing and openings.
5. [#130](https://github.com/captproton/yardstake-ux/issues/130) P3 overlay, plus the plate-height gate, proved by perturbation.
6. [#117](https://github.com/captproton/yardstake-ux/issues/117) **Declare the model's front** in the manifest, so the viewer stops assuming +Z. A page change, proved on the barn cabin and the fixtures before Laurel depends on it.
7. [#131](https://github.com/captproton/yardstake-ux/issues/131) P4 materials, the stucco/siding swap, three levels, manifest, baseline. **Laurel lands on the page with no page code; closes [#111](https://github.com/captproton/yardstake-ux/issues/111).**
8. [#132](https://github.com/captproton/yardstake-ux/issues/132) Tier 1 finishes and trim.
9. [#119](https://github.com/captproton/yardstake-ux/issues/119) **Declare where each footprint sits**, so the overlay stops centring. A page change, before Laurel's dimensions are trusted.
10. [#133](https://github.com/captproton/yardstake-ux/issues/133) Tier 2 textures and configurator: `sets`, `presence`, `views`, `dimensions`, `disclosure` meeting the page's contract.
11. [#134](https://github.com/captproton/yardstake-ux/issues/134) Tier 3 fixtures, including the water heater and the mini-split.
12. [#135](https://github.com/captproton/yardstake-ux/issues/135) Furniture and arrangements.

Steps 1 and 2 are the ones that pay for themselves across Richmond and the six
Concord sets. Steps 6 and 9 pay for themselves on every model after Laurel.
Everything else is this building only.
