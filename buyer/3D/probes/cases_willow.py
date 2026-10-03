"""
cases_willow.py -- Willow's build gates each still say no when they should (#172).

These perturb Willow's BUILD, not its spec (a red test that moves the spec proves nothing,
because the build would move with it), and require the gate under test to say no BY ITSELF.

EVERY CASE EXPECTS "[FAIL] <label>" AND NOT THE LABEL. A gate's label is printed on its PASS
line too, so a case that only looked for the label could be satisfied by some OTHER gate failing
the build while the gate under test printed PASS: exactly what a gate that has silently stopped
checking does (found on #177; the same rule as cases_kitgates.py).

  * the rear wall built a foot short                       footprint
  * the walls built a foot low                             _walls_to_the_plate
  * the slab built half a foot too thick                   _walls_to_the_plate
  * the slab built a foot short on one side                _slab_is_the_footprint
  * the sheathing skins never built                        _sheathing_on_every_wall
  * a skin cut short along its wall                        _sheathing_on_every_wall
  * the width read from the depth's key in the build        footprint (the gates' own envelope)
  * the depth read from the width's key in the build        footprint
  * the wall thickness read from the sheathing's key        footprint
  * a sash shifted along its wall                          _sashes_and_leaves_in_their_openings
  * every sash built half a foot short                     _sashes_and_leaves_in_their_openings
  * a sash set off its wall's centre plane                 _sashes_and_leaves_in_their_openings
  * a leaf a half foot short along its wall                _sashes_and_leaves_in_their_openings
  * every leaf built twice as thick                        _sashes_and_leaves_in_their_openings
  * a leaf set off its wall's centre plane                 _sashes_and_leaves_in_their_openings
  * a partition built half a foot from the spec            every_partition_built
  * one window never cut                                   every_row_built
  * one door never given a leaf                            every_row_built
  * the sheathing skin never cut                           every_row_built
  * every window built as one plate, not a sash            sash_members
  * a vertex that is not a number                          no_degenerate
  * an opening recorded under a block no gate knows        openings_on_the_wall_their_block_names
  * the X 0 end's openings cut into the X 24 wall          _frame_not_mirrored (and the block gate)
  * window B's sash built to the rough opening             _window_b_unit_in_its_rough_opening
"""
from pathlib import Path

from suite import Case, Run, WILLOW, model_dir

G = "willow build"
BUILD = "build.py"


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, WILLOW) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(
            f"{what}: the line this case perturbs is not in {BUILD} exactly once "
            f"(found {text.count(old)}). The case is stale -- re-read build.py.")
    path.write_text(text.replace(old, new))


def _rear_wall_a_foot_short(work: Path) -> None:
    _patch(work,
           'walls["Wall_rear"] = box("Wall_rear", 0.0, W, 0.0, t, 0.0, head, shell)',
           'walls["Wall_rear"] = box("Wall_rear", 0.0, W - 1.0, 0.0, t, 0.0, head, shell)',
           "the rear wall a foot short")


def _walls_a_foot_low(work: Path) -> None:
    _patch(work,
           "    head = ceiling.under_y(0.0)\n",
           "    head = ceiling.under_y(0.0) - 1.0\n",
           "the walls a foot low")


def _slab_half_a_foot_too_thick(work: Path) -> None:
    _patch(work,
           'box("Slab", 0.0, W, 0.0, D, -slab_t, 0.0, site)',
           'box("Slab", 0.0, W, 0.0, D, -slab_t - 0.5, 0.0, site)',
           "the slab too thick")


def _slab_a_foot_short(work: Path) -> None:
    _patch(work,
           'box("Slab", 0.0, W, 0.0, D, -slab_t, 0.0, site)',
           'box("Slab", 0.0, W - 1.0, 0.0, D, -slab_t, 0.0, site)',
           "the slab a foot short")


