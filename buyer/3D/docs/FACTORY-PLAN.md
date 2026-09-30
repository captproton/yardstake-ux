# Factory plan: from two hand-built models to many, faster

Written 2026-09-29, after Laurel's twelve steps. It follows
[`KIT-AUDIT.md`](KIT-AUDIT.md), which measured what is general in the code we
have. This document says what to build next, in what order, and how we will know
it worked.

**Status: a plan, not a record.** Nothing below the "Tooling that exists"
section is built. Issue numbers are left blank until issues are filed; the
sequence names them `#TBD`.

## The goal

Make 3D models of permit-ready ADUs faster, and eventually as a repeatable
process (a factory) rather than a project per building. "Faster" needs a
number, so the first job is to measure one:

> **Model three is timed stage by stage.** Laurel took 16 days and 12 steps
> (2026-09-13 to 2026-09-29) and was on the page at step 7. Model three's
> target is *on the page* (Tier A, below) in a small fraction of that. We do
> not set the fraction until Willow has been timed once; guessing it now would
> be the kind of unchecked number this project's specs refuse.

## What the first two models taught

From the [audit](KIT-AUDIT.md) and Laurel's plan:

1. **The time went to detail, not to shipping.** Massing was one PR (step 4).
   Steps 8–12 (trim, fixtures, furniture, canopy) were fidelity. The page
   never needed them to show a building.
2. **A text layer is the biggest saving.** The harvester turns dimension
   strings into positioned candidates. The barn cabin's scan cost 2,927 spec
   lines read by eye.
3. **A builder with no dimension literals is reusable.** Laurel's is 95%
   roof-agnostic; the barn cabin's is one 1,209-line function.
