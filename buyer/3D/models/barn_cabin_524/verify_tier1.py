"""
verify_tier1.py — gates for the Tier 1 interior: ceilings and floor finishes.

Checks the things a render cannot be trusted to show:
  1. flat ceilings land at their tagged height
  2. vaulted ceilings follow the roof underside they claim to follow
  3. no roof geometry intrudes into an occupied interior volume
  4. floor finishes tile the interior without gaps or overlap
  5. everything new is confined to the Finish collection

    blender --background barn_cabin_524.blend --python verify_tier1.py
"""
import sys
import math
from pathlib import Path

import bpy
import bmesh
import mathutils

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec, ft  # noqa: E402


def bounds(name):
    ob = bpy.data.objects[name]
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return ([min(v[i] for v in vs) for i in range(3)],
            [max(v[i] for v in vs) for i in range(3)])


def volume(name):
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[name].data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def main():
    spec = load_spec(HERE / "spec.yaml")
    env, con, lv, rf = (spec["envelope"], spec["construction"],
                        spec["levels"], spec["roof"])
    W = env["main_body_width"]["ft"]
    D = env["main_body_depth"]["ft"]
    P = env["porch_depth"]["ft"]
    t = con["exterior_wall_thickness"]["ft"]
    ct = con["ceiling_thickness"]["ft"]
    ff = con["floor_finish_thickness"]["ft"]
    plate = lv["main_top_of_plate"]["ft"]
    loft_sf = lv["loft_top_of_subfloor"]["ft"]
    rt = con["roof_assembly_thickness"]["ft"]
    mp = rf["main_pitch"]["rise"] / rf["main_pitch"]["run"]
    dp = rf["dormer_pitch"]["rise"] / rf["dormer_pitch"]["run"]
    ridge_top = rf["elevation_calibration"]["ridge_top_of_roof"]["ft"]
    dorm_len = rf["dormers"]["width"]["ft"]
    mp_v = rt / math.cos(math.atan(mp))
    dp_v = rt / math.cos(math.atan(dp))
    ridge_x = W / 2.0
    NY, SY = P + D, P
    xw, xe, ye, ys = t, W - t, NY - t, SY + t
    loft_s = NY - dorm_len

    def main_under(x):
        return ridge_top - mp * abs(ridge_x - x) - mp_v

    def dorm_under(x):
        return ridge_top - dp * abs(ridge_x - x) - dp_v

    results = []

    def gate(label, ok, detail=""):
        results.append((label, ok, detail))

    print("\n" + "=" * 78)
    print("TIER 1 VERIFICATION — ceilings and floor finishes")
    print("=" * 78)

    # ---- 1. flat ceiling height -------------------------------------------
    lo, hi = bounds("Ceil_flat_under_loft")
    err_in = (hi[2] - plate) * 12
    gate("flat ceiling top face at the 8'-0\" plate", abs(err_in) < 0.125,
         f"top at {ft(hi[2])}, target {ft(plate)}, err {err_in:+.3f}\"")

    # ---- 2. vaults follow their roof --------------------------------------
    for name, fn in (("Ceil_vault_living", main_under),
                     ("Ceil_vault_loft", dorm_under)):
        ob = bpy.data.objects[name]
        worst = 0.0
        for v in ob.data.vertices:
            wv = ob.matrix_world @ v.co
            expect = fn(wv.x)
            # every vertex sits on either the upper face or ct below it
            d = min(abs(wv.z - expect), abs(wv.z - (expect - ct)))
            worst = max(worst, d)
        gate(f"{name} follows its roof underside", worst < 0.01,
             f"max deviation {worst*12:.3f}\"")

    # ---- 3. roof must not intrude into occupied interior volume -----------
    # The loft is the exposed case: its ceiling follows the DORMER plane, which
    # sits above the MAIN plane, so a main-roof slab spanning the dormer zone
    # would cut through the loft.
    # Volume is the only reliable test here, and it is exact.
    #
    # Three earlier attempts failed, all instructive:
    #   - the roof FORMULA alone cannot know the roof has been cut
    #   - face centroids are not a containment proxy: the boolean leaves large
    #     concave faces whose centroid sits in the loft though the face does not
    #   - closest_point_on_mesh + normal is only valid for CONVEX solids, and a
    #     cut roof is deeply concave, so it reports false positives
    #
    # The roof profile is a band of constant vertical thickness, so both the
    # uncut volume and the removed wedge are exact closed forms.
    eave = rf["eave_overhang"]["ft"]
    rake = rf["rake_overhang"]["ft"]
    uncut = (W + 2 * eave) * mp_v * (NY + 2 * rake)
    removed = W * (NY - loft_s) * mp_v          # the dormer void, wall to wall
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects["Roof_main"].data)
    actual = abs(bm.calc_volume())
    bm.free()
    gate("main roof cut away from the loft, and only there",
         abs(actual - (uncut - removed)) < 0.05,
         f"{actual:.2f} ft3 = {uncut:.2f} uncut - {removed:.2f} removed "
         f"(err {actual - (uncut - removed):+.3f})")

    # ---- 4. floor finishes tile without gap or overlap --------------------
    # Measure the REAL top surface, not the bounding box. A bbox cannot see a
    # hole: cutting the 24"x24" crawl opening out of Floor_main_N leaves the
    # bbox identical, so the old form of this gate would have kept reporting a
    # perfect tiling over a floor with a square missing. Rule 12 -- a gate that
    # names a container must test the extent.
    names = ["Floor_main_S", "Floor_main_N", "Floor_bath"]
    area = 0.0
    for n in names:
        ob = bpy.data.objects[n]
        for poly in ob.data.polygons:
            if poly.normal.z > 0.9 and abs((ob.matrix_world @ poly.center).z - ff) < 1e-4:
                area += poly.area
    hole = next((i for i in spec["fixtures"]["access"]["items"]
                 if i["id"] == "crawl_hole" and i.get("floor_opening")), None)
    cut = (hole["w"] * hole["d"]) if hole else 0.0
    expect = (xe - xw) * (ye - ys) - cut
    gate("main-level floor finishes tile the interior, less the crawl opening",
         abs(area - expect) < 0.05,
         f"{area:.2f} sf vs {expect:.2f} sf expected "
         f"({(xe - xw) * (ye - ys):.2f} less {cut:.2f} crawl hole)")

    # And the hatch must fill that opening exactly, or the floor has a gap.
    #
    # SIZE WAS NOT ENOUGH, AND THE NAME SAID OTHERWISE. This checked width and
    # depth only, so a correctly-sized hatch sitting anywhere else in the room
    # passed under the words "fills its opening" -- rule 29's well-formed
    # versus well-placed, in a gate written long before that rule existed.
    # Found by auditing every gate in this repo for name-versus-predicate
    # mismatch after #93's review found four of them.
    if hole:
        hlo, hhi = bounds("Floor_crawl_hatch")
        hx0, hy0 = xw + hole["x"], ye - (hole["y"] + hole["d"])
        wrong = []
        if abs((hhi[0] - hlo[0]) - hole["w"]) > 0.01:
            wrong.append(f"width {hhi[0] - hlo[0]:.3f} vs {hole['w']:.3f}")
        if abs((hhi[1] - hlo[1]) - hole["d"]) > 0.01:
            wrong.append(f"depth {hhi[1] - hlo[1]:.3f} vs {hole['d']:.3f}")
        if abs(hlo[0] - hx0) > 0.01 or abs(hlo[1] - hy0) > 0.01:
            wrong.append(f"corner at {hlo[0]:.3f},{hlo[1]:.3f} "
                         f"but the opening is at {hx0:.3f},{hy0:.3f}")
        gate("crawl hatch fills its opening", not wrong,
             "; ".join(wrong) or
             f"{hhi[0] - hlo[0]:.3f} x {hhi[1] - hlo[1]:.3f} ft at "
             f"{hlo[0]:.3f},{hlo[1]:.3f}, matching the opening")

    # pairwise overlap
    ov = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            la, ha = bounds(a)
            lb, hb = bounds(b)
            ox = min(ha[0], hb[0]) - max(la[0], lb[0])
            oy = min(ha[1], hb[1]) - max(la[1], lb[1])
            if ox > 1e-6 and oy > 1e-6:
                ov.append(f"{a}/{b} {ox*oy:.2f} sf")
    gate("no floor finishes overlap", not ov, "; ".join(ov) or "clear")

    # ---- 5. thicknesses ----------------------------------------------------
    lo, hi = bounds("Floor_loft")
    gate("loft floor finish sits on the loft subfloor",
         abs(lo[2] - loft_sf) < 1e-4 and abs(hi[2] - loft_sf - ff) < 1e-4,
         f"{ft(lo[2])} .. {ft(hi[2])}")

    # ---- 6. door leaves ----------------------------------------------------
    lay = spec["interior_partitions"]["layout"]
    ti = con["interior_wall_thickness"]["ft"]
    dh = spec["doors"]["default_state"]
    pd = {p["id"]: p for p in lay["partitions"]}
    bad = []
    for d in lay["doors"]:
        typ = ("bypass" if d["id"].endswith("CLOSET")
               else "double_pocket" if "DBL" in d["id"] else "pocket")
        leaves = [o for o in bpy.data.objects
                  if o.name.startswith(f"Door_{d['id']}_")]
        if not leaves:
            bad.append(f"{d['id']}: no leaf"); continue
        total = sum(max(o.dimensions.x, o.dimensions.y) for o in leaves)
        if abs(total - d["w"]) > 0.02:
            bad.append(f"{d['id']}: leaves total {total:.2f} vs {d['w']:.2f} ft")
        # An OPEN leaf must clear its opening -- but "clear" means something
        # different for the two mechanisms, and this test only ever described
        # one of them. Its own comment said POCKET, while it ran against any
        # door whose state was open.
        #
        # A POCKET leaf retracts into the wall and leaves the opening empty.
        # A BYPASS leaf CANNOT: it slides behind its partner and stays inside
        # the opening, because a bypass reveals half and never more. Applying
        # the pocket rule to a bypass is a predicate no correct bypass can
        # satisfy -- it failed the moment `default_state.bypass` was honoured
        # for the first time in #93.
        #
        # So the bypass gets the invariant that IS true of it: HALF the
        # opening clear, no more and no less. That is not a relaxation --
        # "leaves cover half" is stronger than "leaves are somewhere", and it
        # catches both a bypass that never moved and one slid clean out of its
        # own opening.
        if dh.get(typ) == "open":
            pdef = pd[d["in"]]
            c, hw = d["centre_ft"], d["w"] / 2.0
            spans = []
            for o in leaves:
                lo, hi = bounds(o.name)
                if pdef["axis"] == "x":
                    a = (lo[0] - t), (hi[0] - t)
                else:
                    a = ((NY - t) - hi[1]), ((NY - t) - lo[1])
                spans.append(a)
                if typ != "bypass" and min(a[1], c + hw) - max(a[0], c - hw) > 0.02:
                    bad.append(f"{d['id']}: open leaf still blocks its opening")
            if typ == "bypass":
                # A REAL INTERVAL UNION, not the hull. The first version took
                # the span from the lowest clamped start to the highest clamped
                # end, which is the same number whether the leaves overlap or
                # sit apart with a GAP between them -- so two leaves covering
                # two disjoint strips whose outer edges happen to be half the
                # opening apart would have passed while leaving a hole in the
                # middle of the covered half. Merge, then sum.
                clipped = sorted((max(a[0], c - hw), min(a[1], c + hw))
                                 for a in spans)
                merged = []
                for lo_e, hi_e in clipped:
                    if hi_e <= lo_e:
                        continue                   # entirely outside the opening
                    if merged and lo_e <= merged[-1][1] + 1e-9:
                        merged[-1][1] = max(merged[-1][1], hi_e)
                    else:
                        merged.append([lo_e, hi_e])
                union = sum(hi_e - lo_e for lo_e, hi_e in merged)
                # ONE CONTIGUOUS RUN, not merely the right total. Switching the
                # hull for a real union fixed the case where two SMALL leaves
                # sum to less than a half, and left the case where two leaves
                # of exactly hw/2 sit at opposite ends of the opening: the
                # union is hw, the middle is bare, and the pair is stacked on
                # no half at all. Length was never the invariant -- a covered
                # HALF is -- and a half is contiguous by definition.
                if len(merged) != 1:
                    bad.append(f"{d['id']}: open bypass covers {len(merged)} "
                               f"separate strips {[[round(v, 2) for v in m] for m in merged]}, "
                               "not one contiguous half")
                else:
                    # AND IT MUST BE ONE OF THE TWO HALVES, not any contiguous
                    # run of the right length. Two leaves overlapping on an
                    # interior interval -- say (c-hw+1, c+1) -- are contiguous
                    # and exactly hw long, and neither end of the opening is
                    # covered or revealed. Length and contiguity are both
                    # properties a half HAS; being a half is the property that
                    # matters, and it is cheap to state directly.
                    #
                    # Fourth attempt at this predicate: hull, total length,
                    # contiguity, and now identity. Each earlier one was the
                    # nearest stronger measurement rather than the thing meant.
                    lo_m, hi_m = merged[0]
                    halves = ((c - hw, c), (c, c + hw))
                    if not any(abs(lo_m - a) < 0.02 and abs(hi_m - b) < 0.02
                               for a, b in halves):
                        bad.append(
                            f"{d['id']}: open bypass covers "
                            f"{lo_m:.2f}..{hi_m:.2f}, which is neither the "
                            f"low half {halves[0][0]:.2f}..{halves[0][1]:.2f} "
                            f"nor the high half "
                            f"{halves[1][0]:.2f}..{halves[1][1]:.2f}")
                    # A leaf hanging outside its own opening is not on a track.
                    outside = [f"{a:.2f}..{b:.2f}" for a, b in spans
                               if a < c - hw - 0.02 or b > c + hw + 0.02]
                    if outside:
                        bad.append(f"{d['id']}: leaf reaches outside the "
                                   f"opening: {', '.join(outside)}")
    # THE NAME CLAIMED THE OPPOSITE OF WHAT IT VERIFIES. "open leaves are
    # clear" is false for a bypass on EVERY passing run -- one half is
    # intentionally covered, which is the whole invariant. The name survived
    # the predicate being rewritten under it, which is how a green run comes
    # to assert something nobody checked.
    gate("door leaves match their callouts and open ones clear what they should",
         not bad, "; ".join(bad) or f"{len(lay['doors'])} doors, "
         f"{len([o for o in bpy.data.objects if o.name.startswith('Door_')])} "
         f"leaves; pockets retract, a bypass covers half")

    # ---- 7. reveals tagged for the trim material ---------------------------
    # A door with sill 0 has no sill reveal, so it contributes 3 faces, not 4.
    op = spec["openings"]["main_floor"]
    want = {}
    for wall, key in (("Wall_N", "north_wall"), ("Wall_S", "south_wall"),
                      ("Wall_W", "west_wall"), ("Wall_E", "east_wall")):
        want[wall] = sum(3 if o["sill"] <= 1e-6 else 4
                         for o in op[key]["openings"])
    nloft = len(spec["openings"]["loft"]["windows"]) * 4
    want["Dormer_face_W"] = want["Dormer_face_E"] = nloft
    wrong = []
    for n, k in want.items():
        got = sum(1 for p in bpy.data.objects[n].data.polygons
                  if p.material_index == 1)
        if got != k:
            wrong.append(f"{n} {got} vs {k}")
    gate("window/door reveals tagged for trim, not siding", not wrong,
         "; ".join(wrong) or f"{sum(want.values())} reveal faces across 6 walls")

    # ---- 8. ladder and guardrail -------------------------------------------
    la = spec["loft_access"]["ladder"]
    lo, hi = bounds("Ladder_loft")
    sec = la["stringer_section"]
    th_, dep_ = sec["thickness"]["ft"], sec["depth"]["ft"]
    want_ang = la["heel_cut_deg"]["value"]

    def verts(name):
        o = bpy.data.objects[name]
        return [o.matrix_world @ v.co for v in o.data.vertices]

    rail_v = verts("Ladder_loft")
    rx = sorted({round(v.x, 3) for v in rail_v})

    # THE BANDS MUST BE PROVEN, NOT ASSUMED. Taking them as "th_ in from each
    # extreme" cannot notice a rail going missing: with one rail, rx[0] and
    # rx[-1] are that rail's own two faces, both bands land on it, and the
    # gate below checks the same board twice and passes. So cluster the x
    # planes instead -- a ladder is two boards, th_ thick, lw apart -- and let
    # the clustering itself be the evidence there are two of them.
    lw_ = la["width"]["ft"]
    groups_x = []
    for x in rx:
        if groups_x and x - groups_x[-1][-1] <= th_ + 1e-3:
            groups_x[-1].append(x)
        else:
            groups_x.append([x])
    bad_b = []
    if len(groups_x) != 2:
        bad_b.append(f"{len(groups_x)} rail(s) found, want 2")
    elif any(abs((max(g) - min(g)) - th_) > 0.002 for g in groups_x):
        bad_b.append("a rail is not "
                     + ft(th_) + " thick: "
                     + ", ".join(ft(max(g) - min(g)) for g in groups_x))
    elif abs((rx[-1] - rx[0]) - lw_) > 0.002:
        bad_b.append(f"rails {ft(rx[-1] - rx[0])} apart outside to outside, "
                     f"want {ft(lw_)}")
    gate("the ladder has two rails, the stated thickness and width apart",
         not bad_b, "; ".join(bad_b) or
         f"2 rails, {ft(th_)} thick, {ft(rx[-1] - rx[0])} overall")
    bands = {"W": (groups_x[0][0] - 1e-3, groups_x[0][-1] + 1e-3),
             "E": (groups_x[-1][0] - 1e-3, groups_x[-1][-1] + 1e-3)} \
        if len(groups_x) == 2 else \
        {"W": (rx[0] - 1e-3, rx[0] + th_ + 1e-3),
         "E": (rx[-1] - th_ - 1e-3, rx[-1] + 1e-3)}

    # BOTH RAILS, EVERY VERTEX. The old gate read the minimum-x outer face only
    # and compared two chosen points on it, so it would have passed with the
    # other rail still a staircase, or with the checked rail bending between
    # those two points. #95 asked for "every vertex of a rail lies on the plane
    # through its own rake"; two points on one rail is a SAMPLE of that, which
    # is rule 33's proxy again.
    #
    # A rail is a straight board, so the property is: every vertex of it lies
    # within half the board's depth of that rail's own centre line, and that
    # line is at the heel-cut angle. The angle is taken per rail from its own
    # extremes, so the two are measured independently and a rail built at the
    # wrong rake fails on the angle rather than being absorbed by the tolerance.
    # NO PRIVILEGED VERTICES. Every version of this gate so far has failed by
    # choosing points: the bbox diagonal (which a 3 1/2" board inflates), then
    # two verts on one rail, then the topmost vertex -- which lands on the 1"
    # radius, curves away from the rail line, and reads 19.98 for a ladder cut
    # at exactly 20. Each fix was a better proxy, which is rule 33's trap.
    #
    # A rail is "a straight board of depth D raked at angle A". Both numbers
    # fall out of one measurement with no point-picking at all: project every
    # vertex perpendicular to a trial angle and take the spread. For a straight
    # board that spread is minimised AT the rake and the minimum IS the depth.
    # A stepped rail has no angle at which it measures 3 1/2" across.
    def spread_at(vs_, deg):
        a_ = math.radians(deg)
        off = [v.y * math.cos(a_) - v.z * math.sin(a_) for v in vs_]
        return max(off) - min(off)

    def fit_rake(vs_):
        lo_, hi_ = 0.0, 45.0
        for _ in range(80):                      # ternary search on the spread
            m1, m2 = lo_ + (hi_ - lo_) / 3, hi_ - (hi_ - lo_) / 3
            if spread_at(vs_, m1) < spread_at(vs_, m2):
                hi_ = m2
            else:
                lo_ = m1
        deg = (lo_ + hi_) / 2
        return deg, spread_at(vs_, deg)

    bad_rail = []
    shown = []
    for side, (x0, x1) in bands.items():
        vs_ = [v for v in rail_v if x0 <= v.x <= x1]
        if not vs_:
            bad_rail.append(f"{side} rail has no geometry")
            continue
        ang_, spread = fit_rake(vs_)
        shown.append(f"{side} {ang_:.2f} deg x {ft(spread)}")
        if abs(ang_ - want_ang) > 0.15:
            bad_rail.append(f"{side} rail rakes at {ang_:.2f} deg, want {want_ang}")
        if abs(spread - dep_) > 0.002:
            bad_rail.append(f"{side} rail measures {ft(spread)} across its own "
                            f"rake, not {ft(dep_)} -- it is not one straight board")
        # AND THE ENVELOPE IS NOT STRAIGHTNESS. The spread is the widest the
        # board gets anywhere; a section that bows or steps INWARD keeps the
        # same extremes and the same fitted angle and passes. A straight board
        # has no vertex between its two long faces at all -- every one is on
        # one face or the other -- except where the 1" radius turns the top.
        a2_ = math.radians(ang_)
        uy_, uz_ = math.sin(a2_), math.cos(a2_)
        off_ = [(w.y * math.cos(a2_) - w.z * math.sin(a2_)) for w in vs_]
        mid_ = (min(off_) + max(off_)) / 2
        run_ = [w.y * uy_ + w.z * uz_ for w in vs_]
        top_ = max(run_) - la["top_radius"]["ft"] - 0.002
        astray = [(t_, o_ - mid_) for t_, o_ in zip(run_, off_)
                  if abs(abs(o_ - mid_) - dep_ / 2) > 0.002 and t_ < top_]
        if astray:
            worst = max(astray, key=lambda p: dep_ / 2 - abs(p[1]))
            bad_rail.append(f"{side} rail has {len(astray)} vertices between "
                            f"its faces (worst {ft(dep_ / 2 - abs(worst[1]))} "
                            f"in) -- it bows or steps somewhere along the run")

    gate("both rails are straight boards on the 20 degree rake", not bad_rail,
         "; ".join(bad_rail) or
         " | ".join(shown))

    # THE RAILS DO NOT STOP AT THE LOFT FLOOR, and this gate said they must.
    # It encoded the old build, where they did -- and the builder's own
    # step-by-step says otherwise: "hang the ladder rails up over the loft by
    # about three feet so we have HANDLES". A gate that pins the top to the
    # floor forbids the handhold, which is the part you grab stepping off.
    over = la["overrun_above_loft"]["ft"]
    want_top = loft_sf + over * math.cos(math.radians(want_ang))
    gate("the rails carry past the loft floor to make a handhold",
         abs(hi[2] - want_top) < 0.08,
         f"top at {ft(hi[2])}, {ft(hi[2] - loft_sf)} above the loft floor "
         f"(want {ft(over)} along the rail = {ft(want_top - loft_sf)} up)")

    # THE RUNGS ARE LAID OUT ON THE RAIL, NOT UP THE WALL, and they are seated
    # by their TOP FACE. This gate used to measure the vertical gap between
    # rung CENTRES against the 12" the source gives for a distance along the
    # rail -- so it certified a 12.77" layout as 12", and it compared the top
    # rung's centre to the loft floor when the face you stand on is 11/16"
    # higher. Both are now measured the way the builder measures them.
    rung_v = verts("Ladder_rungs")
    # THICKNESS, not a single square section. The rungs are 1" x 3 1/2" boards
    # -- 3 1/2" of tread, 1" thick -- so the dimension that decides where the
    # top face lands and what the dado receives is the THICKNESS.
    rt_ = la["rung_section"]["thickness"]["ft"]
    rw_ = la["rung_section"]["depth"]["ft"]
    rs_ = la["rung_spacing"]["ft"]
    zs_ = sorted({round(v.z, 4) for v in rung_v})
    groups = []
    for z in zs_:
        if groups and z - groups[-1][-1] < rt_ * 1.5:
            groups[-1].append(z)
        else:
            groups.append([z])
    cent, tops = [], []
    for g in groups:
        zc = (min(g) + max(g)) / 2
        ys_ = [v.y for v in rung_v if abs(v.z - zc) < rt_]
        cent.append(((min(ys_) + max(ys_)) / 2, zc))
        tops.append(max(g))
    want_n = la["rung_count"]["value"]
    bad_r = []
    if len(cent) != want_n:
        bad_r.append(f"{len(cent)} rungs, want {want_n}")
    # THE FINISHED FLOOR, not the subfloor. loft_sf is the top of the
    # subfloor and Floor_loft lays `ff` of finish on it; comparing to loft_sf
    # approves a tread sitting 3/4" BELOW the surface you step onto, and
    # rejects one correctly flush with it.
    loft_walk = loft_sf + ff
    if tops and abs(tops[-1] - loft_walk) > 0.005:
        bad_r.append(f"top tread FACE at {ft(tops[-1])}, not level with the "
                     f"loft floor at {ft(loft_walk)} "
                     f"(subfloor {ft(loft_sf)} + {ft(ff)} finish)")
    # GUARD THE DETAIL STRING, not just the predicate. `gate(...)` takes its
    # detail as an already-evaluated argument, so with nought or one rung
    # `min(along)` raises ValueError and the verifier dies instead of
    # REPORTING the wrong rung count it was about to catch.
    #
    # AND MEASURE ALONG THE RAKE, NOT THE CHORD BETWEEN CENTRES. The two agree
    # only while the rungs are ON the rail: a straight-line distance between
    # centres is preserved if every rung slides the same amount in Y, which
    # takes the whole set off the rail while the spacing, the top face and
    # every dado shoulder still read correctly. So the gap is projected onto
    # the rake, and each centre's PERPENDICULAR offset from the rail's own
    # centre line is constrained separately. Two numbers, because it is two
    # claims: evenly spaced, and on the ladder.
    a_ = math.radians(want_ang)
    u_y, u_z = math.sin(a_), math.cos(a_)             # along the rake
    p_y, p_z = math.cos(a_), -math.sin(a_)            # across it
    along = [abs((cent[i + 1][0] - cent[i][0]) * u_y
                 + (cent[i + 1][1] - cent[i][1]) * u_z)
             for i in range(len(cent) - 1)]
    if along and any(abs(d - rs_) > 0.01 for d in along):
        bad_r.append(f"rung spacing along the rail runs "
                     f"{ft(min(along))}..{ft(max(along))}, want {ft(rs_)}")
    # the rail centre line, taken from the rails themselves
    rail_off = [w.y * p_y + w.z * p_z for w in rail_v]
    mid_off = (min(rail_off) + max(rail_off)) / 2
    stray = [abs((c[0] * p_y + c[1] * p_z) - mid_off) for c in cent]
    if stray and max(stray) > 0.01:
        bad_r.append(f"a rung centre sits {ft(max(stray))} off the rail's "
                     f"centre line — the rungs are not on the ladder")
    treads = [max(v.y for v in rung_v if abs(v.z - zc) < rt_)
              - min(v.y for v in rung_v if abs(v.z - zc) < rt_)
              for _, zc in cent]
    if treads and any(abs(d - rw_) > 0.004 for d in treads):
        bad_r.append(f"tread depth runs {ft(min(treads))}..{ft(max(treads))}, "
                     f"want {ft(rw_)}")
    gate("nine rungs at 12 inches ALONG THE RAIL, top face on the loft floor",
         not bad_r, "; ".join(bad_r) or
         (f"{len(cent)} rungs, {ft(min(along))} apart on the rail "
          f"({ft(min(along) * math.cos(math.radians(want_ang)))} of height), "
          f"{ft(rw_)} treads {ft(rt_)} thick, top face flush") if along else
         f"{len(cent)} rung(s) — too few to have a spacing")

    # EVERY RUNG SITS IN A SLOT. The rungs used to be pushed into solid rail by
    # the dado depth and left interpenetrating it. Nothing looked wrong, and
    # nothing would have until something cut a section. The recess is real when
    # the rail's inner lamination STOPS at each rung: those stops are faces, so
    # they leave vertices at the rung's top and bottom inside the dado's own
    # thin band of x. Checked on both rails, for every rung.
    dado_ = la["dado_depth"]["ft"]
    # MEASURE THE SLOT, AND CHECK THE RUNG IS IN IT. This used to look for a
    # vertex at each expected z SOMEWHERE inside a band of x a whole dado
    # wide, and never asked where in that band, nor whether the rung reached
    # it. A shallower dado whose shoulder still fell inside the band passed,
    # and so did a rung translated in x until it missed the slot entirely.
    #
    # The shoulder is a plane, so find the plane: the innermost x the rail
    # occupies, and the x the slot is cut back to. Their separation is the
    # dado's real depth. Then require each rung's own x extent to reach into
    # both slots, which is what "seated" means.
    slots = {"W": (rx[0] + th_ - dado_ - 1e-3, rx[0] + th_ + 1e-3),
             "E": (rx[-1] - th_ - 1e-3, rx[-1] - th_ + dado_ + 1e-3)}
    missing = []
    for side, (x0, x1) in slots.items():
        planes = sorted({round(v.x, 4) for v in rail_v if x0 <= v.x <= x1})
        if len(planes) < 2:
            missing.append(f"{side} rail has no slot cut in it at all")
            continue
        got_depth = max(planes) - min(planes)
        if abs(got_depth - dado_) > 0.002:
            missing.append(f"{side} dado is {ft(got_depth)} deep, want {ft(dado_)}")
        shoulder = min(planes) if side == "W" else max(planes)
        zs_side = {round(v.z, 3) for v in rail_v
                   if abs(v.x - shoulder) < 1e-3}
        for _, zc in cent:
            for edge in (zc - rt_ / 2, zc + rt_ / 2):
                if not any(abs(z - edge) < 0.004 for z in zs_side):
                    missing.append(f"{side} rail has no dado shoulder at {ft(edge)}")
    # AND EACH RUNG SEPARATELY. Taking the extent across ALL the rungs lets
    # one shortened or shifted rung miss its slot while another supplies the
    # global minimum and maximum -- the aggregate is seated even though that
    # rung is not. Every rung is asked about its own two ends.
    #
    # `if rung_v` because an EMPTY rung mesh reaches here with `missing` still
    # empty -- no shoulder loop runs when there are no rungs -- and min() over
    # nothing raises before the wrong-count gate above can report it.
    if not rung_v:
        missing.append("Ladder_rungs is empty — there is nothing to seat")
    elif not missing:
        for _, zc in cent:
            own = [w for w in rung_v if abs(w.z - zc) < rt_]
            if not own:
                continue
            a0, a1 = min(w.x for w in own), max(w.x for w in own)
            if a0 > slots["W"][0] + 0.002 or a1 < slots["E"][1] - 0.002:
                missing.append(f"the rung at {ft(zc)} spans {ft(a0)}..{ft(a1)} "
                               f"and does not reach into both slots")
    gate("every rung is dadoed into both rails, not buried in them",
         not missing,
         "; ".join(missing[:3]) or
         f"{len(cent) * 4} shoulders, {ft(dado_)} deep, all present")

    # THE ROD REACHES BOTH RAILS, tested by where it is rather than by its
    # existing. It is one tube spanning the full width, so nothing would have
    # noticed it shortening to touch only one rail.
    # THE OUTER EXTENT OF THE HARDWARE IS NOT THE ROD. This compared the
    # min/max x of the whole welded Hdw_ladder_rod -- rod, elbows AND flanges
    # -- against the rails. The flanges sit outside the rails by design, so
    # they set both extremes and the gate would keep passing with the straight
    # rod shortened off one rail entirely. It only caught the lesion in the
    # RED test because this build happens to move the elbow with the rod end;
    # that is a coupling in the builder, not a property of the gate.
    #
    # The property is that a tube of the rod's diameter CROSSES each rail. So
    # look inside each rail's own band of x -- where nothing but the straight
    # rod can reach -- and check what is there is a rod-sized cross-section,
    # at the same height on both sides.
    hw = verts("Hdw_ladder_rod")
    rr_rod = la["slide_rod"]["diameter"]["ft"] / 2

    # SLICE THE SOLID. Two drafts of this gate failed on the same instinct --
    # find the rod by looking at vertices -- and a tube has vertices only at
    # the ends of its segments.
    #   Draft 1 asked what vertices lie inside the rail's band of x. None do,
    #   because the rod's rings are outside it.
    #   Draft 2 recovered the rod from rings sharing one axis, and counted the
    #   ELBOW'S FIRST RING as rod: the elbow leaves tangent to the rod, so its
    #   opening ring is exactly on the rod's axis. Shorten the rod and leave
    #   the elbow where it was and that draft still reported a rod spanning
    #   both rails, with a gap in the middle where no metal is.
    # The question is not where the vertices are. It is whether there is
    # METAL in the plane of each rail, so cut the mesh there and measure what
    # the cut returns: a rod-sized ring, or nothing.
    def section_at(x):
        bm = bmesh.new()
        bm.from_mesh(bpy.data.objects["Hdw_ladder_rod"].data)
        bm.transform(bpy.data.objects["Hdw_ladder_rod"].matrix_world)
        res = bmesh.ops.bisect_plane(
            bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=(x, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0))
        pts = [g.co.copy() for g in res["geom_cut"]
               if isinstance(g, bmesh.types.BMVert)]
        bm.free()
        return pts

    bad_rod = []
    seen = []
    for side, (x0, x1) in bands.items():
        pts = section_at((x0 + x1) / 2)
        if not pts:
            bad_rod.append(f"no metal in the plane of the {side} rail — "
                           f"the rod does not cross it")
            continue
        dy = max(p_.y for p_ in pts) - min(p_.y for p_ in pts)
        dz = max(p_.z for p_ in pts) - min(p_.z for p_ in pts)
        seen.append((side, dy, dz,
                     (min(p_.z for p_ in pts) + max(p_.z for p_ in pts)) / 2))
        if abs(dy - 2 * rr_rod) > 0.004 or abs(dz - 2 * rr_rod) > 0.004:
            bad_rod.append(f"what crosses the {side} rail sections "
                           f"{ft(dy)} x {ft(dz)}, not the {ft(2 * rr_rod)} rod")
    if len(seen) == 2 and abs(seen[0][3] - seen[1][3]) > 0.004:
        bad_rod.append("the rod sits at a different height in each rail")
    gate("the slide rod passes through both rails", not bad_rod,
         "; ".join(bad_rod) or
         f"a {ft(2 * rr_rod)} section of rod in the plane of both rails, "
         f"at {ft(seen[0][3])}")


    # AND THE FLANGES LAND ON THE TRIM BOARD. The trim is the loft floor's own
    # south fascia, and its position is read OFF THAT OBJECT rather than
    # recomputed here -- so if the floor moves, this gate moves with it and the
    # hardware is what has to keep up. That is the point of placing the flange
    # off the floor and the elbow off the rod: two independently positioned
    # things that have to meet.
    # THE TRIM BOARD IS A REAL OBJECT NOW. This used to read the loft floor's
    # own edge, because there was no board -- the flanges were screwed to
    # paint. The gate reads the LEDGER's face, so it is testing the thing the
    # source actually describes, and it fails if the board is ever removed
    # rather than silently falling back to the floor behind it.
    fl = la["slide_rod"]["flange"]
    fl_pre = fl
    led = bpy.data.objects.get("Ledger_loft")
    # AND IT IS THE HEIGHT OF THE FLANGE. The spec ties the board's height to
    # the flange diameter rather than giving it a number of its own, because
    # that is the relationship the frame shows; this checks the built board
    # kept it, so a board that drifts back to a full-height fascia fails.
    # AGAINST THE FLANGE, NOT AGAINST THE SPEC'S COPY OF IT. The spec says
    # the board's height is `derived: slide_rod.flange.diameter`, and that
    # text is prose -- nothing enforced it. Comparing the built board with
    # `ledger.height` lets the flange change while the board does not, and
    # the gate goes on passing over a broken relationship. So the flange is
    # the authority, and the spec's own number is checked against it too,
    # which is what makes `derived:` mean something.
    led_h_want = fl_pre["diameter"]["ft"]
    if abs(la["ledger"]["height"]["ft"] - led_h_want) > 1e-6:
        bad_b = (f"spec ledger.height {ft(la['ledger']['height']['ft'])} no "
                 f"longer equals the flange it says it is derived from, "
                 f"{ft(led_h_want)}")
    else:
        bad_b = None
    led_h_got = (bounds("Ledger_loft")[1][2] - bounds("Ledger_loft")[0][2]
                 ) if led else None
    # AND IT HANGS FROM THE LOFT FLOOR SURFACE. Checked against the floor
    # rather than against the rod, so a board that drifts down the edge with
    # its own hardware fails instead of travelling along with it. (It used to
    # be checked against the plate, when the board sat on the top of the
    # wall -- which is where the footage puts it and where the ladder's own
    # placement will not allow it; see spec.ledger.)
    # MEASURED AGAINST THE FLOOR, NOT AGAINST THE SPEC'S ARITHMETIC. Reading
    # `loft_sf + ff` here recomputes the same sum the builder used, so the two
    # cannot disagree -- and `trim_y` is then read off the ledger itself, so
    # the board and all its hardware could move away from the loft floor
    # together and every gate downstream would follow them and pass. Compared
    # against Floor_loft's own top and south face, the board's position is a
    # relationship between two objects, and drifting breaks it.
    fl_b = bounds("Floor_loft")
    led_b0 = bounds("Ledger_loft") if led else None
    led_on_wall = led is not None and (
        abs(led_b0[1][2] - fl_b[1][2]) < 0.004          # top flush with the floor
        and abs(led_b0[1][1] - fl_b[0][1]) < 0.004)     # back against its edge
    ok_led = (led is not None and bad_b is None
              and abs(led_h_got - led_h_want) < 0.004 and led_on_wall)
    gate("the trim board is the height of the flange and hangs from the floor",
         ok_led,
         (f"Ledger_loft {ft(led_h_got)} tall, matching the "
          f"{ft(fl_pre['diameter']['ft'])} flange, hung from Floor_loft at "
          f"{ft(fl_b[1][2])} and applied to its edge at {ft(fl_b[0][1])}")
         if led and ok_led else
         (bad_b or
          (f"Ledger_loft is {ft(led_h_got)} tall, want the flange's "
           f"{ft(led_h_want)}"
           if abs(led_h_got - led_h_want) >= 0.004 else
           f"Ledger_loft tops out at {ft(led_b0[1][2])} / backs onto "
           f"{ft(led_b0[1][1])}, not hung from Floor_loft at "
           f"{ft(fl_b[1][2])} / {ft(fl_b[0][1])}")
          if led else "Ledger_loft MISSING — the flanges have nothing to "
          "screw to"))

    # NO EARLY RETURN. The first draft of this bailed out here when the board
    # was absent, and the RED test caught what that costs: deleting the ledger
    # did not produce a failing gate, it produced a script that printed its
    # header and stopped -- no gates, no RESULT line, exit 0. A suite that
    # says NOTHING reads like a suite that passed, which is worse than the
    # defect it was hiding. The two gates below depend on the board, so they
    # fail when it is gone; nothing else does, so nothing else is skipped.
    trim_y = min(v.y for v in verts("Ledger_loft")) if led else None
    on_trim = [v for v in hw if abs(v.y - trim_y) < 0.004] if led else []
    fx = sorted({round(v.x, 3) for v in on_trim})
    clusters = []
    for x in fx:
        if clusters and x - clusters[-1][-1] < fl["diameter"]["ft"]:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    widths = [max(c) - min(c) for c in clusters]
    ok_fl = (led is not None and len(clusters) == fl["count"]
             and all(abs(w - fl["diameter"]["ft"]) < 0.02 for w in widths))
    gate("both flanges sit flat on the trim board", ok_fl,
         (f"{len(clusters)} flange(s) on the board at {ft(trim_y)}, "
          f"{', '.join(ft(w) for w in widths) or 'none'} across "
          f"(want {fl['count']} x {ft(fl['diameter']['ft'])})") if led else
         "there is no trim board for them to sit on")

    # AND THE ELBOW HAS TO REACH THEM. This gate exists because the previous
    # one did not catch a lesion it looked like it should: put the rod back to
    # its old 8.854 height and the flanges still sit perfectly on the fascia,
    # because they are placed off the FLOOR and never moved. What moved was the
    # elbow, which drove 2 3/4" THROUGH the fascia into the floor build-up.
    #
    # The comment above this hardware in build_adu says the flange and the rod
    # are positioned independently "and have to meet". That was true of the
    # geometry and asserted by nobody -- prose standing in for a check, which
    # is exactly what ground rule 34 is about. So: the pipe's furthest reach
    # must land ON the flange's inner face, neither short of it nor through it.
    # AND IT MUST BE ON THE BOARD. Sharing the board's Y plane says nothing
    # about where in the board's face the flange landed: it could hang off the
    # bottom edge or sit beyond the end of the run and still pass. Read the
    # board's own X and Z extent and require the whole flange ring inside it.
    led_b = bounds("Ledger_loft") if led else None
    off_board = []
    for c in clusters:
        ring = [v for v in on_trim if min(c) - 0.01 <= v.x <= max(c) + 0.01]
        if not ring:
            continue
        z0, z1 = min(v.z for v in ring), max(v.z for v in ring)
        if not (led_b[0][2] - 0.002 <= z0 and z1 <= led_b[1][2] + 0.002):
            off_board.append(f"a flange spans {ft(z0)}..{ft(z1)}, outside the "
                             f"board's {ft(led_b[0][2])}..{ft(led_b[1][2])}")
        if not (led_b[0][0] <= min(c) and max(c) <= led_b[1][0]):
            off_board.append(f"a flange runs past the end of the board in x")
    gate("each flange lands within the board's face, not off an edge",
         led is not None and bool(clusters) and not off_board,
         "; ".join(off_board) or
         (f"both rings inside {ft(led_b[0][2])}..{ft(led_b[1][2])} vertically"
          if led and clusters else "no flange to place"))

    rr_ = la["slide_rod"]["diameter"]["ft"] / 2
    fl_t_ = fl["thickness"]["ft"]
    want_face = (trim_y - fl_t_) if led else None
    bad_e = [] if led else ["there is no trim board to land on"]
    for c in clusters:
        xc = (min(c) + max(c)) / 2
        zc = sum(v.z for v in on_trim if abs(v.x - xc) < fl["diameter"]["ft"]) \
            / max(1, len([v for v in on_trim if abs(v.x - xc) < fl["diameter"]["ft"]]))
        pipe = [v for v in hw
                if math.dist((v.x, v.z), (xc, zc)) < fl["diameter"]["ft"] * 0.3]
        if not pipe:
            bad_e.append(f"no pipe arrives at the flange at {ft(xc)}")
            continue
        reach = max(v.y for v in pipe)
        if abs(reach - want_face) > 0.005:
            d = reach - want_face
            bad_e.append(f"elbow at {ft(xc)} "
                         + (f"drives {ft(d)} THROUGH the trim board"
                            if d > 0 else f"stops {ft(-d)} short of the flange"))
    gate("the elbow lands on the flange, neither short nor through it",
         led is not None and not bad_e, "; ".join(bad_e) or
         f"both elbows reach {ft(want_face)}, the flange's inner face")

    # NOTHING CAUGHT THE LADDER BEING INSIDE THE BUILDING, and that is the
    # defect a person found by looking. Every ladder gate measured the ladder
    # against ITSELF -- its own rake, its own rungs, its own rails -- so a
    # perfectly built ladder buried to its shoulders in the loft floor passed
    # all of them. Rule 31: a gate that only knows about its own subject
    # cannot see the subject in the wrong place.
    #
    # The ladder leans on the loft floor's edge, so touching it is correct and
    # passing THROUGH it is not. Measured as overlap of the real solids: for
    # every rail vertex north of the floor's south face, how far past it does
    # the rail go, and at what height.
    floor_face = bounds("Loft_floor")[0][1]
    floor_lo, floor_hi = bounds("Loft_floor")[0][2], bounds("Floor_loft")[1][2]
    # EDGES, NOT VERTICES. A rail's long edges run from the main floor to the
    # overrun in one span, so the rail can cross the floor's slab between two
    # vertices with neither of them inside it -- and a vertex test sees
    # nothing. The rail is a solid; ask its edges.
    #
    # Each edge is a straight segment, so clip it to the slab's z band and the
    # deepest incursion is at one of the two clipped ends. That is exact, and
    # it costs one pass over the edge list.
    lad = bpy.data.objects["Ladder_loft"]
    M = lad.matrix_world
    deep, worst_z = 0.0, None
    for e in lad.data.edges:
        p0 = M @ lad.data.vertices[e.vertices[0]].co
        p1 = M @ lad.data.vertices[e.vertices[1]].co
        z0, z1 = p0.z, p1.z
        lo_, hi_ = max(min(z0, z1), floor_lo), min(max(z0, z1), floor_hi)
        if lo_ > hi_:
            continue                                  # never in the slab's band
        for zc_ in (lo_, hi_):
            f_ = 0.0 if abs(z1 - z0) < 1e-9 else (zc_ - z0) / (z1 - z0)
            y_ = p0.y + f_ * (p1.y - p0.y)
            if y_ - floor_face > deep:
                deep, worst_z = y_ - floor_face, zc_
    gate("the ladder clears the loft floor edge it leans on", deep <= 0.004,
         f"a rail edge reaches {ft(deep)} inside the floor slab at {ft(worst_z)}"
         if deep > 0.004 else
         f"every rail edge stops at the edge face {ft(floor_face)} "
         f"or south of it")

    gh = spec["loft_access"]["guardrail"]["height"]["ft"]
    lo, hi = bounds("Rail_loft")
    gate("guardrail reaches its stated height", abs((hi[2] - loft_sf) - gh) < 0.02,
         f"{ft(hi[2] - loft_sf)} above the loft floor (stated {ft(gh)}, ASSUMED)")

    # ---- 9. mesh budget ----------------------------------------------------
    nm = len([o for o in bpy.data.objects if o.type == "MESH"])
    gate("lod0 mesh count within budget", nm <= 120, f"{nm} meshes, cap 120")

    # ---- 10. new geometry confined to Finish -------------------------------
    fin = {o.name for o in bpy.data.collections["Finish"].objects}
    stray = [o.name for o in bpy.data.objects
             if o.type == "MESH" and o.name.startswith(("Ceil_", "Floor_main",
                                                        "Floor_bath", "Floor_loft",
                                                        "Door_", "Trim_", "Ladder_",
                                                        "Ledger_", "Rail_", "Hdw_"))
             and o.name not in fin]
    gate("all Tier 1 geometry is in the Finish collection", not stray,
         ", ".join(stray) or f"{len(fin)} objects")

    w = max(len(r[0]) for r in results)
    print()
    for label, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label.ljust(w)}  {detail}")
    print("=" * 78)
    ok_all = all(r[1] for r in results)
    print("RESULT:", "ALL PASS" if ok_all else "FAILURES PRESENT")
    if not ok_all:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
