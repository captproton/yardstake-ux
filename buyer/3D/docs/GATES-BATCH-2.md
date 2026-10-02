# Gates, batch 2: the plan (#169)

Written 2026-10-02, after batch 1 merged
([#177](https://github.com/captproton/yardstake-ux/pull/177), `177e16c`).
**Status: a plan; nothing here is built.** It answers three questions: which of the
remaining gates should move into the kit, how, and *when*. The last answer is not the
one the factory plan first assumed.

## What batch 1 taught

Moving seven gates took five Copilot review rounds, and **every finding was a defect in
an original gate**, not in the move:

1. `sign()` raised `TypeError` on a YAML list or mapping (the same bug was in Laurel's
   original).
2. `frame_not_mirrored` hardcoded Laurel's window marks, so in a shared module a model
   with other marks would get a silent PASS. It went back to Laurel.
3. `openings_on_the_wall_their_block_names` skipped an opening whose `block` was present
   but unknown: a gate with nothing to look at reported PASS.
4. Six of the seven moved gates had **no probe that proved they could still say no**
   (mutation test: each replaced by an unconditional PASS left all 230 cases green).
5. The same gate accepted any same-way wall in the right half of the building, so an
   opening cut into an interior partition passed.

So batch 2 does not start from "copy the code". It starts from **reading each gate and
testing that it bites**, before and after it moves.

## The method: read, bite, move, bite again

For each gate:

1. **Read it**, and write down what it assumes: the `geo` keys, the spec keys, the scene
   and object names, and any Laurel-only content. Ask what it does when it has *nothing to
   look at*: it must fail or skip, never pass.
2. **Mutation-test it where it is.** Replace it with an unconditional PASS and run the
   whole probe suite. If anything goes BAD, a probe already requires this gate. If
   nothing does, the gate is unproven.
3. **If unproven, write the probe first**, in its own commit, against the original in
   `build.py`. The probe expects the gate's **failure message**, never its label (a label
   also prints on a PASS line; see "Why survivors survive" below).
4. **Move it by script** (copy by AST range, never retype), listing any deliberate
   change with the finding that motivated it.
5. **Mutation-test it again** in the kit and require its own probe to catch it.

## The evidence: where every remaining gate stands

Measured 2026-10-02 on `main` at `177e16c`, in clean git worktrees whose unmutated
baseline was 237 of 237 cases. Each gate was replaced in `build.py` by an unconditional
PASS and the full probe suite run once. **CAUGHT** means at least one probe went BAD.
(A first attempt at this measurement was invalid, because my script appended the stub
after `build.py`'s `main()` call and crashed every build; it was discarded, and the
script now defines the stub before the original.)

| Gate | Lines | Needs (beyond `spec`/`geo`) | Laurel-only content | Mutation | Decision |
|---|---|---|---|---|---|
| `_every_opening_cased` | 17 | `_cased`, `_stacks`, `room_faces` | none | CAUGHT (1) | move, **2b** |
| `_baseboard_runs` | 28 | `_pt`, `_stacks`, `room_faces` | none | CAUGHT (1) | move, **2b** |
| `_siding_trim` | 24 | `_cased`, `_stacks`, `outer_face`, `room_faces` | `Trim_ext_siding_` prefix | CAUGHT (1) | move, **2b** |
| `_siding_skins` | 46 | `_face_slot`, `_volume` | none | CAUGHT (4) | move, **2b** |
| `_floor_on_the_slab` | 17 | `_floor_slot`, `UP` | none | CAUGHT (1) | move, **2b** |
| `_fixtures_where_drawn` | 45 | `_fixture_targets`, `room_faces` | messages name "A-1.0" | CAUGHT (3) | move, **2c** |
| `_furniture_placed` | 65 | `_mesh_boxes`, `_overlap`, `_partition_band` | `Furn_` object names | CAUGHT (4) | move, **2c** |
| `_where_a10_draws_them` | 44 | none | messages name "A-1.0" | CAUGHT (2) | move, **2c** |
| `_water_heater_as_published` | 23 | none | Rheem PROPH40, `Fix_water_heater` | CAUGHT (1) | **stay** |
| `_canopy_hung` | 105 | `_mesh_boxes`, `_overlap`, `outer_face` | `Canopy_*`, door `D-1` | CAUGHT (6) | **stay** |
| `_ground_mounted` | 67 | none | `Equip_condenser`, `Equip_pad` | CAUGHT (5) | **stay** |
| `_door_one_has_its_sidelite` | 14 | none | door 1 | **SURVIVED** | **stay**; needs a probe |
| `_frame_not_mirrored` | 33 | none | window marks C/D/E | **SURVIVED** | **stay**; needs a probe |
| `_roof_top_at_the_front_edge` | 24 | none | one shed plane | CAUGHT (1) | stay with the roof |
| `_roof_covers_its_overhangs` | 17 | none | one shed plane | **SURVIVED** | stay with the roof; needs a probe |
| `_roof_meets_the_plates` | 36 | none | one shed plane | **SURVIVED** | stay with the roof; needs a probe |

**Why "stay" for the Laurel-only gates.** The lesson of the frame gate is that a gate
which knows a building should not move until a second model needs it. Whether Willow has
a canopy, a condenser or a named water heater is a question for its spec (#171), so those
four stay until then.

**Why survivors survive** (shown directly for `_roof_meets_the_plates`): the "roof floats
a foot above the plates" probe expects the gate's *label*. With the gate mutated to PASS,
the lifted roof still prints `[PASS] the built roof underside meets T.P. 1`, and another
gate (the roof's height at the front edge) fails the build, so the probe is satisfied
without the gate it is named for doing anything. The probes written later (trim, interior,
furniture, canopy, equipment, finish) match the **failure message**, which only prints
when the gate itself says no, and those all bite. The older ones do not.

The four survivors all stay in `build.py`, so none of them blocks a move, but each is a
gate that could silently stop checking. They get probes in **2.0**.

## The helpers

The 8 gates to move call 12 helpers. Six are used only by gates and move with them. Six
are **also used by the builder**, so they need a shared home that both import.

| Helper | Lines | Used by | Needs | Goes to |
|---|---|---|---|---|
| `_cased` | 22 | gates only | `_pt` | with its gates (2b) |
| `_pt` | 3 | gates only | none | with its gates (2b) |
| `_stacks` | 10 | gates only | none | with its gates (2b) |
| `_fixture_targets` | 16 | gates only | none | with its gate (2c) |
| `_mesh_boxes` | 11 | gates only (also `_canopy_hung`, which stays) | `VERTS_PER_BOX`; reads a Blender object's vertices, no `bpy` import | with its gates (2c); `build.py` imports it |
| `_overlap` | 5 | gates only (also `_canopy_hung`) | `MESH_TOL`; **pure Python**, so unit-testable | with its gates (2c); `build.py` imports it |
| `room_faces` | 29 | gates **and builder** | `_partition_band`, spec | `adu_kit/rectangle.py` |
| `outer_face` | 8 | gates **and builder** | spec | `adu_kit/rectangle.py` |
| `_partition_band` | 7 | gates **and builder** | `specread.sign` | `adu_kit/rectangle.py` |
| `_face_slot`, `_floor_slot` | 9, 2 | gates **and builder** | `manifest.face_slots` | `adu_kit/manifest.py` |
| `_volume` | 7 | gates **and builder** | `bmesh` | `adu_kit/kernel.py` |

**`room_faces`, `outer_face`, `_partition_band` and `_overlap` are plain Python:** spec
or box arithmetic, with no Blender. In a pure module they can have real unit tests with
Laurel's known numbers, which is a stronger proof than the probe suite alone.

## The plan

**2.0, cheap and independent: prove the four survivors.** Commit the mutation harness
(it currently lives outside the repo, in a scratch directory) as `probes/mutate_gate.py`,
and write one probe each for `_door_one_has_its_sidelite`, `_frame_not_mirrored`,
`_roof_covers_its_overhangs` and `_roof_meets_the_plates`, each expecting that gate's
failure message. For the roof gates the lesion must be one **only that gate** catches
(for example, halving the front overhang for `_roof_covers_its_overhangs`). Nothing
moves. This can happen any time.

**2a, the shared helpers.** Move `room_faces`, `outer_face`, `_partition_band` into
`adu_kit/rectangle.py` (pure Python), `_face_slot`/`_floor_slot` into `manifest.py`, and
`_volume` into `kernel.py`. Proof: **golden outputs**. Capture `room_faces(spec)` and
`outer_face(spec, wall)` for Laurel before the move and require them identical after,
plus a byte-identical export and the same 25 build lines. Add unit tests with those
numbers.

**2b, trim, floor and siding.** Move `_every_opening_cased`, `_baseboard_runs`,
`_siding_trim`, `_siding_skins`, `_floor_on_the_slab` with `_cased`, `_pt`, `_stacks`.
Follow the method above for each. The `Trim_ext_siding_` prefix is a convention that goes
in the module's contract, as batch 1's did.

**2c, fixtures, furniture and the plan overlay.** Move `_fixtures_where_drawn`,
`_furniture_placed`, `_where_a10_draws_them` with `_fixture_targets`, `_mesh_boxes`,
`_overlap`. Their messages name "A-1.0", Laurel's floor-plan sheet: decide, per message,
whether to take the sheet name from the spec or leave it, and record the choice.

**Done when (for #169).** Every gate that moved has a probe that goes BAD when the gate is
replaced by an unconditional PASS; Laurel's `build.py` prints the same 25 lines in the
same order; the exported files are byte-identical; `python3 run_gates.py` and the probe
suite pass; and the four "stay" gates, `_frame_not_mirrored`, and the roof gates are named
in `adu_kit/gates.py` as deliberately left behind, with the reason.

## When: this is not on Willow's critical path

Every gate in 2a to 2c is about trim, finish, fixtures, furniture or the plan overlay.
The factory plan puts all of those in **Tier B** for Willow. Willow's Tier A (spec,
build, elevation overlay, export) needs only the seven batch 1 gates, the roof, and the
sheet-reading helpers (#168).

**Recommendation: do 2.0 any time, but defer 2a to 2c until Willow's Tier B begins.**
Reasons:

- Nothing in Willow's Tier A waits on them, so doing them first delays Willow.
- Batch 1's lesson was that extracting without a second consumer produced wrong
  generalizations (the frame gate, the half-building test). Willow's Tier B is that second
  consumer, and it will show which assumptions hold *before* they are fixed in the kit.
- The cost of waiting is small: Willow's Tier B author reads the gates anyway.

The counter-argument is that doing it now keeps the factory plan's original order and
spares Willow's Tier B from importing from `build.py`. That is a preference, not a
blocker, so it is a decision for you, not a finding.

**Suggested order:** Willow spec (#171) and `ink.py` (#168) in parallel, then the Willow
build (#172), overlay (#173) and export (#170); 2.0 alongside; then 2a to 2c as Willow's
Tier B items need them.

## Risks and open questions

- **Messages that name Laurel's sheets** ("A-1.0 draws ..."): a shared gate that prints
  another model's sheet name is wrong output. Each needs a decision at the move.
- **`_furniture_placed`** reads `Furn_` object names and the room layout through the
  builder's arrangement scheme; its coupling to how Laurel reuses the barn cabin's
  furniture has not been read closely, and the method's first step is to read it.
- **New import edges.** The builder will import helpers that now live in the kit, so a
  mistake shows as a crash on import, not a wrong answer; the byte-identical export is
  the check.
- **The mutation harness is not yet in the repo.** Until 2.0 lands, the evidence above
  can be reproduced only from this document's description.
- **Survivors are about the probe, not the gate.** A surviving gate may be correct; it is
  unproven. The decision "stay" is about Laurel-specific content, not about quality.
