"""
test_manifest.py — adu_kit.manifest, without Blender (#131).

    python3 -m unittest adu_kit.test_manifest     (from buyer/3D)

The known answers are the barn cabin's own: its committed variants.json is
rebuilt from its spec and its lod0 .glb, and must come out the same. That is
the test that the move out of finish_adu.py was a move.
"""
import json
import unittest
from pathlib import Path

import yaml

from adu_kit import manifest
from adu_kit.schema import model_contract

HERE = Path(__file__).resolve().parent
BARN = HERE.parent / "models" / "barn_cabin_524"
LOD0 = BARN / "export" / "barn_cabin_524_lod0.glb"


def barn():
    spec = yaml.safe_load((BARN / "spec.yaml").read_text())
    published = json.loads((BARN / "export" / "variants.json").read_text())
    mats, nodes = model_contract.glb_names(LOD0)
    return spec, published, mats, nodes


def modes(*ms, groups=None):
    return {"groups": groups or {"roof": ["Roof_"], "wall": ["Wall_"]},
            "modes": list(ms)}


class KnownAnswers(unittest.TestCase):
    """The barn cabin's published manifest, rebuilt."""

    @classmethod
    def setUpClass(cls):
        cls.spec, cls.published, cls.mats, cls.nodes = barn()

    def test_sets_rebuild_the_published_ones(self):
        sets, problems = manifest.sets_block(self.spec["variants"], self.mats)
        self.assertEqual(problems, [])
        self.assertEqual(sets, self.published["sets"])

    def test_views_rebuild_the_published_ones(self):
        views, problems = manifest.views_block(
            self.spec["export"]["display_modes"], self.nodes)
        self.assertEqual(problems, [])
        self.assertEqual(views, self.published["views"])
        self.assertEqual(manifest.VIEWS_NOTE, self.published["views_note"])

    def test_identity_rebuilds_the_published_one(self):
        ident, problems = manifest.identity_block(
            self.spec, LOD0, self.published["model"]["note"])
        self.assertEqual(problems, [])
        # KEY ORDER TOO: the manifest is written with json.dumps, so a
        # reordered block is a different file.
        self.assertEqual(list(ident.items()), list(self.published["model"].items()))


class Sets(unittest.TestCase):

    def v(self, **option):
        opt = {"id": "a", "label": "A", "value": [0.1, 0.2, 0.3], "default": True}
        opt.update(option)
        return {"sets": [{"id": "wall", "label": "Wall", "targets": ["adu_wall"],
                          "options": [opt]}]}

    def test_alpha_is_appended(self):
        sets, problems = manifest.sets_block(self.v(), {"adu_wall"})
        self.assertEqual(problems, [])
        self.assertEqual(sets[0]["options"][0]["value"], [0.1, 0.2, 0.3, 1.0])
        self.assertEqual(sets[0]["property"], "baseColorFactor")

    def test_a_target_the_export_lacks(self):
        _, problems = manifest.sets_block(self.v(), {"adu_roof"})
        self.assertIn("wall -> unknown material adu_wall", problems)

    def test_no_default(self):
        _, problems = manifest.sets_block(self.v(default=False), {"adu_wall"})
        self.assertIn("wall needs exactly one default", problems)

    def test_an_rgba_value_keeps_its_alpha(self):
        """Found by review: alpha was appended unconditionally, so a valid
        four-number colour became five and the contract refused it."""
        sets, problems = manifest.sets_block(self.v(value=[0.1, 0.2, 0.3, 1.0]), {"adu_wall"})
        self.assertEqual(problems, [])
        self.assertEqual(sets[0]["options"][0]["value"], [0.1, 0.2, 0.3, 1.0])

    def test_no_sets_list_is_a_problem_not_a_crash(self):
        for variants in ({}, {"sets": "wall"}, None):
            with self.subTest(variants=variants):
                sets, problems = manifest.sets_block(variants, {"adu_wall"})
                self.assertEqual(sets, [])
                self.assertIn("variants.sets must be a list", problems[0])

    def test_a_malformed_set_is_named_not_raised(self):
        for bad in ("wall", {"id": "wall", "label": "Wall", "targets": ["adu_wall"]},
                    {"id": "wall", "label": "Wall", "targets": ["adu_wall"],
                     "options": [{"id": "a", "label": "A"}]}):
            with self.subTest(bad=bad):
                _, problems = manifest.sets_block({"sets": [bad]}, {"adu_wall"})
                self.assertTrue(any(p.startswith("variants.sets[0] is malformed")
                                    for p in problems), problems)


