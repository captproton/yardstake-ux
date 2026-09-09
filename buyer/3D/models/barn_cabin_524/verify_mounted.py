"""
verify_mounted.py — the exterior sconce is where the spec says, on the outside.

WHY THIS IS NOT verify_fixtures. That file checks recorded numbers against each
other and against code minimums, which is the right test for a fixture whose
position came off a drawing. This one's position came off a single video frame,
so the numbers cannot be checked against a sheet — there is no electrical sheet
to check them against. What CAN be checked is that the geometry ended up where
the numbers say, on the correct side of the wall, and clear of everything it
must be clear of. That is a different question and it needs its own file.

WHY IT ASKS ABOUT POSITION AND NOT NAMES. Same reason as verify_geometry: a
check that a Light_ object exists would pass if the sconce were built inside the
living room. The two failures worth catching here are both silent —

  MIRRORED. build_adu's frame convention was wrong once already, and P3 only
  caught it by overlaying the front elevation and noticing the 4'-0" window on
  the wrong side of the door. A sconce built on the INSIDE face of the south
  wall looks perfectly fine in every render that does not include that wall.

  BURIED. The arm peaks within 0.15 ft of the porch ceiling by measurement. A
  small error in `rise` or `projection` puts it through the soffit, where it is
  invisible from outside and visible from the porch.

    blender --background barn_cabin_524.blend --python verify_mounted.py
"""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec  # noqa: E402

FAILED = []


