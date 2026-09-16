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
    """[(name, value, lineno)] for every module-level ALL_CAPS = <number>.

    A LIST, NOT A DICT KEYED BY VALUE. Keyed by value, two constants sharing
    one number collapsed: the later declaration overwrote the earlier, the
    comment gate below only ever saw the survivor, and an undocumented
    constant could hide behind a documented one with the same value. Review
    caught it; reproduced by declaring a second constant equal to RULE.
    """
    out = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (isinstance(target, ast.Name) and _is_constant_name(target.id)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, (int, float))
                    and not isinstance(node.value.value, bool)):
                out.append((target.id, node.value.value, node.lineno))
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
        # A SIGNED LITERAL IS TWO NODES, and ast.walk visits the inner one.
        # `-1` is UnaryOp(USub, Constant(1)), so the gate saw a bare 1, called
        # it an allowed index, and let a negative length through. Review found
        # it. Every negated constant is recorded here by its signed value, and
        # the inner node is then skipped so it is not judged twice.
        signed = {}
        for n in ast.walk(tree):
            if (isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd))
                    and isinstance(n.operand, ast.Constant)
                    and isinstance(n.operand.value, (int, float))
                    and not isinstance(n.operand.value, bool)):
                value = n.operand.value
                signed[id(n.operand)] = -value if isinstance(n.op, ast.USub) else value

        bad = []
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Constant)
                    and isinstance(n.value, (int, float))
                    and not isinstance(n.value, bool)):
                continue
            if n.lineno in declared:          # the constant's own definition
                continue
            if id(n) in signed:
                value = signed[id(n)]
                if value != 0:                # -0.0 is still the origin
                    bad.append((n.lineno, value))
                continue
            # ONLY THE DECLARATION IS EXEMPT, NEVER THE VALUE. This used to
            # read `n.value in consts`, which allowed any literal that
            # happened to EQUAL a declared constant anywhere in the file --
            # so once SASH_FRAME_MEMBERS = 4 and VERTS_PER_BOX = 8 existed, a
            # 4 or an 8 pasted in as a dimension sailed through the gate
            # written to reject it. Review caught it; the hole was reproduced
            # before it was closed. A reference to a constant is a Name node
            # and never reaches here, so it needs no exemption at all.
            # AN INT IS AN INDEX; A FLOAT IS A LENGTH. Testing membership
            # alone let 1.0 through, because Python says 1.0 == 1 and 1 is an
            # allowed index -- so a one-foot length written as a float read as
            # a list subscript. The only float that is a datum is 0.0, which
            # is where this frame's origin and its finished floor both sit.
            if isinstance(n.value, int) and n.value in DATUM_AND_INDEX:
                continue
            if isinstance(n.value, float) and n.value == 0.0:
                continue
            bad.append((n.lineno, n.value))
        return sorted(set(bad))

    def test_build_py_carries_no_dimension(self):
        bad = self.offenders()
        self.assertEqual(bad, [], "build.py carries numeric literals that are neither a "
                                  "datum, an index, nor a named constant: "
                                  + "; ".join(f"line {ln}: {v!r}" for ln, v in bad))

    def test_every_named_constant_says_what_it_is_for(self):
        """A constant with no comment is a dimension waiting to be smuggled in.

        EVERY DECLARATION IS CHECKED, not one per distinct value: two
        constants sharing a number used to collapse, and the undocumented one
        could hide behind the documented one."""
        lines = self.src.splitlines()
        silent = [name for name, _value, lineno in self.consts
                  if "#" not in lines[lineno - 1]]
        self.assertEqual(silent, [], f"named constants with no comment: {silent}")

    def test_two_constants_with_one_value_are_both_seen(self):
        """Found by review. Keyed by value, the second declaration overwrote
        the first and only the survivor was ever checked for a comment."""
        rule = next(v for n, v, _ in self.consts if n == "RULE")
        hurt = self.src.replace(f"RULE = {rule}", f"SNEAKY = {rule}\nRULE = {rule}", 1)
        names = [n for n, _v, _l in module_constants(ast.parse(hurt))]
        self.assertIn("SNEAKY", names)
        self.assertIn("RULE", names)

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

    def test_a_dimension_that_collides_with_a_constants_value_is_caught(self):
        """Found by review. The gate exempted any literal EQUAL to a declared
        constant, so once SASH_FRAME_MEMBERS was 4, a 4 pasted anywhere passed.
        Every value this module declares is tried here, so adding a constant
        cannot quietly re-open the hole."""
        for name, value, _lineno in self.consts:
            hurt = self.src.replace('env["width"]["ft"]', repr(value), 1)
            tree = ast.parse(hurt)
            bad = self.offenders(tree, module_constants(tree))
            self.assertTrue(any(v == value for _, v in bad),
                            f"a pasted {value!r}, the value of {name}, "
                            f"was not caught; offenders were {bad}")

    def test_a_negative_dimension_is_caught(self):
        """Found by review. `-1` is UnaryOp(USub, Constant(1)) and ast.walk
        visits the inner node, so the gate saw an allowed index and let a
        negative length through."""
        for literal, value in (("-1", -1), ("-2", -2), ("-9.625", -9.625)):
            hurt = self.src.replace('env["width"]["ft"]', literal, 1)
            tree = ast.parse(hurt)
            bad = self.offenders(tree, module_constants(tree))
            self.assertTrue(any(v == value for _, v in bad),
                            f"a pasted {literal} was not caught; offenders were {bad}")

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
        names = [n for n, _v, _l in module_constants(tree)]
        self.assertIn("WIDTH", names)                   # past the literal gate
        lines = hurt.splitlines()
        ln = next(n.lineno for n in tree.body
                  if isinstance(n, ast.Assign) and len(n.targets) == 1
                  and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "WIDTH")
        self.assertNotIn("#", lines[ln - 1])            # stopped by the comment gate


if __name__ == "__main__":
    unittest.main()