class Views(unittest.TestCase):
    NODES = {"Roof_main", "Wall_front", "Wall_rear", "Slab"}

    def test_missing_modes_are_a_problem_not_an_empty_block(self):
        views, problems = manifest.views_block(None, self.NODES)
        self.assertIsNone(views)
        self.assertIn("display_modes is missing", problems[0])

    def test_prefixes_resolve_to_sorted_names(self):
        views, problems = manifest.views_block(
            modes({"id": "x", "label": "X", "default": True, "hide": ["wall"]}), self.NODES)
        self.assertEqual(problems, [])
        self.assertEqual(views[0]["hide"], ["Wall_front", "Wall_rear"])

    def test_hide_objects_names_exactly_one(self):
        """A single wall, where the prefix would take its neighbours too."""
        views, problems = manifest.views_block(
            modes({"id": "x", "label": "X", "default": True, "hide": ["roof"],
                   "hide_objects": ["Wall_front"]}), self.NODES)
        self.assertEqual(problems, [])
        self.assertEqual(views[0]["hide"], ["Roof_main", "Wall_front"])

    def test_hide_objects_that_were_not_exported(self):
        _, problems = manifest.views_block(
            modes({"id": "x", "label": "X", "default": True, "hide": [],
                   "hide_objects": ["Wall_side"]}), self.NODES)
        self.assertTrue(any("hides objects that were not exported: ['Wall_side']" in p
                            for p in problems), problems)

    def test_a_prefix_that_matches_nothing(self):
        _, problems = manifest.views_block(
            modes({"id": "x", "label": "X", "default": True, "hide": []},
                  groups={"roof": ["Roof_", "Rooof_"]}), self.NODES)
        self.assertTrue(any("['Rooof_']" in p for p in problems), problems)

    def test_an_unknown_group_is_reported_not_raised(self):
        _, problems = manifest.views_block(
            modes({"id": "x", "label": "X", "default": True, "hide": ["ceiling"]}), self.NODES)
        self.assertTrue(any("do not exist: ['ceiling']" in p for p in problems), problems)

    def test_two_defaults(self):
        _, problems = manifest.views_block(
            modes({"id": "a", "label": "A", "default": True, "hide": []},
                  {"id": "b", "label": "B", "default": True, "hide": ["roof"]}), self.NODES)
        self.assertTrue(any("exactly one default" in p for p in problems), problems)

    def test_malformed_shapes_are_named_not_raised(self):
        """Found by review: a YAML typo in display_modes raised AttributeError
        or TypeError and aborted the export with a traceback."""
        ok_mode = {"id": "x", "label": "X", "default": True, "hide": ["roof"]}
        cases = {
            "display_modes must be an object": ["full"],
            "groups must map each group": {"groups": ["Roof_"], "modes": [ok_mode]},
            "groups.roof must be a list of name prefixes": {"groups": {"roof": "Roof_"},
                                                            "modes": [ok_mode]},
            "modes must be a list": {"groups": {"roof": ["Roof_"]}, "modes": {"x": ok_mode}},
            "modes[0] must be an object": {"groups": {"roof": ["Roof_"]}, "modes": ["full"]},
            # Found by review: YAML reads `2:` as an int, and sorting the
            # group names for the unknown-group message then raised TypeError.
            "groups has a name that is not text: 2": {
                "groups": {2: ["Roof_"], "roof": ["Roof_"]},
                "modes": [dict(ok_mode, hide=["ceiling"])]},
            "modes[0].label must be a non-empty string": {
                "groups": {"roof": ["Roof_"]}, "modes": [{"id": "x", "default": True, "hide": []}]},
            "modes[0].hide must be a list of names": {
                "groups": {"roof": ["Roof_"]}, "modes": [dict(ok_mode, hide="roof")]},
            "modes[0].hide_objects must be a list of names": {
                "groups": {"roof": ["Roof_"]}, "modes": [dict(ok_mode, hide_objects="Wall_front")]},
        }
        for expected, dm in cases.items():
            with self.subTest(expected=expected):
                views, problems = manifest.views_block(dm, self.NODES)
                self.assertIsNone(views)
                self.assertTrue(any(expected in p for p in problems), problems)


