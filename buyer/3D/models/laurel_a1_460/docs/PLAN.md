# laurel_a1_460 — build plan

Second ADU model. Subject: **Sacramento County Permit Ready ADU, Model A1
"Laurel", 460 sf**, from
[`../../../example plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf`](../../../example%20plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf)
(20 sheets, Laura Miller Design, El Dorado Hills CA; drawn 2024-04-04;
2022 California Residential Code).

**The sheet set is in git** (13.65 MB), because this model and the
harvester's tests depend on it; `buyer/3D/.gitignore` un-ignores it alone. The
rest of `example plans/sacramento_adus/` is still ignored, including
`a1-laurel-rendering.jpg`, which exists only in the main working tree.

This plan assumes the ladder, the gates and the ground rules from
[`../../barn_cabin_524/docs/README.md`](../../barn_cabin_524/docs/README.md).
Read its ground rules (1–42) before writing anything here. Nothing below repeats them.

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

**Updated 2026-09-23, after step 4
([#148](https://github.com/captproton/yardstake-ux/pull/148)).** Four decisions
were settled before the steps that need them:
- **Trim:** the barn cabin's ten trim values become Laurel's declared
  `assumed` defaults, with exterior trim for siding and none for stucco
  ([Tier 1 trim](#tier-1-trim--the-barn-cabins-values-declared-assumed)).
- **Interior checks:** the interior gets an overlay against A-1.0 of its own
  ([P3b](#p3b--overlay-against-the-a-10-plan)).
- **Overlay tolerance:** it is 0.5" per named feature (P3).
- **Colour:** one rendering and no second source (P4).

Issue [#132](https://github.com/captproton/yardstake-ux/issues/132) carries all
four as done-when items.

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
| Roof overhang | 5'-0" front (over the entry); 1'-6" rear and both ends | A-2.0 roof plan |
| Elevation scale | 1/4" = 1'-0" | A-2.0 front elevation title |
| Ceilings | follow the roof line (vaulted) | A-1.0 note |
| Entry canopy | optional, 2x6 cedar frame, 1x6 trim | A-3.4 |
| Windows | vinyl, SHGC 0.21 | A-0.0, window notes |

**Two top-plate heights and an upper/lower roof split: one shed roof.** A-2.0
sizes attic ventilation separately for an "upper roof" and a "bottom roof",
110.16 square inches each, and marks T.P. 1 and T.P. 2. This plan first read
that as **two roof planes**. P1 (#128) settled it the other way: **one shed
roof**, falling 1" per foot from T.P. 2 (9'-7 1/2") at the front wall to T.P. 1
(8'-0") at the rear. Both side elevations draw one plane, the rear elevation
shows only T.P. 1, the roof plan has one slope arrow, "upper" and "bottom" are
its high and low eaves vented in the same 12 rafter bays, and S1.0 frames it
with one run of 2x12 rafters in a drawing file named "SHED ROOF". See
`spec.yaml` `roof.settled` and the discrepancy
`the-roof-is-one-shed-not-two-planes`.

**There is an option split, as there was for the barn cabin.** A-1.0 carries a
"1 bedroom floor plan option", and the Willow A2 cover sheet lists a second
area of 122 sf beside the 460. Decide and record the chosen option in
`spec.yaml` under `option_selection` with the same reasoning format used for
the barn cabin's Option B, and note that the unchosen option is a candidate for
the variants manifest later, not a second model. **Decided (2026-09-14): the
studio is built; the one-bedroom plan is a future configurator choice** (#133),
recorded under `variants.floor_plan_options`.

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

- ~~**The front faces +Z.**~~ **No longer assumed** ([#117](https://github.com/captproton/yardstake-ux/issues/117),
  step 6, done). The manifest declares the front, and the export proves it.
  Laurel's is `-z`, and without #117 it would have opened showing its back.
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
  generic (step 7, #131). **Moved in [#153](https://github.com/captproton/yardstake-ux/pull/153)**,
  step 7's PR A: `adu_kit/finish.py`, `publish.py` and `manifest.py`, with
  the barn cabin's export byte-identical. Glazing, furniture presence, the
  dimensions block and the scale gate stay with the barn cabin.

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

**The harvester is built** ([#127](https://github.com/captproton/yardstake-ux/issues/127)):
`python3 -m adu_kit.sheets "example plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf" --pages 4,6 --out candidates.yaml`,
run from `buyer/3D`. What
reading Laurel's sheets showed:

- **Dimensions come out in pieces.** `24'`, `-`, `0"` on one line for a
  horizontal dimension, the same pieces stacked for a vertical one. The
  harvester stitches them by position: A-1.0 yields 67 feet-and-inches
  dimensions (45 horizontal, 18 vertical, 4 already one word), A-2.0 yields
  34, and every page matches a plain `pdftotext -layout` search.
- **Some need care:** negative elevations (`-0' - 6"`, grade below the
  floor), lengths in parentheses in notes (`(6'-1" TO 10'-0")`), and a length
  glued to a rebar callout (`2-NO.5X4'-0"`).
- **Sheet ids** come from the title block for A-0.0 to A-3.5 and T24-1 to
  T24-4. The four structural pages are portrait with the title block turned,
  so their candidates carry `sheet: null`; cite them by page.
- **Inch-only strings are not harvested** (`6"`, `1/4":12"`). On these sheets
  they are mostly notes, spacings and slopes.
- **Known answers:** the parser agrees with 175 of the barn cabin's 183
  hand-read lengths exactly. Seven more are `ft` values measured, assumed or
  derived, whose `raw` is only the nearest fraction; `6x6` is a lumber size.
  The test lists both, so a new disagreement fails.

What it was built to do:

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
  **Settled: one shed roof** (above).
- The **overall footprint**, which 460 sf does not determine on its own. A
  24'-0" dimension and a 13'-2" dimension both appear on A-1.0; neither is
  confirmed as an overall. **Settled: 24'-0" x 19'-2" to face of stud**, 460.0 sf
  exactly; 13'-2" is grid 1 to grid 2.
- The **height datum**. Slab on grade means finished floor sits near grade, so
  the barn cabin's finished-floor-versus-grade ambiguity should not recur, but
  it must be stated explicitly rather than assumed absent.
- The **window and door schedules** on A-1.0. Both exist as tables; page
  coordinates are what will reconstruct their rows, since reading order alone
  scrambles them.
- **Wall assembly thickness** for 2x6 exterior and 2x4 interior, from A-3.x.

Exit gate: every numeric value has a `source:`, and a spec-lint gate rejects
any key that carries a number without one. **Built as `adu_kit/spec_lint.py`**:
every number cites a sheet (or shows its arithmetic, or says why it is
assumed), every source names a listed sheet, and every drawn feet-and-inches
length is a dimension the harvester finds on the sheet it cites. CI runs it.
Until Laurel exports, `models/laurel_a1_460/EXPORT_PENDING` names #131, so the
index gates list it as pending rather than failing.

---

## P2 — massing and openings

Write `build.py` for this typology only. It calls the kit kernel and reads
`spec.yaml`. No dimension appears in the file.

Scope: slab, exterior and interior walls, the shed roof with a 5'-0" front and 1'-6"
overhangs, vaulted ceilings that follow the roof line, and window and door
openings cut from the schedule.

The optional entry canopy moved out to #144. A-2.0 marks it "OPTIONAL CANOPY
SEE A-3.4", but A-3.4 has not been harvested, so `spec.yaml` records it under
`variants.canopy` with a citation and no dimensions — nothing a build that
carries no dimension literals can use. It is optional on the drawings and the
exit gate below does not need it.

Promote from the barn cabin, unchanged where possible: the opening cutter and
sash construction from the declared window type. These were the subject of
four PRs and are the most battle-tested code in the project.

**Exterior casing, interior stools and aprons, and reveal marking move to
[#132](https://github.com/captproton/yardstake-ux/issues/132).** They need
`spec.trim` — casing width, head casing height, baseboard height, stool
projection and thickness, two apron heights, sill projection and thickness,
and the reveal material — and Laurel's sheets dimension exactly ONE of them,
the 3/8" reveal at the metal casing bead on A-3.0 details 3 and 4, which the
spec already carries. #129 declined to write the other ten as `assumed` just
to finish P2, and left them for #132, the step named for trim.
Parameterising those helpers with only one caller would also have meant
guessing at an interface; the sash had two the moment it moved, which is what
made its shape obvious. Recorded on #129.

**Where the ten values come from is decided (2026-09-23), and this replaces
#129's hope of reading them off A-3.0 and A-3.2:** #132 takes the barn
cabin's values as declared `assumed` defaults. See
[Tier 1 trim](#tier-1-trim--the-barn-cabins-values-declared-assumed), the one
place that decision lives.

Do **not** call: dormers, knee walls, loft subfloor, ladder, guardrail,
crawlspace stemwall, vents, piers, porch posts.

Exit gate: the geometry gates pass, and the opening gate confirms every
schedule row produced a cut opening with a sash.

---

## P3 — overlay calibration against A-2.0

Same method that settled the barn cabin ridge, and it is the phase that will
catch a wrong roof reading.

Render the model orthographically at the sheet's stated 1/4" = 1'-0" and
compare it with A-2.0.

**The tolerance is 0.5" per feature**, recorded as
`spec.elevation_overlay.tolerance_in` (set in #130, PR
[#147](https://github.com/captproton/yardstake-ux/pull/147)). Every named
feature must fall within it individually. The drawing's own roof line sits
about 1/4" below its labelled T.P. datums, so the model cannot agree more
closely than that.

**Compare named features, not silhouettes** (changed in #130, PR
[#147](https://github.com/captproton/yardstake-ux/pull/147)). A per-column
silhouette diff gives a mean and a standard deviation that depend on whether
the crop caught every dimension line, leader and datum. They look
authoritative either way. Instead, measure individual features off A-2.0
rasterised at 400 dpi (100 px/ft): the roof underside at each wall, the
overhang, and each window's sill, head and edges. Record them in
`spec.elevation_overlay` as cited numbers, and have `verify_spec.py` compare
them against what A-1.0's strings put in the same place. That runs in CI with
no Blender. Each residual is held to the 0.5" per-feature tolerance.

Add one gate this model needs and the barn cabin did not: **the single roof
plane passes through T.P. 2 at the front wall and T.P. 1 at the rear** (it was
first written for two planes; P1 found one). Prove it can fail by moving T.P. 2
an inch and confirming the gate goes red. Rule 19 — a red test that
moves the spec proves nothing — means perturb the *build*, not the spec.

**What P3 cannot reach.** An elevation shows the outside. Door 5's position,
doors 3 and 4 centred in their clear spans, and every partition running to the
roof underside appear on no elevation, so no overlay against A-2.0 tests them.
They belong to [P3b](#p3b--overlay-against-the-a-10-plan).

---

## P3b — overlay against the A-1.0 plan

The same named-feature method, pointed at the floor plan. It is the only step
that tests the interior against a drawing. It lands with Tier 1 in
[#132](https://github.com/captproton/yardstake-ux/issues/132), as that step's
first PR ([#155](https://github.com/captproton/yardstake-ux/pull/155)), ahead of
the trim, because it moves the walls and doors the trim wraps.

**Done (#155).** It was read from A-1.0's **vectors**, not a raster:
`plan_ink.py` has `pdftocairo` write the page as SVG, registers the frame on the
19'-2" and 24'-0" strings' own ticks (each pair confirmed by its label in the
text layer), and reads a partition as the pair of 0.48 pt stud-face lines 3 1/2"
apart and a door as its gap's centre. It found three walls (P_block_W,
P_laundry_W, P_laundry_E) half an inch off and door 2 4 1/2" off, and resolved
the "half inch in the interior strings" discrepancy: the strings never
disagreed. Partition height stays `assumed` with a `what_would_settle_it`, since
no section on A-3.0 to A-3.5 cuts a partition. The plan below is kept as written.

A-1.0 is vector, and the harvester already returns every string with its page
rectangle, so the plan's scale and origin come from the sheet's own dimension
strings rather than from a guess. Measure where the ink is **drawn**, not
where a string implies it is:

- **door 5's leaf and opening.** The 3'-9" string beside it resolves onto no
  pair of faces, so the drawn position is the only evidence there is;
- **doors 3 and 4**, to test whether "centred in the clear span" is what the
  drawing shows;
- **each of the seven partitions' faces**, against the five interior strings
  read outside face to outside face.

A plan cannot show height, so "every partition runs to the roof underside"
stays open until a section settles it. Look for one on A-3.0 and A-3.2 in the
same step. If neither sheet draws one, record that the question cannot be
settled from these sheets, as the barn cabin did for its interior ledges.

Exit gate: every `assumed` interior position either becomes `measured` with a
residual inside P3's 0.5" per-feature tolerance, or stays `assumed` with a
`what_would_settle_it:`. At least one committed probe must move a partition in
the **build** and turn the gate red.

---

## P4 — materials, levels of detail, export

Kit code does nearly all of this.

Model-specific work is the material set: standing seam metal roofing, and
stucco. **Stucco and fibre-cement lap siding are a finish variant, not a
decision** — the sheet offers both — **but P4 ships stucco alone** (decided
2026-09-24). The page's `sets` can swap only `baseColorFactor`, so until #133
adds textures a "Lap siding" option would be smooth stucco in another colour:
an option labelled for something the buyer cannot see. P4 ships stucco with
an exterior-colour set, and the stucco/siding swap arrives in #133 with the
siding texture and the siding trim. It was never purely a material swap
once exterior trim arrives in Tier 1; see
[Tier 1 trim](#tier-1-trim--the-barn-cabins-values-declared-assumed).

**Colour.** `a1-laurel-rendering.jpg` is the only appearance source Laurel
has. There is no tour video, and the file lives only in the main working tree
because `example plans/sacramento_adus/` is ignored. Treat it as follows:

- Use it for colour only, never geometry (rule 5's principle, applied to a
  rendering).
- Crop and look at every sample before measuring it (rule 4). A "siding" patch
  was once the pollinator garden.
- Record each default colour as `assumed`, citing the rendering and the
  crop. Stucco and siding are options the buyer chooses, so a default colour
  is a sensible starting point, not a claim about the building.
- Where the rendering does not show a material, choose a neutral default and
  say so. Do not reach for a second image.

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

### Tier 1 trim — the barn cabin's values, declared assumed

**Decided 2026-09-23.** Laurel's sheets dimension one of the eleven trim
numbers #132 needs: the 3/8" reveal at the metal casing bead, which the spec
already carries. [#132](https://github.com/captproton/yardstake-ux/issues/132)
takes the other ten from the barn cabin's `spec.trim`. Each value is written
into Laurel's `spec.trim` as `confidence: assumed` and cites the barn-cabin
key it came from.

**Confidence does not cross buildings.** Some of these were `measured` on the
barn cabin's A1.1. On Laurel every one of them is `assumed`, because nothing
on Laurel's sheets measured it. The note says what the barn cabin's evidence
was. It does not inherit that evidence's standing.

| Laurel `spec.trim` key | value | barn cabin source (its confidence) | applies to |
|---|---|---|---|
| `casing_width` | 3 1/2" | `trim.casing_width` (measured_approx) | interior casing; siding exterior casing |
| `head_casing_height` | 4 5/8" | `trim.head_casing_height` (measured) | interior casing; siding exterior casing |
| `baseboard_height` | 3 1/2" | `trim.baseboard_height` (assumed) | interior, both finishes |
| `interior_stool_projection` | 7/8" | `trim.interior_stool_projection` (assumed) | interior, both finishes |
| `interior_stool_thickness` | 3/4" | `trim.interior_stool_thickness` (assumed) | interior, both finishes |
| `interior_apron_height` | 3 1/2" | `trim.interior_apron_height` (assumed) | interior, both finishes |
| `exterior_sill_thickness` | 2" | `trim.exterior_sill_thickness` (measured) | siding only |
| `exterior_sill_projection` | 1 1/2" | `trim.exterior_sill_projection` (assumed) | siding only |
| `exterior_apron_height` | 3 5/8" | `trim.exterior_apron_height` (measured_approx) | siding only |
| `reveal_material` | trim | `trim.reveal_material` | siding only; see below for stucco |

**The two finishes trim a window differently.** This is the one place the
stucco/siding swap is not purely a material change:

- **Lap siding:** A-3.2 details 3 and 4 draw FIBER CEMENT TRIM at the vinyl
  window head and sill. Build the exterior casing, sill and apron from the
  defaults above.
- **Stucco:** A-3.0 details 3 and 4 finish the opening with a METAL CASING
  BEAD and a 3/8" reveal. They show no trim board. Build **no** exterior
  casing, sill or apron. The reveal takes the stucco material, `assumed`,
  because the bead ends the plaster at the frame.

The interior is the same under both finishes. Its trim is not a variant.

**Open question for [#133](https://github.com/captproton/yardstake-ux/issues/133),
with [#113](https://github.com/captproton/yardstake-ux/issues/113).** The page
keeps `sets` (colours) and `presence` (nodes shown) as independent groups, so
choosing a finish cannot show or hide the siding trim. The choices are:

- a presence group for the exterior finish that sits beside the colour set,
  which lets a buyer pair siding colours with stucco trim;
- a contract change linking the two, which is a page change;
- or always showing the siding trim, which is wrong for stucco.

#132 does not decide this. It builds the siding exterior trim as its own
named nodes, so any of the three can use them.

**What would settle it.** A-3.2 details 3 and 4 are drawn at 6" = 1'-0". That
is twenty-four times the elevations' scale, and fine enough to measure the
fibre-cement trim's width and sill thickness from the ink. A measurement taken
there supersedes the default. #132 is not required to take it.

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

For the configurator (Tier 2): the stucco / fibre-cement swap, moved here
from P4 so it lands with the siding texture and trim that make it visible; every layout ships in the file and `presence`
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
2. [#127](https://github.com/captproton/yardstake-ux/issues/127) **Done** ([#141](https://github.com/captproton/yardstake-ux/pull/141)). `sheets.py` harvester plus a known-answer test against barn-cabin values already verified by hand: 175 of 183 agree exactly, the other 8 are listed with reasons; A-1.0 gives 67 candidates and A-2.0 gives 34, with exact inches; the tests run in CI against the versioned sheet set.
3. [#128](https://github.com/captproton/yardstake-ux/issues/128) **Done** ([#142](https://github.com/captproton/yardstake-ux/pull/142)). `spec.yaml` P1, with the roof form settled and cited: one shed roof, not two planes; the studio plan, with the 1-bedroom recorded as a future configurator choice; 132 numbers, every one cited. In CI, `adu_kit/spec_lint.py` finds each drawn length on the sheet it cites, and `verify_spec.py` checks that openings follow from their dimension strings and that the frame is not mirrored, with a test for each gate. Open: [#143](https://github.com/captproton/yardstake-ux/issues/143), two lint gaps Laurel's spec does not hit (numeric keys are not checked; a recursive YAML alias crashes the lint). [#145](https://github.com/captproton/yardstake-ux/issues/145), whether the barn cabin's frame is mirrored the way this spec's first draft was, is **settled** ([#149](https://github.com/captproton/yardstake-ux/pull/149)): it is not. `verify_frame.py` now holds the barn cabin's mesh to A1.1's left and right, reading no compass label.
4. [#129](https://github.com/captproton/yardstake-ux/issues/129) **Done** ([#146](https://github.com/captproton/yardstake-ux/pull/146)). `build.py` P2 massing and openings: slab, four walls, seven partitions, the single shed roof with its overhangs, and all fifteen openings cut with a sash from the declared operation or a leaf — door 1 as a leaf AND its glazed sidelite. The two things P2 had to settle are settled and cited: cladding is modelled at ZERO, so the stucco/siding swap stays a material change and cannot move the building's faces, with the geometry stopping at S1.0's 3/8" sheathing; and the five interior strings read outside face to outside face, which is where the partitions come from. `sash_geom` promoted into `adu_kit/kernel.py`, the barn cabin byte-identical. 11 Blender gates, and `test_build_literals.py` holds the no-dimension-literal rule in CI without Blender. 185 numbers cited (was 132), 19 `verify_spec` gates, 26 tests. Four review rounds, 22 findings, 20 real — most of them in the GATES rather than the building; see the PR's summary comment. The optional entry canopy moved out to [#144](https://github.com/captproton/yardstake-ux/issues/144) and the casing, stools and aprons to [#132](https://github.com/captproton/yardstake-ux/issues/132), both for the same reason: the sheets do not dimension them.
5. [#130](https://github.com/captproton/yardstake-ux/issues/130) **Done** ([#147](https://github.com/captproton/yardstake-ux/pull/147)). P3 overlay against A-2.0, and the plate-height gate, which #129 had already built against the roof mesh and #130 inherited. **The overlay found the roof edge 2.47" too thick.** The build had extruded S1.0's 2x12, where both elevations draw a 9 1/4" edge (the fascia). With 9 1/4", the 10'-9 1/2" roof height at the front edge reconciles to 0.02". It was found by measuring A-2.0 at 400 dpi rather than trusting the model's own arithmetic, and it is caught from now on by a new Blender gate on that height.
   - **The method:** named features, not a silhouette diff. `spec.elevation_overlay` records A-2.0's ink as cited numbers, and `verify_spec.py` compares it with A-1.0's strings in CI at 0.5" per feature. No residual exceeded 0.4".
   - **The renderer:** `render_elevations.py` writes A-2.0's four views at 100 px/ft with a manifest. It fails when a view's ink is narrower than its wall, and never leaves a stale manifest behind.
   - **The probes:** the roof perturbations are committed as probes, and the harness runs any model in `BLENDER_MODELS`.
   - **The reviews:** three review rounds, and the same failure four times over: a check that passes by not running. A `.get()` that let the block vanish, an `if ov:` that let it be empty, a renderer that printed success over blank images, and a manifest that outlived a failed run.
   - **Open:** the four interior `assumed` numbers appear on no elevation. They moved to P3b, in step 8.
6. [#117](https://github.com/captproton/yardstake-ux/issues/117) **Done** ([#150](https://github.com/captproton/yardstake-ux/pull/150)). **The model declares its front**, and the page stops assuming +Z.
   - **Declared:** `front` (`+x`, `-x`, `+z`, `-z` in the glTF frame) is required in the identity and every index row. The barn cabin declares `+z`, with its entry door as the witness.
   - **Proved against the file:** `model_contract.front_problems()` reads the `.glb` and requires the entry node to sit nearer the declared end than any other. `finish_adu.py` refuses to publish a wrong front, and `verify_index.py` gate 9 checks it again in CI.
   - **Faced by the page:** the first view, the sun and the dimension overlay come from one basis built from `front`. For `+z` it reproduces the old constants exactly. `fixture_side_entry_box` opens from +X with no code knowing it.
   - **The axis notes were wrong**, not the exporter: they described the mirrored P2 build.
   - **The reviews** found the same thing again, a check that passes by not running, in four forms: a malformed manifest that crashed gate 9, a nested file the check could not place, a page that borrowed a missing front, and a gate comparing names but not directions. #149 found a fifth: **Blender exits 0 on an uncaught exception**, filed as [#151](https://github.com/captproton/yardstake-ux/issues/151) and fixed in [#152](https://github.com/captproton/yardstake-ux/pull/152): the probe harness and every documented Blender command pass `--python-exit-code 1`, and a probe proves a crash exits non-zero.
7. [#131](https://github.com/captproton/yardstake-ux/issues/131) **Done**, in two PRs. **Laurel is on the page, with no page code; [#111](https://github.com/captproton/yardstake-ux/issues/111) closed.**
   - **PR A ([#153](https://github.com/captproton/yardstake-ux/pull/153)):** the export machinery both models need moved into `adu_kit/` (`finish.py`, `publish.py`, `manifest.py`), with the barn cabin byte-identical and the manifest blocks tested in CI. Review hardened it: a malformed spec is a named problem, never a traceback, and `export/` holds exactly one generation.
   - **PR B ([#154](https://github.com/captproton/yardstake-ux/pull/154)):** `models/laurel_a1_460/finish.py`. It adds glass, three Draco levels (lod0 38 KB, lod1 29 KB, lod2 8 KB), a ten-node lod2 contract, and a manifest that faces `-z` with `Leaf_D-1`. `prototype/models.json` gains its second row, and `index.html` and `app.js` are unchanged.
   - **Materials: stucco only** (decided 2026-09-24; the swap moves to #133). Every colour is `assumed` and cites its rendering crop. The rendering is lit at golden hour, so the hue is sampled and the albedo is plausible.
   - **The lod2 baseline is asserted per model**, for both: `model_contract.baseline_problems()` holds origin, axes, units and floor to values derived from each spec (Laurel −0.1016 m, the barn cabin −0.9717 m). Non-finite values are refused.
   - **Verified in the browser** from the model picker: Laurel opens from its front, fits, swaps colours, shows its interior, and draws its dimensions along the front.
   - **Known, and #119's:** the overlay centres the footprint on the model's box, and Laurel's 5'-0" front overhang pulls it 0.53 m forward of the walls. The legend also says "Ridge" for a shed roof's top.
8. [#132](https://github.com/captproton/yardstake-ux/issues/132) **In progress, two PRs** (decided 2026-09-24: P3b first, because it moves what the trim wraps).
   - **PR A done ([#155](https://github.com/captproton/yardstake-ux/pull/155)): [P3b](#p3b--overlay-against-the-a-10-plan), the interior against A-1.0's ink, read as vectors to hundredths of an inch.** Three partitions moved +1/2", door 2 moved 4 1/2" to its drawn centre, doors 3 and 5 about 1/2"; door 4 confirmed. The 5'-2", 7'-3", 3'-2" and 3'-9" strings, the closet and the ink now agree within 0.05", and the interior-strings discrepancy is resolved.
   - **Its gates:** `spec.plan_overlay` records the drawn faces and door centres; `verify_spec.py` holds the layout to them (0.5" per feature), `test_plan_ink.py` re-measures A-1.0 on every CI run, and `build.py` holds the **built** mesh to them, so a wrong spec and a build that follows it no longer pass together. `probes/cases_plan.py` moves a wall and a door in the build and turns it red. Probes 177.
   - **Review** hardened the reader: any SVG transform spacing parses, and the frame is measured from the ticks the drawing carries, each pair confirmed by its label, so a moved page or a neighbour's tick is refused rather than misread.
   - **PR B next:** Tier 1 finishes and trim, using the [barn cabin's trim values, declared `assumed`](#tier-1-trim--the-barn-cabins-values-declared-assumed): interior casing, baseboard, stool and apron, the floor finish, and the siding exterior trim built as its own nodes but not exported until #133 (decided 2026-09-24); none under stucco.
9. [#119](https://github.com/captproton/yardstake-ux/issues/119) **Declare where each footprint sits**, so the overlay stops centring. A page change, before Laurel's dimensions are trusted.
10. [#133](https://github.com/captproton/yardstake-ux/issues/133) Tier 2 textures and configurator: `sets`, `presence`, `views`, `dimensions`, `disclosure` meeting the page's contract.
11. [#134](https://github.com/captproton/yardstake-ux/issues/134) Tier 3 fixtures, including the water heater and the mini-split.
12. [#135](https://github.com/captproton/yardstake-ux/issues/135) Furniture and arrangements.

Steps 1 and 2 are the ones that pay for themselves across Richmond and the six
Concord sets. Steps 6 and 9 pay for themselves on every model after Laurel.
Everything else is this building only.
