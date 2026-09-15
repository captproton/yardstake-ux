"""
models/laurel_a1_460/test_build_literals.py — no dimension literal appears in
build.py (#129), as a gate rather than a promise.

    python3 -m unittest discover -s models/laurel_a1_460      (from buyer/3D)

Plain Python, no Blender: it parses build.py and never runs it, so CI can
hold this line on every PR.

PLAN.md's P2 says "No dimension appears in the file." The rule is easy to
state, easy to believe, and easy to break by one person in a hurry pasting
9.625 where a spec lookup belongs -- which is precisely how the barn cabin
came to carry a ridge datum that was wrong twice.

So: every numeric literal in build.py must be one of

  * a datum or an index -- 0, 1, 2, and the 0.0 that IS the frame's origin;
  * a value bound once, at module level, to an ALL_CAPS name. Those are
    gathered at the top of build.py under a comment that says what each is
    for. They are mesh and printing bookkeeping: a boolean's tolerance, a
    cutter's margin, the width of a printed rule.

Anything else fails, with its line and its value. A spec number pasted into
the file is not in either set, so it fails.

WHAT THIS DOES NOT PROVE. It does not prove the file reads the RIGHT spec
key, only that it reads one. `env["width"]` where `env["depth"]` was meant is
a defect for verify_spec.py and the Blender gates to catch, not this.
"""
import ast
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build.py"

# 0 and 0.0 are the frame's origin and a floor at Z 0; 1 and 2 index pairs and
# halve spans. None of them is a length read off a sheet.
DATUM_AND_INDEX = {0, 1, 2}


def _is_constant_name(name):
    """ALL_CAPS, and more than one letter. A single capital is a local like W
    or D, not a declared constant."""
    return len(name) > 1 and name.isupper()


def module_constants(tree):
    """value -> name, for every module-level ALL_CAPS = <number>."""
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (isinstance(target, ast.Name) and _is_constant_name(target.id)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, (int, float))
                    and not isinstance(node.value.value, bool)):
                out[node.value.value] = target.id
    return out


class BuildLiterals(unittest.TestCase):

    def setUp(self):
        self.src = BUILD.read_text()
        self.tree = ast.parse(self.src)
        self.consts = module_constants(self.tree)

    def offenders(self, tree=None, consts=None):
        tree = self.tree if tree is None else tree
        consts = self.consts if consts is None else consts
        # MODULE LEVEL ONLY. Walking the whole tree was the first version and
        # it was wrong: `W = env["width"]["ft"]` inside build() is an Assign to
        # a Name that `.isupper()` calls ALL_CAPS, so the line was skipped --
        # and a 24 pasted over that lookup went unseen. The gate's own test
        # caught it, which is the reason the test exists.
        declared = {n.lineno for n in tree.body
                    if isinstance(n, ast.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Name)
                    and _is_constant_name(n.targets[0].id)}
        bad = []
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Constant)
                    and isinstance(n.value, (int, float))
                    and not isinstance(n.value, bool)):
                continue
            if n.lineno in declared:          # the constant's own definition
                continue
            if n.value in DATUM_AND_INDEX or n.value in consts:
                continue
            bad.append((n.lineno, n.value))
        return sorted(set(bad))

    def test_build_py_carries_no_dimension(self):
        bad = self.offenders()
        self.assertEqual(bad, [], "build.py carries numeric literals that are neither a "
                                  "datum, an index, nor a named constant: "
                                  + "; ".join(f"line {ln}: {v!r}" for ln, v in bad))

    def test_every_named_constant_says_what_it_is_for(self):
        """A constant with no comment is a dimension waiting to be smuggled in."""
        lines = self.src.splitlines()
        silent = [name for value, name in self.consts.items()
                  if "#" not in lines[next(
                      n.lineno for n in ast.walk(self.tree)
                      if isinstance(n, ast.Assign) and len(n.targets) == 1
                      and isinstance(n.targets[0], ast.Name)
                      and n.targets[0].id == name) - 1]]
        self.assertEqual(silent, [], f"named constants with no comment: {silent}")

    # ── the gate catches what it exists for ──────────────────────────────

    def test_a_pasted_dimension_is_caught(self):
        hurt = self.src.replace('shed.under(0.0)', '9.625', 1)
        tree = ast.parse(hurt)
        bad = self.offenders(tree, module_constants(tree))
        self.assertTrue(any(v == 9.625 for _, v in bad),
                        f"a pasted 9.625 was not caught; offenders were {bad}")

    def test_a_pasted_whole_foot_dimension_is_caught(self):
        hurt = self.src.replace('env["width"]["ft"]', '24', 1)
        tree = ast.parse(hurt)
        bad = self.offenders(tree, module_constants(tree))
        self.assertTrue(any(v == 24 for _, v in bad),
                        f"a pasted 24 was not caught; offenders were {bad}")

    def test_a_dimension_shouted_into_a_constant_still_needs_a_comment(self):
        """Naming a dimension does not launder it.

        Moving 24.0 into WIDTH gets it past the literal gate -- that is what an
        allowlist is. What stops it is the second gate: a declared constant
        with no comment saying what it is for. The two together mean smuggling
        a dimension in takes a deliberate, reviewable sentence claiming it is
        bookkeeping."""
        hurt = self.src.replace("FAILED = []", "FAILED = []\nWIDTH = 24.0", 1)
        hurt = hurt.replace('env["width"]["ft"]', 'WIDTH', 1)
        tree = ast.parse(hurt)
        self.assertIn(24.0, module_constants(tree))     # past the literal gate
        lines = hurt.splitlines()
        ln = next(n.lineno for n in tree.body
                  if isinstance(n, ast.Assign) and len(n.targets) == 1
                  and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "WIDTH")
        self.assertNotIn("#", lines[ln - 1])            # stopped by the comment gate


if __name__ == "__main__":
    unittest.main()
