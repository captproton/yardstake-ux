# Kit audit: what the second model taught about the third

Written 2026-09-29, after Laurel's twelve steps. It answers one question: to
make models faster, what is already general and what is not? Every figure below
was measured from the files on `main` that day; the method is at the end, so it
can be redone.

## Findings

**1. Laurel was rewritten, not copied, and that is the good news.**
Lines that appear verbatim in both models' scripts, of the barn cabin's
substantive lines:

| Barn cabin | Laurel | Shared |
|---|---|---|
| `build_adu.py` | `build.py` | 29 of 1,053 |
| `finish_adu.py` | `finish.py` | 23 of 330 |
| `views.py` | `views.py` | 25 of 338 |
| `render_elevations.py` | `render_elevations.py` | 22 of 53 |
| `make_textures.py` | `make_textures.py` | 6 of 120 |

A low number here is not waste being carried; it says Laurel's scripts share
almost no text with the barn cabin's. The kit extraction already took what
was byte-identical (kernel, export, finish, manifest, textures).

**2. The two builders are different kinds of program.**
The barn cabin's `build_adu.py` is 8 functions; one, `build()`, is 1,209 lines,
and `build_casework()` is another 598. It does read `spec.yaml` (about 80
lookups), but about 50 non-trivial numeric literals remain in the code, and
nothing gates them. Laurel's `build.py` is 56 functions, makes about 126 spec
lookups, keeps 7 such literals, and `test_build_literals.py` fails the build if
a dimension literal appears in it. The difference is enforcement and size, not
"spec against no spec". (An earlier draft of this audit said the barn cabin's
dimensions were in the code. That overstated it; measured 2026-09-29 by
counting float constants and spec subscripts with `ast`.)

**3. Laurel's `build.py` is already a general builder for one class of
building.** Its 1,762 lines of functions split:

| Part | Lines | Share |
|---|---|---|
| Gates (`report` and the `_every_*`, `_roof_*`... checks) | 889 | 51% |
| Builders (`build`, `_build_fixtures/canopy/condenser/furniture`) | 518 | 29% |
| Helpers (faces, bands, slots, stud faces) | 258 | 15% |
| Roof-specific (`Shed`, `_roof_*` gates) | 97 | 5% |

Only the roof plane knows it is a shed. Everything else is written against
"a rectangle, one storey, slab on grade, partitions, openings cut in walls,
trim, fixtures". That class, with a swappable roof, is the extraction target.

**4. Four "ink" readers repeat one technique and share its primitives.**
`plan_ink.py`, `fixture_ink.py`, `canopy_ink.py` and `condenser_ink.py` (about
960 lines) each read a sheet as vectors, register it, and write a
`spec.<x>.drawn` block a gate holds the model to. `plan_ink` owns the SVG
reading (`svg`, `paths`, `segments`, `matrix`, `frame`); `canopy_ink` and
`condenser_ink` each redefine `_runs`/`_bbox`/`_within`-style helpers.

**5. The intake question decides the schedule.** Laurel's PDF has a text
layer (86 KB), so the harvester gave it 67 dimensions on A-1.0 alone; the
barn cabin's is a scan and cost 2,927 spec lines read by eye. Willow, the
other Sacramento set, has a text layer too (208 candidates). `new_model.py`
now says which case a plan set is before any work starts.

## What follows, in order

1. **`run_gates.py` and `new_model.py`** (done; the sequel is
   [FACTORY-PLAN.md](FACTORY-PLAN.md)): one command for
   every gate, one command to start a model. They take nothing from any model.
2. **Move the ink primitives to `adu_kit/ink.py`.** SVG reading, segments,
   runs, registration. Prove the four readers' output byte-identical, as step 1
   of Laurel's plan did for the kernel. Smallest, safest, and every new model
   uses it.
3. **Move the gates.** They take `(spec, geo)` and about half know no
   roof. Move them behind a small `geo` contract; leave `_roof_*` with the roof.
4. **A `roof` class per roof form.** Laurel is `shed`. Willow's sheets mention
   `GABLE` 11 times, so its roof is the first thing model three must settle;
   this is a hint from `docs/INTAKE.md`, not a finding. Do this only when a
   model needs a second form, not before.
5. **Leave the barn cabin alone for now.** It has a loft, dormers and a
   crawlspace, so it is a different class. Retrofitting it would cost more than
   building the next model in Laurel's class. Cheaper: run the literal test
   against `build_adu.py` and move its ~50 literals into the spec.

## What this audit did not do

- It did not read the four ink readers line by line; point 4 is from their
  function lists. Diff them before extracting.
- The shared-line count is verbatim after whitespace folding. A renamed
  variable hides a shared line, so the true overlap is somewhat higher, though
  the design difference in point 2 stands regardless.
- It did not time anything. The claim that steps 8-12 were detail, not
  shipping, comes from the plan: Laurel was on the page at step 7.

## Method

Line overlap: lines over 25 characters, whitespace folded, comments dropped,
compared as sets between each barn/Laurel pair. Function split: `ast` over
`build.py`, classified by name prefix. Both are a few lines of Python; rerun
them before trusting these numbers after the files change.