def _no_sheathing_skins(work: Path) -> None:
    """Disable the branch that builds the four skins. skin_of stays empty, so every_row_built
    expects no skin cuts and used to pass."""
    _patch(work, "    if sheath:\n        faces = {", "    if False:\n        faces = {",
           "no sheathing skins")


def _a_skin_cut_short_along_its_wall(work: Path) -> None:
    """The rear skin stops at W instead of W + sheath: its last 3/8 inch of wall is bare."""
    _patch(work,
           '"Wall_rear":  box_geom(-sheath, W + sheath, -sheath, 0.0, 0.0, head),',
           '"Wall_rear":  box_geom(-sheath, W, -sheath, 0.0, 0.0, head),',
           "a skin cut short")


def _a_sash_shifted_along_its_wall(work: Path) -> None:
    """W-A1, an ordinary window (not B, which has its own gate), half a foot along its wall."""
    _patch(work,
           '            sashes.append(_glazed(f"Sash_{o[\'id\']}", along, plane, u0, u1, o["z0"], o["z1"],',
           '            u0, u1 = (u0 + 0.5, u1 + 0.5) if o["id"] == "W-A1" else (u0, u1)\n'
           '            sashes.append(_glazed(f"Sash_{o[\'id\']}", along, plane, u0, u1, o["z0"], o["z1"],',
           "a sash shifted along its wall")


def _every_sash_half_a_foot_short(work: Path) -> None:
    _patch(work,
           "        parts = sash_geom(along, plane, a0, a1, z0, z1, f2g, proud,",
           "        parts = sash_geom(along, plane, a0, a1, z0, z1 - 0.5, f2g, proud,",
           "every sash short")


def _a_sash_off_the_wall_plane(work: Path) -> None:
    _patch(work,
           "        plane = (lo + hi) / 2                 # spec.windows.glazing_plane: the wall's centre",
           '        plane = (lo + hi) / 2 + (0.1 if o["id"] == "W-C1" else 0.0)',
           "a sash off the wall plane")


def _a_leaf_short_along_its_wall(work: Path) -> None:
    _patch(work,
           '        spec_box = ((o["a0"], o["a1"], d0, d1, o["z0"], o["z1"]) if along == "x"',
           '        spec_box = ((o["a0"], o["a1"] - 0.5, d0, d1, o["z0"], o["z1"]) if along == "x"',
           "a leaf short along its wall")


def _every_leaf_twice_as_thick(work: Path) -> None:
    _patch(work,
           "        d0, d1 = plane - leaf_t / 2, plane + leaf_t / 2",
           "        d0, d1 = plane - leaf_t, plane + leaf_t",
           "every leaf twice as thick")


def _a_leaf_off_the_wall_plane(work: Path) -> None:
    _patch(work,
           "        d0, d1 = plane - leaf_t / 2, plane + leaf_t / 2",
           "        d0, d1 = plane - leaf_t / 2 + 0.2, plane + leaf_t / 2 + 0.2",
           "a leaf off the wall plane")


def _the_width_read_from_the_depth(work: Path) -> None:
    """A wrong key in the BUILD. The gates used to read W back from the build's own record, so they
    agreed with the mistake; they take the envelope from the spec now."""
    _patch(work, '    W = env["width"]["ft"]', '    W = env["depth"]["ft"]', "W read from the depth")


def _the_depth_read_from_the_width(work: Path) -> None:
    _patch(work, '    D = env["depth"]["ft"]', '    D = env["width"]["ft"]', "D read from the width")


def _the_wall_thickness_read_from_the_sheathing(work: Path) -> None:
    _patch(work,
           '    t = con["exterior_wall"]["stud_depth"]["ft"]',
           '    t = con["exterior_wall"]["sheathing"]["ft"]',
           "t read from the sheathing")


