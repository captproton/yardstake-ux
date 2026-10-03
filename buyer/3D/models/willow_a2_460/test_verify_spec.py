"""
models/willow_a2_460/test_verify_spec.py -- verify_spec.py's gates catch what they
exist for (#171).

    python3 -m unittest discover -s models/willow_a2_460 -v      (from buyer/3D)

Plain Python; needs PyYAML. Each test breaks a COPY of Willow's spec in one way and
requires the gate written for that mistake to fail, with no traceback. The real spec
is shown passing every gate. A gate switched off in verify_spec.py fails its test
here, so a gate that passes the real spec because it checks nothing is found.

The spec is edited as data (load, change, dump), not as text, because the spec is a
generated block-style file with no stable one-line anchors.
"""
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
VERIFY = HERE / "verify_spec.py"
SPEC = HERE / "spec.yaml"


def run(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "spec.yaml"
        path.write_text(text)
        return subprocess.run([sys.executable, str(VERIFY), str(path)], capture_output=True, text=True, timeout=120)


def opening(spec, oid):
    for wall in ("front_wall", "rear_wall", "end_wall_x0", "end_wall_x24"):
        for row in spec["openings"][wall]["openings"]:
            if row["id"] == oid:
                return row
    raise KeyError(oid)


def partition(spec, pid):
    return next(p for p in spec["interior_partitions"]["layout"]["partitions"] if p["id"] == pid)


class VerifySpec(unittest.TestCase):

    def broken(self, change):
        spec = copy.deepcopy(yaml.safe_load(SPEC.read_text()))
        change(spec)
        return run(yaml.safe_dump(spec, sort_keys=False, width=150))

    def assertGateFails(self, r, label):
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        failed = [line for line in r.stdout.splitlines() if line.startswith("  [FAIL] ")]
        self.assertTrue(any(line[len("  [FAIL] "):].startswith(label) for line in failed),
                        f"expected [FAIL] {label!r}, got:\n{r.stdout}")

    def test_the_real_spec_passes(self):
        r = run(SPEC.read_text())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all gates pass", r.stdout)
        self.assertNotIn("[FAIL]", r.stdout)

    def test_the_front_wall_mirrored(self):
        def change(s):
            row = opening(s, "W-A1")
            row["x0"], row["x1"] = 3.5833, 7.5833
        self.assertGateFails(self.broken(change), "front openings follow from the string")

    def test_a_typo_in_the_front_string(self):
        def change(s):
            s["openings"]["front_wall"]["string"][1] = "4'-1\""
        self.assertGateFails(self.broken(change), "the front wall's string sums to the width")

    def test_window_b_off_the_door_on_the_wrong_side(self):
        def change(s):
            b, d = opening(s, "W-B1"), opening(s, "D-1")
            b["x0"], b["x1"], d["x0"], d["x1"] = d["x0"], d["x0"] + 1.5833, b["x0"] + 1.5833 - 3.0, b["x0"] + 1.5833
        self.assertGateFails(self.broken(change), "window B is on the X 24 side of door 1")

    def test_window_b_wider_than_its_rough_opening_allows(self):
        def change(s):
            b = opening(s, "W-B1")
            b["x1"] = b["x0"] + 1.5 + 0.25
        self.assertGateFails(self.broken(change), "window B's rough opening")

    def test_c_moved_to_the_x0_wall(self):
        def change(s):
            opening(s, "W-C1")["type"] = "D"
        self.assertGateFails(self.broken(change), "not mirrored: C and F")

    def test_the_rear_openings_mirrored(self):
        def change(s):
            for oid, (a, b) in (("D-6", (12.8333, 15.8333)), ("W-E1", (17.4167, 22.4167))):
                opening(s, oid)["x0"], opening(s, oid)["x1"] = a, b
        r = self.broken(change)
        self.assertGateFails(r, "rear openings follow from the string")
        self.assertGateFails(r, "not mirrored: the rear wall's door 6 and window E")

    def test_a_d_window_slid_along_the_wall(self):
        def change(s):
            row = opening(s, "W-D3")
            row["y0"] += 0.5
            row["y1"] += 0.5
        self.assertGateFails(self.broken(change), "end-wall openings follow from their strings")

    def test_a_seventh_d_window_is_a_count_mismatch(self):
        def change(s):
            s["openings"]["end_wall_x0"]["openings"].append(
                {"id": "W-D7", "type": "D", "y0": 0.1, "y1": 0.2, "derived": "test"})
        self.assertGateFails(self.broken(change), "the drawn window counts match")

    def test_overlapping_windows(self):
        def change(s):
            # the windows are 3" apart, so a slide of 0.4 ft runs D2 into D1
            opening(s, "W-D2")["y0"] = opening(s, "W-D2")["y0"] + 0.4
            opening(s, "W-D2")["y1"] = opening(s, "W-D2")["y1"] + 0.4
        self.assertGateFails(self.broken(change), "no two openings on a wall overlap")

    def test_an_opening_leaving_its_wall(self):
        def change(s):
            opening(s, "W-A1")["x1"] = 25.0
        self.assertGateFails(self.broken(change), "every opening sits inside its wall")

    def test_a_partition_face_moved(self):
        def change(s):
            partition(s, "P_pantry_N")["at_ft"] += 0.25
        self.assertGateFails(self.broken(change), "the partition faces follow from the interior strings")

    def test_a_partition_leaving_the_envelope(self):
        def change(s):
            partition(s, "P_bath_W")["to_ft"] = 24.5
        self.assertGateFails(self.broken(change), "every partition lies inside the envelope")

    def test_an_interior_door_of_the_wrong_width(self):
        def change(s):
            row = s["interior_partitions"]["layout"]["door_openings"][0]
            row["b_ft"] += 0.5
        self.assertGateFails(self.broken(change), "every interior door is its schedule width")

    def test_a_door_not_placed(self):
        def change(s):
            s["interior_partitions"]["layout"]["door_openings"] = [
                d for d in s["interior_partitions"]["layout"]["door_openings"] if d["id"] != "D-4"]
        self.assertGateFails(self.broken(change), "every row of the door schedule is built or recorded")

    def test_malformed_studs_toward_is_a_readable_failure(self):
        def change(s):
            partition(s, "P_bath_W")["studs_toward"] = "north"
        r = self.broken(change)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("studs_toward", r.stdout)

    def test_a_wrong_slope(self):
        def change(s):
            s["roof"]["main"]["slope"]["rise_in"] = 6
        self.assertGateFails(self.broken(change), "the heel's unexplained height")

    def test_a_wrong_top_of_roof(self):
        def change(s):
            s["levels"]["top_of_roof"]["ft"] = 14.5
        r = self.broken(change)
        self.assertGateFails(r, "the heel's unexplained height")
        self.assertGateFails(r, "the unexplained heel is a plausible")

    def test_a_wrong_porch_junction(self):
        def change(s):
            s["roof"]["porch"]["junction_depth"]["ft"] = 6.5
        self.assertGateFails(self.broken(change), "the porch roof meets the main roof")

    def test_a_junction_that_adds_the_eaves_to_the_rise(self):
        def change(s):
            s["roof"]["porch"]["junction_depth"]["ft"] = 5.6333      # the earlier, wrong derivation
        self.assertGateFails(self.broken(change), "the porch roof meets the main roof")

    def test_porch_eaves_not_the_rakes(self):
        def change(s):
            s["roof"]["porch"]["side_eaves"]["ft"] = 1.5
        self.assertGateFails(self.broken(change), "the porch roof's side eaves are the main roof's rakes")

    def test_a_ceiling_claimed_as_settled(self):
        def change(s):
            s["roof"]["ceiling"]["settled"] = True
        self.assertGateFails(self.broken(change), "the ceiling is declared an assumption")

    def test_a_ceiling_form_that_is_not_flat(self):
        def change(s):
            s["roof"]["ceiling"]["form"] = "follows_roof"
        self.assertGateFails(self.broken(change), "the ceiling form is flat at the plate and the partitions stop at it")

    def test_partitions_that_do_not_stop_at_the_ceiling(self):
        def change(s):
            s["interior_partitions"]["layout"]["height"]["to"] = "roof_underside"
        self.assertGateFails(self.broken(change), "the ceiling form is flat at the plate and the partitions stop at it")

    def test_a_ceiling_with_no_reason(self):
        def change(s):
            s["roof"]["ceiling"]["assumed"] = ""
        self.assertGateFails(self.broken(change), "the ceiling is declared an assumption")

    def test_a_wrong_area(self):
        def change(s):
            s["areas_declared"]["studio_sf"]["value"] = 480
        self.assertGateFails(self.broken(change), "the envelope's area is the declared 460 sf")

    def test_door_one_the_wrong_width(self):
        def change(s):
            door = next(d for d in s["openings"]["door_types"]["types"] if d["mark"] == "1")
            door["width"]["ft"] = 3.5
        self.assertGateFails(self.broken(change), "door 1 is its schedule width")

    def test_a_typo_in_the_rear_string(self):
        def change(s):
            s["openings"]["rear_wall"]["string"][0] = "9'-5\""
        self.assertGateFails(self.broken(change), "the rear wall's string sums to the width")

    def test_a_typo_in_the_x0_string(self):
        def change(s):
            s["openings"]["end_wall_x0"]["string"][0] = "2'-7\""
        self.assertGateFails(self.broken(change), "the X 0 wall's string sums to the depth")

    def test_a_typo_in_the_x0_halves(self):
        def change(s):
            s["openings"]["end_wall_x0"]["halves"]["first"] = "9'-10 1/2\""
        self.assertGateFails(self.broken(change), "the X 0 wall's two halves sum to the depth")

    def test_a_partition_running_through_another(self):
        def change(s):
            partition(s, "P_laundry_W")["at_ft"] = 11.3
        self.assertGateFails(self.broken(change), "no partition runs through another")

    def test_the_main_ridge_off_centre(self):
        def change(s):
            s["roof"]["main"]["ridge_at_y"]["ft"] = 8.0
        self.assertGateFails(self.broken(change), "the main ridge is at mid-depth")

    def test_a_porch_ridge_above_the_main_ridge(self):
        def change(s):
            s["roof"]["porch"]["slope"]["rise_in"] = 12
        self.assertGateFails(self.broken(change), "the porch ridge meets the main roof's front slope")

    def test_porch_post_spacing_that_does_not_sum(self):
        def change(s):
            s["roof"]["porch"]["posts"]["spacing"]["strings"][1] = "7'-4\""
        self.assertGateFails(self.broken(change), "the porch posts' spacing strings sum")

    def test_a_porch_post_moved(self):
        def change(s):
            s["roof"]["porch"]["posts"]["x"]["ft"][1] = 15.0
        self.assertGateFails(self.broken(change), "the porch posts' positions follow from their spacing")

    def test_a_missing_porch_post(self):
        def change(s):
            s["roof"]["porch"]["posts"]["count"] = 3
        self.assertGateFails(self.broken(change), "the porch posts' positions follow from their spacing")

    def test_porch_posts_outside_the_roof(self):
        def change(s):
            s["roof"]["porch"]["posts"]["setback_from_front_wall"]["ft"] = 6.0
        self.assertGateFails(self.broken(change), "the porch posts stand inside the porch roof's edge")

    def test_the_king_post_off_the_middle(self):
        def change(s):
            s["roof"]["porch"]["posts"]["king_post"]["at_x"]["ft"] = 10.0
        self.assertGateFails(self.broken(change), "the king post is at the middle")

    def test_the_porch_beam_off_the_plate(self):
        def change(s):
            s["roof"]["porch"]["posts"]["beam"]["top"]["ft"] = 7.0
        self.assertGateFails(self.broken(change), "the porch beam's top is at the plate line")

    def test_a_room_list_split_at_its_commas(self):
        def change(s):
            s["interior_partitions"]["rooms"] = ["kitchen", "bath (tub", "toilet", "36\" vanity)"]
        self.assertGateFails(self.broken(change), "the rooms are a non-empty list of whole tags")

    def test_a_scalar_rooms_value(self):
        def change(s):
            s["interior_partitions"]["rooms"] = "kitchen"
        self.assertGateFails(self.broken(change), "the rooms are a non-empty list of whole tags")

    def test_an_empty_rooms_list(self):
        def change(s):
            s["interior_partitions"]["rooms"] = []
        self.assertGateFails(self.broken(change), "the rooms are a non-empty list of whole tags")

    def test_two_openings_swapped_between_the_front_and_rear_walls(self):
        def change(s):
            o = s["openings"]
            a = next(r for r in o["front_wall"]["openings"] if r["id"] == "W-A2")
            e = next(r for r in o["rear_wall"]["openings"] if r["id"] == "W-E1")
            o["front_wall"]["openings"].remove(a)
            o["rear_wall"]["openings"].remove(e)
            o["front_wall"]["openings"].append(e)
            o["rear_wall"]["openings"].append(a)
        self.assertGateFails(self.broken(change), "each wall block holds exactly the openings the elevations draw")

    def test_an_opening_listed_on_two_walls(self):
        def change(s):
            o = s["openings"]
            o["rear_wall"]["openings"].append(dict(o["front_wall"]["openings"][0]))
        self.assertGateFails(self.broken(change), "each wall block holds exactly the openings the elevations draw")

    def test_a_zero_run_is_a_readable_failure_not_a_traceback(self):
        def change(s):
            s["roof"]["main"]["slope"]["run_in"] = 0
        r = self.broken(change)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("ZeroDivisionError", r.stdout)

    def test_studs_toward_parallel_to_the_wall(self):
        def change(s):
            row = partition(s, "P_bath_W")      # runs along X
            row["studs_toward"] = "+X"
        self.assertGateFails(self.broken(change), "every partition's studs run across it")

    def test_a_y_running_wall_with_y_studs(self):
        def change(s):
            partition(s, "P_pantry_N")["studs_toward"] = "-Y"      # runs along Y
        self.assertGateFails(self.broken(change), "every partition's studs run across it")

    def test_the_bath_wall_off_the_rear_strings_first_segment(self):
        def change(s):
            row = partition(s, "P_bath_S")
            row["at_ft"] += 0.25
        self.assertGateFails(self.broken(change), "the bath wall's far face is the rear string's first segment")

    def test_window_a_the_wrong_width(self):
        def change(s):
            opening(s, "W-A1")["x0"] -= 0.5
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_window_d_the_wrong_width(self):
        def change(s):
            opening(s, "W-D1")["y0"] -= 0.5
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_window_e_the_wrong_width(self):
        def change(s):
            opening(s, "W-E1")["x0"] -= 0.5
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_door_six_the_wrong_width(self):
        def change(s):
            opening(s, "D-6")["x1"] += 0.5
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_window_b_with_no_unit_span(self):
        def change(s):
            del opening(s, "W-B1")["unit_x0"]
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_window_b_unit_off_centre(self):
        def change(s):
            b = opening(s, "W-B1")
            b["unit_x0"] -= 0.04
            b["unit_x1"] -= 0.04
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_window_b_unit_the_wrong_width(self):
        def change(s):
            opening(s, "W-B1")["unit_x1"] += 0.04
        self.assertGateFails(self.broken(change), "every exterior opening is its schedule width")

    def test_a_plain_single_hung_window_given_two_units(self):
        def change(s):
            s["windows"]["operations"]["single_hung"]["units"] = 2
        self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_a_double_window_given_one_unit(self):
        def change(s):
            s["windows"]["operations"]["single_hung_double"]["units"] = 1
        self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_a_window_naming_an_operation_that_is_not_defined(self):
        def change(s):
            s["openings"]["window_types"]["types"][2]["operation"] = "awning"
        self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_a_porch_footprint_of_the_wrong_width(self):
        def change(s):
            s["roof"]["porch"]["footprint"]["width"]["ft"] = 20.0
        self.assertGateFails(self.broken(change), "the porch footprint is the front wall's width")

    def test_a_porch_footprint_that_is_not_122_sf(self):
        def change(s):
            s["roof"]["porch"]["footprint"]["area"]["value_sf"] = 150
        self.assertGateFails(self.broken(change), "the porch footprint's width x depth is the sheet's 122 sf")

    def test_a_porch_depth_far_from_the_roof_projection(self):
        def change(s):
            s["roof"]["porch"]["footprint"]["depth"]["ft"] = 6.0
        self.assertGateFails(self.broken(change), "the porch depth is within an inch of the roof's 5'-0\" projection")

    def test_two_setback_readings_that_disagree(self):
        def change(s):
            s["roof"]["porch"]["posts"]["setback_second_reading"]["ft"] = 5.0
        self.assertGateFails(self.broken(change), "A-1.0's two readings of the post line's setback agree")

    def test_a_partition_id_used_twice(self):
        def change(s):
            parts = s["interior_partitions"]["layout"]["partitions"]
            parts.append(copy.deepcopy(parts[0]))
        self.assertGateFails(self.broken(change), "every partition id is used once")

    def test_an_interior_door_id_used_twice(self):
        def change(s):
            doors = s["interior_partitions"]["layout"]["door_openings"]
            doors.append(copy.deepcopy(doors[0]))
        self.assertGateFails(self.broken(change), "every interior door id is used once")

    def test_an_interior_door_with_an_exterior_openings_id(self):
        def change(s):
            s["interior_partitions"]["layout"]["door_openings"][0]["id"] = "D-1"
        self.assertGateFails(self.broken(change), "every interior door id is used once")

    def test_two_interior_doors_sharing_a_span(self):
        def change(s):
            doors = s["interior_partitions"]["layout"]["door_openings"]
            second = copy.deepcopy(doors[0])
            second["id"] = "D-2b"
            doors.append(second)
        self.assertGateFails(self.broken(change), "no two interior doors in one wall overlap")

    def test_a_post_section_that_is_the_nominal_size(self):
        def change(s):
            s["roof"]["porch"]["posts"]["section"]["width"]["ft"] = 0.5
        self.assertGateFails(self.broken(change), "the posts' and beam's sections are the dressed sizes")

    def test_a_beam_section_that_is_the_nominal_size(self):
        def change(s):
            s["roof"]["porch"]["posts"]["beam"]["section"]["depth"]["ft"] = 10 / 12
        self.assertGateFails(self.broken(change), "the posts' and beam's sections are the dressed sizes")

    def test_posts_that_stop_short_of_the_beam(self):
        def change(s):
            s["roof"]["porch"]["posts"]["z1"]["ft"] = 7.0
        self.assertGateFails(self.broken(change), "the posts run from grade to the beam's underside")

    def test_posts_that_start_above_grade(self):
        def change(s):
            s["roof"]["porch"]["posts"]["z0"]["ft"] = 0.0
        self.assertGateFails(self.broken(change), "the posts run from grade to the beam's underside")

    def test_a_beam_that_does_not_reach_the_last_post(self):
        def change(s):
            s["roof"]["porch"]["posts"]["beam"]["x1"]["ft"] = 20.0
        self.assertGateFails(self.broken(change), "the beam runs from the first post to the last")

    def test_a_roof_form_that_is_not_two_gables(self):
        def change(s):
            s["roof"]["form"] = "shed"
        self.assertGateFails(self.broken(change), "the roof is two gables")

    def test_a_main_roof_that_is_not_a_gable(self):
        def change(s):
            s["roof"]["main"]["form"] = "shed"
        self.assertGateFails(self.broken(change), "the roof is two gables")

    def test_a_porch_roof_that_is_not_a_gable(self):
        def change(s):
            s["roof"]["porch"]["form"] = "hip"
        self.assertGateFails(self.broken(change), "the roof is two gables")

    def test_a_main_ridge_along_y(self):
        def change(s):
            s["roof"]["main"]["ridge_runs_along"] = "Y"
        self.assertGateFails(self.broken(change), "the roof is two gables")

    def test_a_porch_ridge_along_x(self):
        def change(s):
            s["roof"]["porch"]["ridge_runs_along"] = "X"
        self.assertGateFails(self.broken(change), "the roof is two gables")

    def test_a_missing_ridge_direction(self):
        def change(s):
            del s["roof"]["porch"]["ridge_runs_along"]
        self.assertGateFails(self.broken(change), "the roof is two gables")

    def test_an_elevation_fact_that_disagrees_with_the_openings(self):
        def change(s):
            s["frame"]["drawn_on"]["walls"]["C"] = "end_wall_x0"
        self.assertGateFails(self.broken(change), "every opening is on the wall the elevations draw its mark on")

    def test_a_window_drawn_on_the_wrong_wall_of_the_openings(self):
        def change(s):
            o = s["openings"]
            e = next(r for r in o["rear_wall"]["openings"] if r["id"] == "W-E1")
            o["rear_wall"]["openings"].remove(e)
            o["front_wall"]["openings"].append(e)
        self.assertGateFails(self.broken(change), "every opening is on the wall the elevations draw its mark on")

    def test_a_mark_the_elevations_do_not_draw(self):
        def change(s):
            del s["frame"]["drawn_on"]["walls"]["F"]
        self.assertGateFails(self.broken(change), "every opening is on the wall the elevations draw its mark on")

    def test_a_meeting_rail_ratio_above_the_window(self):
        def change(s):
            s["windows"]["meeting_rail"]["ratio"] = 2
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_ratio_of_zero_or_less(self):
        for bad in (0, -0.5):
            def change(s, bad=bad):
                s["windows"]["meeting_rail"]["ratio"] = bad
            with self.subTest(ratio=bad):
                self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_ratio_that_is_not_a_number(self):
        def change(s):
            s["windows"]["meeting_rail"]["ratio"] = "half"
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_too_thick_for_the_sash(self):
        def change(s):
            s["windows"]["meeting_rail"]["thickness"]["ft"] = 3.5      # as tall as window C: no room for the sill and head
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_that_lands_on_the_sill(self):
        def change(s):
            s["windows"]["meeting_rail"]["ratio"] = 0.01
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_frame_width_that_is_not_positive(self):
        def change(s):
            s["windows"]["frame_to_glass"]["ft"] = -0.1
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_thickness_that_is_a_string(self):
        def change(s):
            s["windows"]["meeting_rail"]["thickness"]["ft"] = "0.1"
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_thickness_that_is_a_boolean(self):
        def change(s):
            s["windows"]["meeting_rail"]["thickness"]["ft"] = True
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_a_meeting_rail_ratio_that_is_a_boolean(self):
        def change(s):
            s["windows"]["meeting_rail"]["ratio"] = True
        self.assertGateFails(self.broken(change), "every meeting rail lies inside its sash")

    def test_the_single_hung_rail_flag_switched_off(self):
        def change(s):
            s["windows"]["operations"]["single_hung"]["meeting_rail"] = False
        self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_a_fixed_window_given_a_rail(self):
        def change(s):
            s["windows"]["operations"]["fixed"]["meeting_rail"] = True
        self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_a_truthy_non_boolean_rail_flag(self):
        for bad in (1, "true", "yes", [1]):
            def change(s, bad=bad):
                s["windows"]["operations"]["single_hung_double"]["meeting_rail"] = bad
            with self.subTest(flag=bad):
                self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_units_that_are_a_boolean_or_a_string(self):
        for bad in (True, "1"):
            def change(s, bad=bad):
                s["windows"]["operations"]["single_hung"]["units"] = bad
            with self.subTest(units=bad):
                self.assertGateFails(self.broken(change), "every window's operation has the number of side-by-side units")

    def test_a_door_leaf_that_is_negative_zero_or_a_string(self):
        for bad in (-0.1, 0, "0.1", True, float("inf")):
            def change(s, bad=bad):
                s["openings"]["door_types"]["leaf_thickness"]["ft"] = bad
            with self.subTest(leaf=bad):
                self.assertGateFails(self.broken(change), "the door leaf is a positive thickness thinner than the thinnest wall")

    def test_a_door_leaf_as_thick_as_the_wall(self):
        for bad in (0.2917, 0.4583, 1.0):
            def change(s, bad=bad):
                s["openings"]["door_types"]["leaf_thickness"]["ft"] = bad
            with self.subTest(leaf=bad):
                self.assertGateFails(self.broken(change), "the door leaf is a positive thickness thinner than the thinnest wall")

    def test_a_missing_block_names_itself(self):
        def change(s):
            del s["openings"]["end_wall_x0"]
        r = self.broken(change)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("the spec has the blocks these gates read", r.stdout)

    def test_malformed_yaml_is_a_failed_gate_not_a_traceback(self):
        r = run("meta: [unclosed\nlevels: {a: 1\n")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("[FAIL] the spec is valid YAML", r.stdout)

    def test_an_unreadable_spec_path_is_readable_failure(self):
        r = subprocess.run([sys.executable, str(VERIFY), str(HERE / "no_such_spec.yaml")],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("cannot read", r.stdout)

    def test_duplicate_keys_are_named(self):
        text = SPEC.read_text() + "\nlevels:\n  datum: finished_floor\n"
        r = run(text)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("[FAIL] no duplicate keys", r.stdout)


if __name__ == "__main__":
    unittest.main()
