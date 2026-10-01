# Factory plan: from two hand-built models to many, faster

Written 2026-09-29, after Laurel's twelve steps. It follows
[`KIT-AUDIT.md`](KIT-AUDIT.md), which measured what is general in the code we
have. This document says what to build next, in what order, and how we will know
it worked.

**Status (2026-10-01).** The tooling is built and merged
([#165](https://github.com/captproton/yardstake-ux/pull/165), `aaa4672`):
`run_gates.py`, `new_model.py`, 29 tests, and the audit. Phase 0 (the Willow
preflight) is done, in [`WILLOW-PREFLIGHT.md`](WILLOW-PREFLIGHT.md), merged in
[#166](https://github.com/captproton/yardstake-ux/pull/166). Everything from
Phase 1 on is still a plan. The sequence's steps are filed as issues
[#167](https://github.com/captproton/yardstake-ux/issues/167) to
[#174](https://github.com/captproton/yardstake-ux/issues/174).

**Open after #165:**
- **The new tests are not in CI**
  ([#175](https://github.com/captproton/yardstake-ux/issues/175)).
  `.github/workflows/buyer-3d-checks.yml` keeps its own step list and does not
  run `test_run_gates` or `test_new_model`, so a regression in either tool can
  merge unseen. Adding them is two steps (the workflow already installs poppler
  and PyYAML); it was left to the maintainer because it changes the workflow.

**What #165 taught about tooling work.** Nine review rounds, nearly all on how
`run_gates.py` and `new_model.py` treat malformed input: a manifest that is a
list, a command with a NUL, a field the tier ignores, an empty selection. Each
fix was small. The next tool that reads a manifest from disk should start from
that list, with a test per malformed shape written before the code, not found
one round at a time.

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

## Tooling that exists (merged in #165)

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
| Sacramento | **Willow A2** | 20 | yes | 208 | 15 of 20 | GABLE 11, HIP 3 (read on the sheets: a main gable and a porch gable; no hip roof found) |
| Concord | Plans 1, 2, 5, 6 | 46–47 | yes | 727–856 | 19 of 46–47 | GABLE ~30, HIP 14, SHED 3 |
| Concord | Plans 3, 4 | 55 | yes | 973–1,086 | 0 of 55 | same |
| Richmond | RAD_1 bungalow, 1-bed | 19 | yes | 207 | 0 of 19 | GABLE 4, HIP 3 |
| Los Angeles | Standard plans A, B, C | 9 each | thin | 160 (A) | 0 of 9 | GABLE 4 |
| That ADU Guy | Barn cabin (built) | 7 | **no** (a scan) | none | by eye | has loft, dormers |

**"Roof words" are hints.** A word on a sheet is not a roof; the spec's
citations decide the roof. Willow's A-2.0 text also shows a `3" / 12"`-style
slope fragment, unconfirmed.

## Why Willow is model three

It is the closest thing we have to a controlled experiment: the verified
differences from Laurel are mainly the roof and the porch (the door and window
schedules and the interior layout are not yet compared; that is step 4). The
preflight ([`WILLOW-PREFLIGHT.md`](WILLOW-PREFLIGHT.md)) found
the roof is a bigger difference than first assumed.

- Same designer's sheet system, same sheet ids (A-0.0 … A-3.4, T24), same
  slab-on-grade foundation, same 24'-0" by 19'-2" footprint, stucco and siding
  options. Laurel's sheet-reading scripts, trim and finish decisions should
  carry over where the sheets match; that is checked sheet by sheet at step 4,
  not assumed.
- Different roof: "stick framed and truss roof with composite shingles"
  (A-0.0). The preflight read **two roofs**, not one: a main gable at 5:12 on
  trusses, and a small porch gable at 3:12 on posts and a beam, against Laurel's
  one shed plane. Its walls stop at T.P. 8'-0", and its ceiling is probably
  flat at the plate (an attic sits above; not confirmed), where Laurel's run to a
  vaulted roof.
- A 1-bedroom plan option is drawn on A-1.0, as in Laurel's, so the option
  split recurs. (The 122 sf on the cover sheet is the **covered porch**, outside
  the 460 sf; an earlier version of this plan read it as a second plan area.)

If Willow is slow, the cause is the roof or the process, not a new sheet
system. That is the point of choosing it.

**Confirmed by the preflight:** one storey, 460 sf, a 24'-0" by 19'-2"
rectangle, and the roof forms (main gable and porch gable). **Still open, and
settled at step 4 (the spec):** the heel height, where the porch roof meets the
main roof, which overhang is where, the frame, and **the ceiling form** (flat
at the plate is likely, but no ceiling plan or section was found; see the
preflight). The decision rule below was applied and Willow passed it.

**Concord is the larger prize and the wrong first step.** Four of its six
plans look like siblings (46–47 pages each), which is what a factory wants.
But the harvester names only 19 of 46 sheets (0 of 55 on Plans 3 and 4), the
sheet system is not Laurel's, and porches and a garage appear. It goes after
Willow, when the kit has been tested once.

## Approach

The order matters: change the kit first, prove nothing moved, then build the
model on it. Otherwise Willow becomes a fork of Laurel rather than a test of
the kit.

**The order is by dependency, and differs from the audit's list.**
[`KIT-AUDIT.md`](KIT-AUDIT.md) lists the extractions smallest-first (ink,
gates, roof). This plan puts the roof first because the roof interface is what
decides which of Laurel's gates are roof-specific (97 lines) and which know no
roof (the rest of the 889), so the gates cannot be split cleanly before it
exists. The sheet-reading move is independent of both. So: roof (Phase 1), ink
(Phase 2, may run in parallel), gates (Phase 3, after Phase 1), then Willow.

### Phase 0: settle the roof before any code

Read Willow's A-2.0 and A-0.0 and apply the decision rule. **Phase 0's outputs
are the read and the verdict:** the roof forms, the plate and top-of-roof
heights, and the storey count, with where each came from. **Decision rule:** if
Willow is not one storey on a rectangle, stop and re-pick from the table above
before Phase 1.

**Deferred to A1 (the spec), on purpose:** citing each number into `spec.yaml`,
choosing the plan option (as Laurel's `option_selection` did; the 1-bedroom
option is drawn on A-1.0), and settling the overhangs, the heel height, the
porch roof's junction, the frame and the ceiling form. None of them changes
whether Willow is the right model or what Phase 1 must support, so they do not
hold up Phase 1.

**Done 2026-10-01, in [`WILLOW-PREFLIGHT.md`](WILLOW-PREFLIGHT.md): Willow passes**
(one storey on a 24'-0" by 19'-2" rectangle). The findings are a read, not a
spec.

### Phase 1: the roof becomes a class (kit change, own PR)

Laurel's roof-specific code is 97 lines: `Shed` and the `_roof_*` gates.
Give them an interface and make `Shed` one implementation.

**The interface is a list of roof planes, each with its extent, not one
surface.** The preflight is why. Laurel's `Shed` answers "underside height at
this Y", which is one plane. Willow is a main gable and a porch gable that
meet, so a function of position cannot say which roof covers a point. Design for
a list of planes (with slope, extent and overhangs), with Laurel as a list of
one, and have the interface answer: the underside at a point, the solid's
profile, and the gates that follow from the form. Also separate **ceiling from
roof**, as a general requirement: Laurel's partitions run to the roof (vaulted
ceilings), and a truss roof over an attic would stop them at a ceiling below it.
Whether Willow's does is **not settled**: the preflight found evidence for a flat
ceiling at the plate (an attic sits above, per A-2.0's attic-access note) but no
ceiling plan, section or truss profile. Do not design Phase 1 around Willow's
partition termination until step 4 confirms the ceiling form.

- **Proof:** Laurel's export is byte-identical before and after, as the kernel
  and finish extractions were (the plan's rule: "move only what knows no
  building").
- **Not before it is needed:** only Willow's gable class is added, and only in
  Phase 4. No speculative hip class.

### Phase 2: the sheet-reading primitives move to `adu_kit/ink.py` (kit change, own PR)

`plan_ink.py` owns the SVG reading (`svg`, `paths`, `segments`, `matrix`,
`frame`); `canopy_ink.py` and `condenser_ink.py` redefine `_runs`, `_bbox` and
`_within`. Move the shared primitives and have all four readers import them.

- **Proof:** each reader's committed output (`spec.plan_overlay`, `fixtures.drawn`,
  `variants.canopy`, the condenser block) is byte-identical, and the existing
  `test_*_ink.py` files pass unchanged.
- **First diff the four readers line by line.** The audit read function lists
  only.

### Phase 3: the gates move into the kit (kit change, own PR, after Phase 1)

Gates are 889 of the 1,762 lines in Laurel's `build.py`, and most take
`(spec, geo)` and know no roof. If Willow copies them, the factory pays for
them again with every model, and they drift. Move the roof-agnostic gates
(`_every_row_built`, `_openings_on_the_wall_their_block_names`, the trim,
fixture, furniture, canopy and condenser gates, `report`) behind a small `geo`
contract; leave the `_roof_*` gates with the roof class.

**Caution from the preflight:** "knows no roof" is not the same as "holds for any
ceiling". Gates that assume a partition reaches the roof (Laurel's vaulted
ceilings) may not hold for a model with a ceiling below its roof, which Willow's
probably is (unconfirmed). When moving a
gate, check whether it reads the roof or the ceiling, and move it behind the
ceiling/roof split that Phase 1 introduces.

- **Proof:** Laurel's gate output is unchanged: the same 25 PASS lines in the
  same order from `build.py`, and the probe suite still catches what it caught
  (its cases break one thing each, so a moved gate that stopped looking shows
  as a probe that no longer fails).
- **First measure the `geo` contract.** What the gates read from `geo` is the
  contract; list it before moving anything, and do not widen it for Willow's
  sake.
- **Not a precondition for Willow's spec (A1),** only for its build (A2).

### Phase 4: Willow, Tier A only

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

### Phase 5: measure, then Concord

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

**Done:** the tooling and the audit
([#165](https://github.com/captproton/yardstake-ux/pull/165)): `run_gates.py`,
`new_model.py`, `KIT-AUDIT.md`, this plan.

0. **Done 2026-10-01: preflight, before any PR (Phase 0; a read, not a change).**
   Findings in [`WILLOW-PREFLIGHT.md`](WILLOW-PREFLIGHT.md): Willow passes, with a
   two-roof finding that shapes step 1. The check was: read A-2.0 and A-0.0 and
   confirm one storey, a rectangle, the roof form and pitch, and if not one
   storey on a rectangle, **stop and re-pick the model before step 1**, because
   steps 1 to 3 are shaped by it. The findings are
   written into the spec at step 4; the decision is taken now.
1. [#167](https://github.com/captproton/yardstake-ux/issues/167) **Roof interface** (Phase 1): a list of planes, and ceiling split from
   roof. Laurel byte-identical.
2. [#168](https://github.com/captproton/yardstake-ux/issues/168) **`adu_kit/ink.py`** (Phase 2). Four readers byte-identical.
3. [#169](https://github.com/captproton/yardstake-ux/issues/169) **The gates move into `adu_kit/`** (Phase 3). Laurel's gate output
   unchanged; probes still fail where they should.
4. [#171](https://github.com/captproton/yardstake-ux/issues/171) **Willow spec** (A1): records step 0's findings with citations,
   scaffolded by `new_model.py`.
5. [#172](https://github.com/captproton/yardstake-ux/issues/172) **Willow build**, with the gable class (A2).
6. [#173](https://github.com/captproton/yardstake-ux/issues/173) **Willow overlay** (A3).
7. [#170](https://github.com/captproton/yardstake-ux/issues/170) **Willow export** (A4): Willow is on the page.
8. [#174](https://github.com/captproton/yardstake-ux/issues/174) **Timing and lessons** appended here (Phase 5); then Concord's plan.

Step 0 comes first. Steps 1 and 2 are independent and may run in parallel. Step 3 waits for step 1
(the roof interface decides which gates move). Step 4 can start while 1 to 3
are in review, but step 5, the build, waits for steps 1 and 3.

## Risks

- **Willow is not the shape we think.** Mitigated by Phase 0's decision rule.
- **A roof interface designed around one shape.** With only Laurel's shed as
  the existing user, the interface could fit one form. The gable class in step
  5 is the check; expect to revise the interface then, and do not freeze it
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