4. **Gates are why the output can be trusted**, and also most of the code
   (51% of Laurel's `build.py`). They must move into the kit, not be rewritten
   per model.
5. **The same decisions were asked repeatedly.** Trim defaults, the
   stucco/siding presence group, reused furniture, what "assumed" means.
6. **Process overhead is real.** One PR per step, a Copilot round of about 7
   minutes (sometimes several), a "Plan:" commit after each.
7. **Environment friction cost time**: a lost scratchpad runner, and a
   `python3` that resolved to Apple's 3.9 without PyYAML.

## Tooling that exists (this change)

Both run from anywhere; both are tested and on the fast gate list.

| Tool | Use | Notes |
|---|---|---|
| [`run_gates.py`](../run_gates.py) | `python3 run_gates.py [--model ID] [--tier fast\|blender\|probes]` | Reads `gates.json` (shared) and `models/<id>/gates.json`. Fast is about 25 s and needs no Blender; Blender is about 15 s; probes take 7–30 min and are opt-in. A skipped gate fails the run unless `--allow-skip`. A Blender gate that exits 0 but prints no PASS line fails. |
| [`new_model.py`](../new_model.py) | `python3 new_model.py PLANS.pdf --id ID --name NAME --issue N` | Intake report first (text layer, sheets, candidate count, class-hint words), then `models/<id>/` with a spec skeleton (sheet index only, no dimension), `docs/INTAKE.md`, `docs/candidates.yaml`, a tiered `docs/PLAN.md`, `gates.json`, `EXPORT_PENDING`. Refuses a scanned PDF without `--allow-raster`; never overwrites. |

A scaffolded model from a plan set whose sheet ids can be read passes
`spec_lint` and every index gate on day one (tested), so it starts green and
stays green. **Not every set starts green.** A scanned set (`--allow-raster`),
and a text-layer set whose sheet ids cannot be read (Concord Plans 3 and 4 name
0 of 55), scaffold an empty `sheet_index.sheets`, which `spec_lint` rejects by
design. Those models start red until a person fills in the index.

CI still runs its own list of steps. Replacing them with
`python3 run_gates.py --tier fast` would put one list in one place; it changes
the PR checks, so it is a separate, deliberate change.

## The plan sets we have

Intake run on every set with `new_model.py --intake-only`, 2026-09-29.

| Set | Plans | Pages | Text layer | Candidates | Sheets named | Roof words |
|---|---|---|---|---|---|---|
| Sacramento | Laurel (built) | 20 | yes | 67 on A-1.0 alone | not measured | one shed plane (settled in its spec) |
| Sacramento | **Willow A2** | 20 | yes | 208 | 15 of 20 | GABLE 11, HIP 3 |
| Concord | Plans 1, 2, 5, 6 | 46–47 | yes | 727–856 | 19 of 46–47 | GABLE ~30, HIP 14, SHED 3 |
| Concord | Plans 3, 4 | 55 | yes | 973–1,086 | 0 of 55 | same |
| Richmond | RAD_1 bungalow, 1-bed | 19 | yes | 207 | 0 of 19 | GABLE 4, HIP 3 |
| Los Angeles | Standard plans A, B, C | 9 each | thin | 160 (A) | 0 of 9 | GABLE 4 |
| That ADU Guy | Barn cabin (built) | scan | **no** | none | by eye | has loft, dormers |

**"Roof words" are hints.** A word on a sheet is not a roof; the spec's
citations decide the roof. Willow's A-2.0 text also shows a `3" / 12"`-style
slope fragment, unconfirmed.

## Why Willow is model three

It is the controlled experiment: it changes **one variable** from Laurel.

- Same designer's sheet system, same sheet ids (A-0.0 … A-3.4, T24), same
  slab-on-grade foundation, stucco and siding options. Laurel's sheet-reading
  scripts, trim and finish decisions should carry over nearly unchanged.
- Different roof: "stick framed and truss roof with composite shingles"
  (A-0.0), against Laurel's one shed plane.
- Its cover sheet also lists a second area beside the main one (the 122 sf
  noted in Laurel's plan), so the option split will recur.

If Willow is slow, the cause is the roof or the process, not a new sheet
system. That is the point of choosing it.

**Not confirmed, and step 1 of Willow's own plan:** its storeys, area, roof
form and pitch, and whether it is a rectangle. If Willow turns out not to be a
one-storey rectangle, this choice is revisited before any code (see the
decision rule below).

**Concord is the larger prize and the wrong first step.** Four of its six
plans look like siblings (46–47 pages each), which is what a factory wants.
But the harvester names only 19 of 46 sheets (0 of 55 on Plans 3 and 4), the
sheet system is not Laurel's, and porches and a garage appear. It goes after
Willow, when the kit has been tested once.

## Approach

The order matters: change the kit first, prove nothing moved, then build the
model on it. Otherwise Willow becomes a fork of Laurel rather than a test of
the kit.

### Phase 0: settle the roof before any code

Read Willow's A-2.0 and cite, in a draft spec section: roof form, pitch,
plate heights, overhangs, ridge height, and the storey count. Decide the
option (plan) to build, as Laurel's `option_selection` did. **Decision rule:**
if Willow is not one storey on a rectangle, stop and re-pick from the table
above before Phase 1.

### Phase 1: the roof becomes a class (kit change, own PR)

Laurel's roof-specific code is 97 lines: `Shed` and the `_roof_*` gates.
Give them an interface (the underside height at a point, the profile of the
roof solid, the gates that follow from the form) and make `Shed` one
implementation.

- **Proof:** Laurel's export is byte-identical before and after, as the kernel
  and finish extractions were (the plan's rule: "move only what knows no
  building").
- **Not before it is needed:** only Willow's gable class is added, and only in
  Phase 3. No speculative hip class.

### Phase 2: the sheet-reading primitives move to `adu_kit/ink.py` (kit change, own PR)

`plan_ink.py` owns the SVG reading (`svg`, `paths`, `segments`, `matrix`,
`frame`); `canopy_ink.py` and `condenser_ink.py` redefine `_runs`, `_bbox` and
`_within`. Move the shared primitives and have all four readers import them.

- **Proof:** each reader's committed output (`spec.plan_overlay`, `fixtures.drawn`,
  `variants.canopy`, the condenser block) is byte-identical, and the existing
  `test_*_ink.py` files pass unchanged.
- **First diff the four readers line by line.** The audit read function lists
  only.

### Phase 3: Willow, Tier A only

Scaffold with `new_model.py` and take Laurel's tier list: A ships, B
upgrades.

| Step | Work | Gate |
|---|---|---|
| A1 | Spec: cite every number; option, frame, roof settled | `spec_lint --pdf`, `verify_spec.py` |
| A2 | Build: slab, walls, partitions, gable roof, every opening cut | Blender build gates; no-literal test |
| A3 | Elevation overlay: named features against A-2.0's ink | `verify_spec.py` overlay gate |
| A4 | Export: one finish, three levels of detail, manifest, index row, front declared; delete `EXPORT_PENDING` | `verify_index.py`, model contract |

**Willow is on the page when A4 is done.** Tier B (interior overlay, trim,
stucco/siding, fixtures, furniture, canopy) are separate PRs decided after the
timing is in. Inherited decisions, applied as defaults and overridden in the
spec, not in code: trim values `assumed` from the barn cabin, exterior finish as
a presence group, furniture reused, `assumed` always with a reason.

### Phase 4: measure, then Concord

Record time per phase. Then answer three questions in this document before
starting Concord:

1. How much of Willow's code was new? (Lines added to `models/willow_*/` and to
   `adu_kit/`.)
2. Which decisions still needed a person, and can each become a kit default?
3. Did the harvester and sheet-id reader cope? Concord needs
   `adu_kit.sheets.sheet_id` to name more than 19 of 46 sheets, so that work is
   scoped from Willow's misses (5 of 20 unnamed) plus Concord's.

Then take **one** Concord plan, and if it goes well, its siblings, which is the
first real throughput test.

## Process changes for the factory

- **Batch the review overhead.** Tier A is one to four PRs, not twelve. Tier B
  items are opt-in and batched by kind.
- **One command to check.** `run_gates.py`; no scratchpad scripts, and it names
  its Python and Blender so an environment problem looks like one.
- **Defaults live in the kit.** A decision asked twice becomes a documented
  default in `adu_kit/`. A person is asked only what the sheets cannot say.
- **The plan is generated.** `new_model.py` writes the tiered `docs/PLAN.md`;
  a person edits it, not authors it.
- **Barn cabin: leave it.** Cheaper than a rewrite: run the literal test
  against `build_adu.py` and move its ~50 literals into the spec.

## Sequence

One line per pull request. Mark each **Done** with its number.

1. `#TBD` **Roof interface** (Phase 1). Laurel byte-identical.
2. `#TBD` **`adu_kit/ink.py`** (Phase 2). Four readers byte-identical.
3. `#TBD` **Willow spec** (A1), including Phase 0's roof decision, scaffolded by
   `new_model.py`.
4. `#TBD` **Willow build**, with the gable class (A2).
5. `#TBD` **Willow overlay** (A3).
6. `#TBD` **Willow export** (A4): Willow is on the page.
7. `#TBD` **Timing and lessons** appended here (Phase 4); then Concord's plan.

Steps 1 and 2 are independent and may run in parallel. Step 3 can start while
they are in review, but its build waits for step 1.

## Risks

- **Willow is not the shape we think.** Mitigated by Phase 0's decision rule.
- **A roof interface designed around one shape.** With only Laurel's shed as
  the existing user, the interface could fit one form. The gable class in step
  4 is the check; expect to revise the interface then, and do not freeze it
  before.
- **"Faster" measured on one model is noisy.** It is one data point, and Willow
  shares Laurel's sheet system. Concord is the test that generalises.
- **Byte-identical proofs are strict.** A moved function that changes
  float ordering fails them; that is the intended behaviour, not a nuisance.
- **The harvester reads only text.** A scanned set (like the barn cabin's)
  remains the slow path, and `new_model.py` flags it up front instead of hiding
  it.

## Out of scope for now

A generic builder for lofts, dormers and crawlspaces (the barn cabin's class);
OCR for scanned sets; drawing several footprints at once on the page; changing
CI's step list.