def _partitions_in_the_wrong_place(work: Path) -> None:
    """Every partition built half a foot from where the spec puts it. Dropping one would crash
    the build before any gate ran, and a partition in the wrong place is the other thing the gate
    exists to catch."""
    _patch(work,
           '            walls[row["id"]] = box(row["id"], a, b, lo, hi, 0.0, top, partitions)',
           '            walls[row["id"]] = box(row["id"], a, b, lo + 0.5, hi + 0.5, 0.0, top, partitions)',
           "the X-running partitions in the wrong place")
    _patch(work,
           '            walls[row["id"]] = box(row["id"], lo, hi, a, b, 0.0, top, partitions)',
           '            walls[row["id"]] = box(row["id"], lo + 0.5, hi + 0.5, a, b, 0.0, top, partitions)',
           "the Y-running partitions in the wrong place")


def _a_window_never_cut(work: Path) -> None:
    """W-C1 is the C window on the X 24 end wall."""
    _patch(work,
           "            cutter(f\"cut_{row['id']}\", wall, a0, a1, z0, z1, along)",
           "            if row[\"id\"] != \"W-C1\":\n"
           "                cutter(f\"cut_{row['id']}\", wall, a0, a1, z0, z1, along)",
           "a window never cut")


def _a_door_without_a_leaf(work: Path) -> None:
    _patch(work,
           '        sashes.append(multibox(f"Leaf_{o[\'id\']}", [spec_box], openings))',
           '        if o["id"] != "D-1":\n'
           '            sashes.append(multibox(f"Leaf_{o[\'id\']}", [spec_box], openings))',
           "a door without a leaf")


def _the_skin_never_cut(work: Path) -> None:
    """The windows are blind from outside: the sheathing skin keeps its wall's solid face."""
    _patch(work,
           "        if o[\"wall\"] in skin_of:\n            cutter(f\"cut_skin_{o['id']}\"",
           "        if False and o[\"wall\"] in skin_of:\n            cutter(f\"cut_skin_{o['id']}\"",
           "the skin never cut")


def _every_window_one_plate(work: Path) -> None:
    _patch(work,
           "        return multibox(name, parts, openings)",
           "        return multibox(name, parts[:1], openings)",
           "every window one plate")


def _a_vertex_that_is_not_a_number(work: Path) -> None:
    _patch(work,
           "    geo = dict(W=W, D=D, t=t, it=it, ceiling=ceiling, walls=walls,",
           '    walls["Wall_rear"].data.vertices[0].co.x = float("nan")\n'
           "    geo = dict(W=W, D=D, t=t, it=it, ceiling=ceiling, walls=walls,",
           "a NaN vertex")


def _a_block_the_gate_does_not_know(work: Path) -> None:
    _patch(work,
           "z0=z0, z1=z1, along=along, row=row, block=block))",
           'z0=z0, z1=z1, along=along, row=row, block=block + "_typo"))',
           "an exterior opening under an unknown block")


def _the_x0_end_cut_into_the_x24_wall(work: Path) -> None:
    """Route the X 0 block at Wall_x24: the six D windows are cut, sashed and recorded, in the
    wrong end of the building."""
    _patch(work,
           '("end_wall_x0", "Wall_x0", "y0", "y1", "y")',
           '("end_wall_x0", "Wall_x24", "y0", "y1", "y")',
           "the X 0 end routed to the X 24 wall")


def _window_b_built_to_the_rough_opening(work: Path) -> None:
    _patch(work,
           '            u0, u1 = row.get("unit_x0", o["a0"]), row.get("unit_x1", o["a1"])',
           '            u0, u1 = o["a0"], o["a1"]',
           "window B built to the rough opening")


SASHES_AND_LEAVES = "every sash and leaf sits in its opening: its span along the wall, its height and its wall plane"


def _fails(label: str) -> dict:
    return dict(contains=f"[FAIL] {label}")


def _case(name, setup, label):
    return Case(G, name, setup, [Run(BUILD, fails=True, blender=True, model=WILLOW)], **_fails(label))


