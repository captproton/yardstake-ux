"""
test_publish.py — adu_kit.publish, without Blender (#131).

    python3 -m unittest adu_kit.test_publish     (from buyer/3D)
"""
import tempfile
import unittest
from pathlib import Path

from adu_kit.publish import promote, stage


class Publish(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.final = Path(self.tmp.name) / "export"

    def tearDown(self):
        self.tmp.cleanup()

    def test_stage_is_a_fresh_sibling(self):
        out = stage(self.final)
        (out / "leftover.glb").write_text("x")
        again = stage(self.final)
        self.assertEqual(again, self.final.parent / "export.staging")
        self.assertEqual(list(again.iterdir()), [])
        self.assertTrue(self.final.is_dir())

    def test_the_new_generation_replaces_the_old(self):
        self.final.mkdir()
        (self.final / "m_lod0.glb").write_text("old")
        out = stage(self.final)
        (out / "m_lod0.glb").write_text("new")
        promote(out, self.final)
        self.assertEqual((self.final / "m_lod0.glb").read_text(), "new")
        self.assertFalse(out.exists())

    def test_a_file_the_new_run_did_not_write_is_removed(self):
        """Found by review: a level an earlier run exported and this one did
        not stayed beside the new files, and build_index.py reads every .glb
        it finds -- one generation's index over another's files."""
        self.final.mkdir()
        for name in ("m_lod0.glb", "m_lod3.glb", "variants.json"):
            (self.final / name).write_text("old")
        out = stage(self.final)
        for name in ("m_lod0.glb", "variants.json"):
            (out / name).write_text("new")
        removed = promote(out, self.final)
        self.assertEqual(removed, ["m_lod3.glb"])
        self.assertEqual(sorted(p.name for p in self.final.iterdir()),
                         ["m_lod0.glb", "variants.json"])


if __name__ == "__main__":
    unittest.main()