class Identity(unittest.TestCase):

    def spec(self, **index):
        idx = {"area_key": "total", "storeys": {"count": 1, "loft": False},
               "front": {"glb": "+z", "entry": "Door_D-FRONT"}}
        idx.update(index)
        return {"meta": {"model_id": "m", "display_name": "M", "index": idx},
                "areas_declared": {"total": {"value": 500, "source": "sheet"}}}

    def test_a_valid_spec_meets_the_contract(self):
        ident, problems = manifest.identity_block(self.spec(), LOD0, "a note")
        self.assertEqual(problems, [])
        self.assertEqual(model_contract.identity_problems(ident), [])
        self.assertEqual(ident["note"], "a note")

    def test_an_area_key_not_declared(self):
        _, problems = manifest.identity_block(self.spec(area_key="gross"), LOD0, "")
        self.assertIn("meta.index.area_key is 'gross', which is not a key of areas_declared",
                      problems)

    def test_no_entry_node(self):
        _, problems = manifest.identity_block(self.spec(front={"glb": "+z"}), LOD0, "")
        self.assertTrue(any("front.entry is unset" in p for p in problems), problems)

    def test_the_wrong_front_is_held_to_the_file(self):
        _, problems = manifest.identity_block(
            self.spec(front={"glb": "-z", "entry": "Door_D-FRONT"}), LOD0, "")
        self.assertTrue(any("but front is declared -z" in p for p in problems), problems)

    def test_malformed_levels_are_named_not_raised(self):
        """Found by review: `spec["meta"]` raised KeyError on a spec without
        one, and a list where a mapping belongs raised AttributeError."""
        good = self.spec()
        cases = {
            "meta must be an object": dict(good, meta=["m"]),
            "meta.index must be an object": dict(good, meta=dict(good["meta"], index=["x"])),
            "areas_declared must be an object": dict(good, areas_declared=[500]),
            "meta.index.area_key is unset": {"areas_declared": good["areas_declared"]},
        }
        for expected, spec in cases.items():
            with self.subTest(expected=expected):
                _, problems = manifest.identity_block(spec, LOD0, "")
                self.assertTrue(any(expected in p for p in problems), problems)



class Baseline(unittest.TestCase):
    """model_contract.baseline_problems: the lod2 baseline, asserted (#131)."""
    LOD2 = BARN / "export" / "barn_cabin_524_lod2.glb"

    @classmethod
    def setUpClass(cls):
        spec = yaml.safe_load((BARN / "spec.yaml").read_text())
        cls.base = spec["export"]["lod2_baseline"]

    def test_the_barn_cabins_lod2_sits_on_its_baseline(self):
        self.assertEqual(model_contract.baseline_problems(self.LOD2, self.base), [])

    def test_lod0_misses_the_baseline_its_footing_reaches_lower(self):
        problems = model_contract.baseline_problems(BARN / "export" / "barn_cabin_524_lod0.glb", self.base)
        self.assertTrue(any("floor (min y) is -1.1750 m" in p for p in problems), problems)

    def test_a_moved_origin_is_named(self):
        moved = dict(self.base, x_m={"value": [0.0, 7.62], "derived": "moved"})
        problems = model_contract.baseline_problems(self.LOD2, moved)
        self.assertTrue(any("min x" in p for p in problems), problems)

    def test_units_and_axis_are_declared(self):
        problems = model_contract.baseline_problems(self.LOD2, dict(self.base, units="feet", up="+z"))
        self.assertTrue(any("units must be 'metres'" in p for p in problems), problems)
        self.assertTrue(any("up must be '+y'" in p for p in problems), problems)

    def test_a_non_finite_value_is_refused_not_passed(self):
        """Found by review: NaN compares false with everything, so a NaN
        floor passed the tolerance check without being checked."""
        nan, inf = float("nan"), float("inf")
        for bad in (dict(self.base, floor_y_m={"value": nan, "derived": "x"}),
                    dict(self.base, x_m={"value": [nan, 7.1628], "derived": "x"}),
                    dict(self.base, z_m={"value": [-9.6012, inf], "derived": "x"}),
                    # Found by review: too large for a float, so isfinite()
                    # raised OverflowError instead of returning False.
                    dict(self.base, floor_y_m={"value": 10 ** 400, "derived": "x"})):
            with self.subTest(bad=bad):
                problems = model_contract.baseline_problems(self.LOD2, bad)
                self.assertTrue(any("finite" in p for p in problems), problems)

    def test_a_malformed_baseline_is_a_problem_not_a_crash(self):
        for bad in (None, ["x"], dict(self.base, floor_y_m="low")):
            with self.subTest(bad=bad):
                self.assertTrue(model_contract.baseline_problems(self.LOD2, bad))


if __name__ == "__main__":
    unittest.main()
