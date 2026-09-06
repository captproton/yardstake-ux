# Tier 1 — Schematic interior

**Status: DONE**, merged in
[#57](https://github.com/captproton/yardstake-ux/pull/57). 14/14 gates.
Two things surfaced that are worth carrying forward: the main roof ran through
the loft across 100% of its width (a defect inherited from P2, fixed by cutting
the roof out of the dormer zone), and the reveal tagging did not survive export
until `materials.clear()` was found to reset every polygon's material index.

**Goal.** Turn the interior from a shell into rooms. Door leaves, casing and
trim, ceiling planes, distinct floor surfaces, and the loft ladder and
guardrail. Geometry only — no textures, no fixtures.

**Owner:** us, as are Tiers 2 and 3. The placement developer's scope is
placement only — see
[The one handoff](README.md#the-one-handoff--to-the-placement-developer).
Nothing here is blocked on another party.

**Why it comes first.** It unblocks most of Tier 2 (interior materials need
surfaces) and all of Tier 3 (fixtures need floors and walls). It is also what
makes the dollhouse view — the one buyers will use most — stop reading as four
grey boxes.

**Two prerequisites, both cheap, both before geometry:**

1. **Fix texel density.** [TIER-2 §2](TIER-2-materials-and-textures.md) —
   128 px/ft, world-axis cube projection, unwrapped after booleans. It
   constrains how everything below is authored. Decide once, use throughout.
2. **Read the build rules** in [README](README.md#tier-1-build-rules). They
   exist to keep Tiers 2 and 3 cheap.

---

## 1. Where things stand

Present: four measured partitions with two pocket-door openings, exterior walls
with all seven openings cut, a loft floor slab, a porch ceiling, and a floor
slab.

Absent: every door leaf, all trim and casing, every ceiling except the porch,
any distinction between floor and wall surfaces, the loft ladder, the loft
guardrail, and the closet.

## 2. Scope

### 2a. Ceilings

The most valuable item, and the one with the best source data — the plan tags
ceiling conditions room by room.

| Room | Condition | Source |
|---|---|---|
| Bath | flat, 8'-0" | A1.1 tag `8'-0" CEILING` |
| Bedroom | flat, 8'-0" | A1.1 tag `8'-0" CEILING` |
| Living / Kitchen | **vaulted** | A1.1 tag `VAULTED CEILING` |
| Loft storage | **vaulted** | A1.1 loft plan tag `VAULTED CEILING` |
| Porch | flat, 8'-0" | already modelled |

The flat ceilings are trivial planes. **The vaulted ones are the real work of
this tier** — they follow the underside of the roof, which `build_adu.py`
already computes as `main_under(x)` and the dormer equivalent. Derive them from
those functions rather than re-deriving the roof, or they will drift apart.

Watch for: the living/kitchen vault runs up to the ridge and must not poke
through the roof assembly; the loft vault is bounded by the dormer plane on both
sides and the main plane above.

### 2b. Floor surfaces

Tier 1 delivers **planes with a flat material slot each**; Tier 2 replaces the
colour with texture. Three distinct surfaces, because they take different
materials later:

- Main floor — oak (transcript 0:31)
- Bath floor — slate (transcript 1:17)
- Loft floor — carpet over pad (transcript 6:46)

Separate objects, separate material slots, named on the existing prefix
convention so Tier 2 can address them.

### 2c. Door leaves

Sizes are plan callouts and exact. Positions for the interior doors are ±6"
(see `spec.yaml → interior_partitions.layout.doors`).

| Door | Size | Type | Note |
|---|---|---|---|
| `D-FRONT` | 3'-0" × 6'-8" | half-lite entry | Elevation shows 6-lite glazing over a raised panel |
| `D-POCKET-DBL` | 5'-0" | double pocket | Living ↔ bedroom |
| `D-POCKET-BATH` | 2'-4" | pocket | Living ↔ bath |
| `D-CLOSET` | 6'-0" | bypass slider | Needs closet walls — see 2e |

**Decide the default state.** Pocket doors sit *inside* the wall when open, so a
leaf modelled in the open position is invisible. Recommend: build every leaf,
default the pockets to open (leaf hidden in the pocket) for clear sightlines in
the dollhouse view, and default the front door closed. Modelling the leaves
regardless is cheap and lets the configurator show them either way later.

### 2d. Trim and casing

- **Window and door casing** — width measurable off the A1.1 elevations at
  50 px/ft, same technique as everything else.
- **Baseboard** — not on the drawings. Standard 3½"–5¼"; assume and label as
  assumed.
- **Window reveals** — the jamb faces inside each opening. These want the `trim`
  material, not `siding`, which is the per-face material change flagged in
  [TIER-2 §3](TIER-2-materials-and-textures.md). **Tier 1 is the cheap moment to
  do it**, while the openings are being detailed anyway.

Trim is many small objects. Watch mesh count — see §4.

### 2e. Closet walls

Previously deferred out of scope. They belong here: the `6'-0"` bypass door has
nothing to hang on without them, and the plan's `3'-2"` dimension string locates
the stacked-W/D zone between bath and bedroom.

Positions are measurable off A1.1 by the wall-density scan already used for the
other partitions.

### 2f. Loft ladder and guardrail

The one item with real dimensional data already in hand.

**Ladder** — 5/4×4 clear vertical grain Douglas fir, 20° heel cut, bolted to a
flange (video 5:02–5:20). Rise is main floor (0) to loft subfloor (8'-10¼"), so
at 20° off vertical the stringer runs ≈ 9'-5". Plan position is measurable —
A1.1 tags `LADDER TO MAIN FLOOR` on both the main floor and loft plans.

**Guardrail** at the loft's open edge (video 5:34, "we have our guard rail
here"). Height not stated; assume 36" and label it. The edge itself is known —
it is the south boundary of the loft floor.

## 3. Approach

Extend `build_adu.py`, spec-driven, in the existing pattern. New `spec.yaml`
blocks, each entry with a `source:` and a confidence:

```yaml
ceilings:      # per-room: flat height, or vaulted -> follows roof underside
floors:        # per-zone finish planes with material slots
doors:         # leaf geometry, thickness, default open/closed state
trim:          # casing width, baseboard height, reveal treatment
loft_access:   # ladder geometry and position, guardrail line and height
```

No dimensions in code. When P4 changed the exterior wall from 6½" to 5½", every
opening volume re-derived itself and all ten checks passed with no code edits —
that property is worth preserving.

## 4. Verification

New gates, in the manner of `verify_openings.py`:

1. **Ceiling heights** — flat ceilings land at their tagged height within ⅛".
2. **Vault clearance** — no vaulted ceiling vertex sits above the roof
   underside. A single min-distance check catches the whole class of error.
3. **Ladder geometry** — angle is 20° ± 0.5°, and the top lands on the loft
   subfloor within ½".
4. **Guardrail height** — ≥ 36" above the loft floor along its whole run.
5. **Door leaves** — each leaf fits its opening with a plausible reveal and does
   not intersect a jamb.
6. **`lod1` and `lod2` are byte-identical** before and after. Nothing in this
   tier may reach them, and a file hash comparison proves it in one line — much
   stronger than eyeballing a size number.
7. **All existing gates still pass** from a clean rebuild: `build_adu.py`,
   `verify_openings.py` ALL PASS, `finish_adu.py` both gates.
8. **Mesh count budget** — trim generates many small objects. Cap `lod0` at
   ~120 meshes and merge by material if it exceeds that, or the draw calls will
   hurt on a phone before the triangles do.

## 5. Suggested order

Sequenced so Tier 2 and Tier 3 unblock as early as possible:

1. **Ceilings and floors** — unblocks Tier 2's interior materials, which is the
   longest-lead item downstream.
2. **Closet walls** — unblocks Tier 3's fixture placement in that zone.
3. **Door leaves** — cheap, high visual return in the dollhouse view.
4. **Trim, casing and reveals** — the per-face material work Tier 2 depends on.
5. **Ladder and guardrail** — self-contained, can slip without blocking anything.

## 6. Open items

- **Guardrail height is assumed** at 36". Not on the drawings and not stated in
  the video. Label it as assumed; it is a code-relevant dimension and someone
  may want it at 42".
- **Baseboard is assumed.** Not drawn.
- **Interior door positions remain ±6"**, unchanged from P4. Do not let leaf
  geometry imply more precision than the position it hangs in.
- **The vaulted loft ceiling interacts with the dormer plane** on both sides.
  That geometry was corrected once already in P3 — reuse the corrected
  functions, do not re-derive.
