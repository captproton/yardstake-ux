"""#120 — the option rail: `sets`, `presence` and `disclosure`, whole or
refused (verify_index.py gate 8), the disclosure limit the page and the
contract share (verify_prototype.py gate 4), and finish_adu.py reporting a
malformed spec instead of crashing (the one Blender case)."""
from pathlib import Path

from suite import (Case, Run, app_js, barn, edit, index_gates, manifest,
                   page_gates, replace)

G = "#120 rail"
CHAIR = "\U0001FA91"  # one code point, two UTF-16 units


def _variants_is_a_list(root: Path) -> None:
    """Found by review (#131): sets_block reports a malformed `variants`, but
    finish_adu.py went on to call v.get("presence") on it and raised."""
    spec = barn(root) / "spec.yaml"
    text = spec.read_bytes()
    old = b"\nvariants:\n"
    if text.count(old) != 1:
        raise AssertionError("spec.yaml no longer has exactly one top-level variants:")
    # The block moves to a spare key, so the YAML stays valid.
    spec.write_bytes(text.replace(old, b"\nvariants: [not, a, mapping]\nvariants_moved_aside:\n"))


def _disclosure_note_is_a_number(root: Path) -> None:
    spec = barn(root) / "spec.yaml"
    text = spec.read_bytes()
    old = b"    disclosure_note: >\n"
    if text.count(old) != 1:
        raise AssertionError("spec.yaml no longer has exactly one folded disclosure_note")
    # Keep the YAML valid: the folded text moves to a spare key.
    spec.write_bytes(text.replace(old, b"    disclosure_note: 123\n    disclosure_note_moved_aside: >\n"))


CASES = [
    Case(G, "an option colour with alpha 0.5",
         edit(manifest, lambda m: m["sets"][0]["options"][1].__setitem__("value", [0.5, 0.5, 0.5, 0.5])),
         index_gates(), "sets[0].options[1].value has an alpha of 0.5"),
    Case(G, "an option colour above 1",
         edit(manifest, lambda m: m["sets"][1]["options"][0].__setitem__("value", [1.2, 0.2, 0.2, 1.0])),
         index_gates(), "sets[1].options[0].value must be three or four numbers from 0 to 1"),
    Case(G, "a set that tints a texture, not a colour",
         edit(manifest, lambda m: m["sets"][2].__setitem__("property", "baseColorTexture")),
         index_gates(), "sets[2].property must be 'baseColorFactor'"),
    Case(G, "a set with no targets", edit(manifest, lambda m: m["sets"][3].__setitem__("targets", [])),
         index_gates(), "sets[3].targets must be a non-empty list of material names"),
    Case(G, "two sets with one id",
         edit(manifest, lambda m: m["sets"][4].__setitem__("id", m["sets"][3]["id"])),
         index_gates(), "repeats an earlier id"),
    Case(G, "a set with two default options",
         edit(manifest, lambda m: m["sets"][0]["options"][2].__setitem__("default", True)),
         index_gates(), "sets[0] has 2 default options"),
    Case(G, "a layout option whose show holds a number",
         edit(manifest, lambda m: m["presence"][0]["options"][1]["show"].append(7)),
         index_gates(), "presence[0].options[1].show must be a list of strings"),
    Case(G, "a layout group with no options",
         edit(manifest, lambda m: m["presence"][1].__setitem__("options", [])),
         index_gates(), "presence[1].options must be a non-empty list"),
    Case(G, "furniture with no disclosure", edit(manifest, lambda m: m.pop("disclosure")),
         index_gates(), "disclosure is required"),
    Case(G, "a disclosure with its notes appended",
         edit(manifest, lambda m: m.__setitem__("disclosure", m["disclosure"] + " " + m["disclosure_note"])),
         index_gates(), "it is copy shown verbatim, at most 200"),
    Case(G, "app.js and model_contract disagree on the disclosure limit",
         replace(app_js, ("const DISCLOSURE_MAX_CHARS = 200;", "const DISCLOSURE_MAX_CHARS = 300;")),
         page_gates(), "DISCLOSURE_MAX_CHARS differs"),
    Case(G, "150 emoji: 150 characters, 300 UTF-16 units, passes",
         edit(manifest, lambda m: m.__setitem__("disclosure", CHAIR * 150)),
         index_gates(fails=False), "all index gates pass"),
    Case(G, "201 emoji: refused",
         edit(manifest, lambda m: m.__setitem__("disclosure", CHAIR * 201)),
         index_gates(), "disclosure is 201 characters"),
    Case(G, "a disclosure_note that is a number",
         edit(manifest, lambda m: m.__setitem__("disclosure_note", 123)),
         index_gates(), "disclosure_note must be a string when present, found int"),
    Case(G, "Blender: variants as a list in the spec is reported, not a crash",
         _variants_is_a_list, [Run("finish_adu.py", fails=True, blender=True)],
         "spec.variants must be an object with `sets`, found list"),
    Case(G, "Blender: a disclosure_note of 123 in the spec is reported, not a crash",
         _disclosure_note_is_a_number, [Run("finish_adu.py", fails=True, blender=True)],
         "presence `disclosure_note` must be text, found int"),
]