def gate(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")
    if not ok:
        FAILED.append(name)


def ftin(v):
    neg = "-" if v < 0 else ""
    v = abs(v)
    return f"{neg}{int(v)}'-{(v - int(v)) * 12:.1f}\""


def porch_soffit_z(plate):
    """Underside of the porch ceiling, read off the model rather than assumed.

    build_adu hangs Porch_ceiling below the plate; asking the object means this
    gate keeps working if that thickness ever changes, and fails loudly if the
    object is renamed rather than silently reverting to the plate.
    """
    ob = bpy.data.objects.get("Porch_ceiling")
    if ob is None:
        raise SystemExit("[mounted] no Porch_ceiling to measure clearance against")
    return min((ob.matrix_world @ v.co).z for v in ob.data.vertices)


def parts_of(item_id):
    """Every mesh belonging to one mounted item, by either naming scheme.

    Light_<id>_* for the fixture body, Light_lens_<id> for the emissive disc —
    the lens leads with its own token so materials.assignment can reach it by
    prefix, which is also why it cannot be found by a single startswith.
    """
    want = (f"Light_{item_id}_", f"Light_lens_{item_id}")
    return [o for o in bpy.data.objects
            if o.type == "MESH" and o.name.startswith(want)]


def world_pts(objs):
    return [o.matrix_world @ v.co for o in objs for v in o.data.vertices]


def main():
    spec = load_spec(HERE / "spec.yaml")
    mounted = spec["fixtures"].get("mounted")
    if not mounted:
        print("no fixtures.mounted in spec — nothing to verify")
        return

    env, con, lv = spec["envelope"], spec["construction"], spec["levels"]
    P = env["porch_depth"]["ft"]
    SY = P                                   # exterior face of the south wall
    t = con["exterior_wall_thickness"]["ft"]
    plate = lv["main_top_of_plate"]["ft"]
    op = spec["openings"]["main_floor"]["south_wall"]["openings"]

    print("=" * 76)
    print("MOUNTED FIXTURES — geometry, side and clearance")
    print("=" * 76)

    for item in mounted["items"]:
        fid = item["id"]
        form = mounted["forms"][item["form"]]
        along = item["along"]["ft"]
        aff = item["height_aff"]["ft"]
        proj = form["projection"]["ft"]
        shade_r = form["shade_dia"]["ft"] / 2.0
        tol = mounted["measurement"]["tolerance_in"] / 12.0

        print(f"\n{fid}  {item['surface']}/{item['side']}  "
              f"along {ftin(along)}  canopy {ftin(aff)} AFF")

        objs = parts_of(fid)
        gate(f"{fid}: geometry exists", bool(objs),
             f"{len(objs)} meshes: {', '.join(sorted(o.name for o in objs))}")
        if not objs:
            continue
        pts = world_pts(objs)
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]

        # --- on the OUTSIDE of the wall ------------------------------------
        # South wall spans SY..SY+t and the porch is to its south, so every
        # point of an exterior fixture must have y <= SY. This is the mirror
        # check, and it is the one worth having.
        gate(f"{fid}: entirely outside the wall face", max(ys) <= SY + 1e-6,
             f"max y {max(ys):.3f} vs wall face {SY:.3f}")
        # Projects no further than its own declared dimensions allow. The arm
        # is rooted on the canopy's outer face, so the reach is canopy depth
        # plus projection plus the shade's radius — the first version of this
        # bound dropped the canopy depth and failed a correct model, which is
        # the failure mode a gate can least afford.
        reach = form["canopy_depth"]["ft"] + proj + shade_r
        gate(f"{fid}: projects no further than its own dimensions",
             min(ys) >= SY - reach - 1e-6,
             f"reaches {(SY - min(ys)) * 12:.1f}\" off the wall, "
             f"allowed {reach * 12:.1f}\"")

        # --- lands on its declared anchor -----------------------------------
        # The canopy is the anchored part; the shade hangs outboard of it, so
        # the fixture's x-centre is checked, not its bbox.
        cx = (min(xs) + max(xs)) / 2.0
        gate(f"{fid}: centred on the declared offset", abs(cx - along) <= tol,
             f"model {ftin(cx)} vs spec {ftin(along)} "
             f"(tol {mounted['measurement']['tolerance_in']:.0f}\")")
        gate(f"{fid}: canopy height matches the declared AFF",
             min(zs) <= aff <= max(zs),
             f"spans {ftin(min(zs))}..{ftin(max(zs))}, canopy {ftin(aff)}")

        # --- clear of the porch ceiling -------------------------------------
        # Against the ceiling's UNDERSIDE as built, not against the plate. The
        # first version of this gate used the plate and was wrong by the 0.1 ft
        # soffit thickness — in the safe direction here, but a gate that is
        # right by luck is a gate that will be wrong somewhere else.
        soffit = porch_soffit_z(plate)
        gate(f"{fid}: clear of the porch ceiling", max(zs) <= soffit,
             f"top {ftin(max(zs))} vs soffit {ftin(soffit)} "
             f"— {(soffit - max(zs)) * 12:.2f}\" of clearance")

        # --- clear of every opening in the same wall ------------------------
        # A sconce over a window is not wrong the way a mirrored one is, but it
        # is wrong, and nothing else would catch it.
        fouled = []
        for o in op:
            ox0, ox1 = o["offset"], o["offset"] + o["w"]
            oz0, oz1 = o["sill"], o["sill"] + o["h"]
            if (min(xs) < ox1 and max(xs) > ox0
                    and min(zs) < oz1 and max(zs) > oz0):
                fouled.append(o["id"])
        gate(f"{fid}: clear of every opening in {item['surface']}", not fouled,
             f"fouls {fouled}" if fouled else
             f"nearest gap {min(abs(min(xs) - (o['offset'] + o['w'])) for o in op) * 12:.1f}\"")

        # --- the emissive part must be reachable by the material rules -------
        if item.get("lit_lens"):
            lens = [o for o in objs if o.name.startswith("Light_lens_")]
            gate(f"{fid}: lens named so assignment can reach it", len(lens) == 1,
                 lens[0].name if lens else "no Light_lens_* object")
            if lens:
                lz = [(lens[0].matrix_world @ v.co).z for v in lens[0].data.vertices]
                gate(f"{fid}: lens sits inside the shade mouth",
                     min(zs) <= min(lz) and max(lz) <= aff,
                     f"lens {ftin(min(lz))}..{ftin(max(lz))}")

    print("\n" + "=" * 76)
    if FAILED:
        print(f"{len(FAILED)} GATE(S) FAILED")
        for f in FAILED:
            print(f"  - {f}")
        raise SystemExit(1)
    print("all mounted-fixture gates passed")
    print("=" * 76)


main()
