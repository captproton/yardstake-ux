# Willow A2: preflight (step 0 of FACTORY-PLAN.md)

Read 2026-10-01 from `example plans/sacramento_adus/adu-plan-full-set-a2-willow.pdf`
(Sacramento County Permit Ready ADU, Model A2 "Willow", Laura Miller Design,
20 pages, MAR 2024). This is a **read**, not a spec: nothing here is cited into a
`spec.yaml` yet, and every number must be re-read on its sheet at step 4. Where a
figure comes from text extraction it says so; where it comes from looking at the
rendered sheet it says that too, and is weaker.

## Verdict

**Willow passes the preflight's rule: one storey on a rectangle. Proceed.**
But its roof is **not "Laurel's shed with a gable swapped in"**, and that changes
what the roof interface (Phase 1) has to be. See "What this means for the plan".

## Confirmed

| Question | Finding | Where |
|---|---|---|
| Storeys | One. A-1.0 is a single plan; no loft, stair or second floor. Attic access only. | A-1.0 (text + sheet) |
| Rectangle | Yes. Overall **24'-0" by 19'-2"**, the same envelope as Laurel. | A-1.0 overall dimension strings (text) |
| Area | **460 sf** (ADU) **plus a 122 sf covered porch**, a separate line. | A-0.0 project data; A-1.0 "122 S.F. COVERED PORCH" |
| Foundation | Slab on grade. | A-0.0 |
| Framing | 2x6 exterior walls; stucco or fibre-cement lap siding (a choice, as Laurel); **"stick framed and truss roof with composite shingles"**. | A-0.0 scope of work |
| Plan option | A-1.0 draws a "1 BEDROOM FLOOR PLAN OPTION" beside the studio, as Laurel's does. | A-1.0 |
| Wall plate | **T.P. 8'-0"** on every elevation. | A-2.0 (text) |
| Overall height | **Top of roof 12'-10 3/4"** (rear elevation). | A-2.0 rear elevation (text) |
| Framing members | Pre-manufactured trusses at 24" o.c.; rafters for the stick-framed part. | S sheets, pages 12-15 (text) |

## The roof, as read

Two roof forms, not one (read from the elevations, A-2.0; pitches are labels on
the sheet, to be re-read at step 4):

1. **Main roof: a gable at 5"/1'-0" (5:12).** Ridge along the 24' direction:
   the roof plan's ridge vent is **24'-3" long** (text). The front elevation is the
   eave side (a plain shingled band); the two side elevations show the gable ends.
   Pre-built trusses. **The ceiling form is not established:** see "The ceiling"
   below.
2. **Porch roof: a small gable at 3"/1'-0" (3:12)**, stick framed, over the covered
   porch at the front, held on 6x6 posts and a 6x10 beam with a king-post truss
   drawn on the front elevation. The roof plan marks a **5'-0" overhang** at one
   edge, which I take to be the porch side; confirm that it is the front.
3. **Overhangs** read as 1'-0" and 1'-6" on the other sides (text); which is which
   needs the roof plan read carefully.

## The ceiling: likely flat at the plate, not confirmed

**Evidence for a ceiling below the roof**, with an attic above it (all text):
- A-2.0's attic-access note measures head height "from the top of the ceiling
  framing members to the underside of the roof framing", so ceiling framing sits
  below the roof framing with a space between.
- A-1.0 draws a "MIN. 22X30 ATTIC ACCESS" hatch in the plan.
- A-2.0's roof ventilation is computed for an enclosed, vented attic over the
  whole 460 sf (460 / 150 = 3.06 sf), and the truss notes (S sheets) mention
  ceiling joists and blocking at ceiling levels.

**What it does not show:** a reflected ceiling plan, a building section, or a truss
profile. Pre-built trusses do not by themselves imply a flat ceiling (scissor
trusses give vaulted ones), and the elevations' plate data does not fix the interior
ceiling plane. So a ceiling at T.P. 8'-0" is **likely**, but a vaulted or partly
vaulted ceiling is not ruled out. **Settle it at step 4** from the truss
profile or a section, before any partition is built to it.

## What this means for the plan

- **The roof interface must be a set of planes, not one surface.** Laurel's `Shed`
  is "underside height as a function of Y" (one plane). Willow is two gables that
  meet: a function of position cannot describe it without knowing which roof
  covers a point. Phase 1 should design the interface around **a list of roof
  planes with their extents**, with Laurel as a list of one. This is the change to
  make now, before Phase 1, because the plan said "do not freeze it before the
  gable class" and this is the evidence for why.
- **Walls probably differ.** Laurel's walls run to the roof underside (vaulted
  ceilings follow the roof). Willow's exterior walls stop at **T.P. 8'-0"** (text),
  and the gable ends need infill above the plate. Whether its partitions stop at a
  **flat ceiling** or run higher is **not established** (see "The ceiling"). Keep
  the general point: gates that assume partitions reach the roof are not
  roof-agnostic, so Phase 1 and Phase 3 separate "ceiling" from "roof". Do not
  design for Willow's termination until step 4 confirms it.
- **The porch is new.** Laurel has a 5'-0" front overhang, not posts, a beam and a
  second roof. Posts and the beam are a new kind of part. The 122 sf is the
  porch, and it is **outside the 460 sf**.
- **What matches Laurel, as verified here:** the footprint (24'-0" by 19'-2"), the
  sheet system and ids, the stucco-or-lap-siding choice (A-0.0), and the
  1-bedroom option drawn on A-1.0. **Not verified, and open for step 4:** the door
  and window schedules and the openings they describe, the interior layout, and
  anything about trim and fixtures. The sheet-reading scripts and finish decisions
  should carry over where the sheets match, which is why Willow still tests the kit
  with a small number of variables (though two roof forms is a bigger variable than
  the plan assumed).

## Open, to settle at step 4

- **The ceiling form** (flat at the plate, or vaulted, or partly): from the truss
  profile or a section. Drives where partitions stop.
- **Heel height.** From T.P. 8'-0" to top of roof 12'-10 3/4" is 58.75". A 5:12
  gable over half of 19'-2" (9'-7") rises about 47.9". About 10.9" is unexplained,
  presumably the truss heel and roofing thickness. Read it off a section or the truss
  notes; do not assume.
- **Where the porch roof meets the main roof,** and the porch's width, depth and
  post spacing.
- **Which overhang is where** (1'-0", 1'-6", 5'-0") on the roof plan.
- **Front, and the frame.** Laurel's front is the 24' wall at +Y with X from the
  living-room end; confirm Willow's front elevation is the same wall and end.
- **The door and window schedules** (A-1.0) are not compared with Laurel's here;
  harvest and compare them at step 4.

## Corrections to earlier documents

- **"A second area of 122 sf"** (Laurel's `PLAN.md`, and `FACTORY-PLAN.md`, which
  repeated it) is wrong: 122 sf is Willow's **covered porch**, not a second plan
  option. The option split is the 1-bedroom plan on A-1.0. Both documents are
  corrected in the same PR as this one (Laurel's at "There is an option split").
- **`FACTORY-PLAN.md` listed Willow's roof words as "GABLE 11, HIP 3".** On the
  sheets I read, the roof is a gable main roof plus a gable porch roof, and I did not
  find a hip roof on any elevation or on the roof plan. Where the three HIP hits
  come from is unchecked.
