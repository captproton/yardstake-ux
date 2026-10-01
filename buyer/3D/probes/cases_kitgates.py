"""
cases_kitgates.py -- the gates in adu_kit/gates.py each still say no when they should (#169, #177).

These perturb Laurel's BUILD, not its spec (a red test that moves the spec proves
nothing, because the build would move with it), and require a gate in the kit to say no
BY ITSELF.

WHY EVERY CASE EXPECTS "[FAIL] <label>" AND NOT THE LABEL. A gate's label is printed on
its PASS line too. A case that only looked for the label could therefore be satisfied by
some OTHER gate failing the build while the gate under test printed PASS, which is
exactly what a gate that has silently stopped checking does. A mutation test showed it:
with six of these seven gates each replaced by an unconditional PASS, all 230 earlier
cases stayed green. Expecting the FAIL line is what makes each of these bite.

  * the rear wall built a foot short                       footprint
  * the partitions built half a foot from the spec         every_partition_built
  * one window never cut                                   every_row_built
  * every window built as one plate, not a sash            sash_members
  * the interior trim lifted above the ceiling             trim_inside_its_walls
  * a vertex that is not a number                          no_degenerate
  * an opening recorded under a block no gate knows        openings_on_the_wall_their_block_names

Each is the lesion the gate's own docstring says it was written to catch.
"""
from pathlib import Path

from suite import Case, LAUREL, Run, model_dir

G = "kitgates"
BUILD = "build.py"


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(
            f"{what}: the line this case perturbs is not in {BUILD} exactly once "
            f"(found {text.count(old)}). The case is stale -- re-read build.py.")
    path.write_text(text.replace(old, new))


def _rear_wall_a_foot_short(work: Path) -> None:
    _patch(work,
           'walls["Wall_rear"] = box("Wall_rear", 0.0, W, 0.0, t, 0.0, ceiling.under_y(0.0), shell)',
           'walls["Wall_rear"] = box("Wall_rear", 0.0, W - 1.0, 0.0, t, 0.0, ceiling.under_y(0.0), shell)',
           "the rear wall a foot short")


def _partitions_in_the_wrong_place(work: Path) -> None:
    """Every partition built half a foot from where the spec puts it.

    The gate's docstring records DROPPING one (P_bath_W) as its original lesion, but
    later features reference that wall by name, so dropping it now crashes the build
    before any gate runs. A partition built in the wrong place is the other thing the
    gate exists to catch, and it keeps every object in the scene."""
    _patch(work,
           '        v, f = prism_geom(profile, extrude[0], extrude[1], plane="yz")\n'
           '        walls[row["id"]] = weld(row["id"], [(v, f)], partitions)',
           '        v, f = prism_geom(profile, extrude[0] + 0.5, extrude[1] + 0.5, plane="yz")\n'
           '        walls[row["id"]] = weld(row["id"], [(v, f)], partitions)',
           "the partitions in the wrong place")


def _a_window_never_cut(work: Path) -> None:
    """W-C1 is the window every_row_built's docstring says it was written to catch."""
    _patch(work,
           "            cutter(f\"cut_{row['id']}\", wall, a0, a1, z0, z1, along)",
           "            if row[\"id\"] != \"W-C1\":\n"
           "                cutter(f\"cut_{row['id']}\", wall, a0, a1, z0, z1, along)",
           "a window never cut")


def _every_window_one_plate(work: Path) -> None:
    """The first build filled every opening with one rectangle: a sash that is a plate."""
    _patch(work,
           "        return multibox(name, parts, openings)",
           "        return multibox(name, parts[:1], openings)",
           "every window one plate")


def _trim_above_the_ceiling(work: Path) -> None:
    _patch(work,
           '    trim = [multibox(f"Trim_{host}", parts, trim_coll)\n'
           '            for host, parts in trim_parts.items() if parts]',
           '    trim = [multibox(f"Trim_{host}", parts, trim_coll)\n'
           '            for host, parts in trim_parts.items() if parts]\n'
           '    for _t in trim:\n'
           '        _t.location.z += 5.0',
           "trim above the ceiling")


def _a_vertex_that_is_not_a_number(work: Path) -> None:
    _patch(work,
           "    geo = dict(W=W, D=D, t=t, it=it, roof_planes=roof_planes, ceiling=ceiling,",
           '    walls["Wall_rear"].data.vertices[0].co.x = float("nan")\n'
           "    geo = dict(W=W, D=D, t=t, it=it, roof_planes=roof_planes, ceiling=ceiling,",
           "a NaN vertex")


def _a_block_the_gate_does_not_know(work: Path) -> None:
    """Record every exterior opening under "<block>_typo". The wall and the geometry are
    untouched, so the only thing wrong is a block name no gate can place."""
    _patch(work,
           "z0=z0, z1=z1, along=along, row=row, block=block))",
           'z0=z0, z1=z1, along=along, row=row, block=block + "_typo"))',
           "an exterior opening under an unknown block")


def _fails(label: str) -> dict:
    return dict(contains=f"[FAIL] {label}")


CASES = [
    Case(G, "laurel: the rear wall built a foot short (footprint)",
         _rear_wall_a_foot_short, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("the shell is")),
    Case(G, "laurel: the partitions built half a foot from where the spec puts them "
            "(every_partition_built)",
         _partitions_in_the_wrong_place, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("every partition in the spec was built, where the spec puts it")),
    Case(G, "laurel: a window in the schedule is never cut (every_row_built)",
         _a_window_never_cut, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("every schedule row produced a cut opening with a sash or a leaf")),
    Case(G, "laurel: every window built as one plate, not a sash (sash_members)",
         _every_window_one_plate, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("every sash carries the members its declared operation implies")),
    Case(G, "laurel: the interior trim lifted above the ceiling (trim_inside_its_walls)",
         _trim_above_the_ceiling, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("no trim runs outside the rooms or above the roof underside")),
    Case(G, "laurel: a vertex that is not a number (no_degenerate)",
         _a_vertex_that_is_not_a_number, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("no NaN or degenerate geometry")),
    Case(G, "laurel: an exterior opening recorded under a block no gate knows "
            "(openings_on_the_wall_their_block_names)",
         _a_block_the_gate_does_not_know, [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         **_fails("every exterior opening is on the wall its spec block names")),
]
