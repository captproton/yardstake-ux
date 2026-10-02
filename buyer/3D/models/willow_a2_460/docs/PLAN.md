# willow_a2_460 -- build plan

Source: `adu-plan-full-set-a2-willow.pdf` (20 pages). See [`INTAKE.md`](INTAKE.md) for what the
plan set is and whether it has a text layer.

**Written from `new_model.py`'s template, then edited.** The template is
tiered on purpose. A model is *on the page* when Tier A is done; Tier B is
detail that makes it more faithful, and each item can wait or be dropped
without the page noticing. Laurel took 12 steps; it was on the page at step 7.

## Tier A -- ships (the model is on the page)

1. **Spec.** Cite every number; settle the roof form, the option and the frame
   in `spec.yaml` (`docs/candidates.yaml` is the raw material). Gate: `spec_lint`.
2. **Build.** Slab, walls, partitions, the main gable and the porch gable, **the
   porch posts and beam** (positions are in `spec.yaml` roof.porch.posts), every
   opening cut. Gate: a
   `build` gate per claim, and no dimension literal in the script.
3. **Overlay.** Hold the model to the elevations' ink, by named features.
4. **Export.** Materials (one finish), three levels of detail, manifest, index
   row, front declared. Delete `EXPORT_PENDING`. The page needs no code.

## Tier B -- upgrades (each optional, each its own PR)

5. Interior overlay against the floor plan's ink. 6. Trim. 7. Finish choices
(stucco/siding) and textures. 8. Fixtures and equipment. 9. Furniture.
10. Optional structures (canopy; porch detail beyond its posts, beam and king post, which are Tier A).

## Decisions this model inherits

Trim defaults are `assumed` from the barn cabin, exterior finish is a presence
group, furniture arrangements are reused, "assumed" carries a reason. See
`models/laurel_a1_460/docs/PLAN.md` for why. Override in the spec, not the code.

## Sequence

One line per pull request; mark each Done with its number.

