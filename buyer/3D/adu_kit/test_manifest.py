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


if __name__ == "__main__":
    unittest.main()