CASES = [
    _case("the rear wall built a foot short (footprint)",
          _rear_wall_a_foot_short, "the shell is"),
    _case("the walls built a foot low (_walls_to_the_plate)",
          _walls_a_foot_low, "the walls and partitions run from the slab to the plate"),
    _case("the slab built half a foot too thick (_walls_to_the_plate)",
          _slab_half_a_foot_too_thick, "the walls and partitions run from the slab to the plate"),
    _case("the slab built a foot short on one side (_slab_is_the_footprint)",
          _slab_a_foot_short, "the slab is the building's footprint, X 0..W and Y 0..D"),
    _case("the sheathing skins are never built (_sheathing_on_every_wall)",
          _no_sheathing_skins, "every exterior wall carries its sheathing skin, outside its face of stud"),
    _case("one sheathing skin is cut short along its wall (_sheathing_on_every_wall)",
          _a_skin_cut_short_along_its_wall,
          "every exterior wall carries its sheathing skin, outside its face of stud"),
    _case("a sash shifted along its wall (_sashes_and_leaves_in_their_openings)",
          _a_sash_shifted_along_its_wall, SASHES_AND_LEAVES),
    _case("every sash built half a foot short (_sashes_and_leaves_in_their_openings)",
          _every_sash_half_a_foot_short, SASHES_AND_LEAVES),
    _case("a sash set off its wall's centre plane (_sashes_and_leaves_in_their_openings)",
          _a_sash_off_the_wall_plane, SASHES_AND_LEAVES),
    _case("a leaf a half foot short along its wall (_sashes_and_leaves_in_their_openings)",
          _a_leaf_short_along_its_wall, SASHES_AND_LEAVES),
    _case("every leaf built twice as thick (_sashes_and_leaves_in_their_openings)",
          _every_leaf_twice_as_thick, SASHES_AND_LEAVES),
    _case("a leaf set off its wall's centre plane (_sashes_and_leaves_in_their_openings)",
          _a_leaf_off_the_wall_plane, SASHES_AND_LEAVES),
    _case("the width read from the depth's key in the build (footprint)",
          _the_width_read_from_the_depth, "the shell is"),
    _case("the depth read from the width's key in the build (footprint)",
          _the_depth_read_from_the_width, "the shell is"),
    _case("the wall thickness read from the sheathing's key in the build (footprint)",
          _the_wall_thickness_read_from_the_sheathing, "the shell is"),
    _case("the partitions built half a foot from where the spec puts them (every_partition_built)",
          _partitions_in_the_wrong_place, "every partition in the spec was built, where the spec puts it"),
    _case("a window in the schedule is never cut (every_row_built)",
          _a_window_never_cut, "every schedule row produced a cut opening with a sash or a leaf"),
    _case("a door is cut but never given a leaf (every_row_built)",
          _a_door_without_a_leaf, "every schedule row produced a cut opening with a sash or a leaf"),
    _case("the sheathing skin is never cut, so the windows are blind (every_row_built)",
          _the_skin_never_cut, "every schedule row produced a cut opening with a sash or a leaf"),
    _case("every window built as one plate, not a sash (sash_members)",
          _every_window_one_plate, "every sash carries the members its declared operation implies"),
    _case("a vertex that is not a number (no_degenerate)",
          _a_vertex_that_is_not_a_number, "no NaN or degenerate geometry"),
    _case("an exterior opening recorded under a block no gate knows "
          "(openings_on_the_wall_their_block_names)",
          _a_block_the_gate_does_not_know, "every exterior opening is on the wall its spec block names"),
    _case("the X 0 end's windows cut into the X 24 wall (_frame_not_mirrored)",
          _the_x0_end_cut_into_the_x24_wall,
          "not mirrored: every opening is on the wall A-2.0's elevations draw its mark on"),
    _case("window B's sash built to the rough opening, not its unit (_window_b_unit_in_its_rough_opening)",
          _window_b_built_to_the_rough_opening,
          "window B's sash is its 1'-6\" unit, centred in the 1'-7\" rough opening the wall is cut to"),
]
