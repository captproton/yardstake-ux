"""
cases_footprint.py — every footprint says where it sits (#119).

`dimensions.<footprint>.extent` places the page's overlay; width and depth only
size it. These cases break a placement one way each and require the refusal:

  * the barn cabin's export with main_body's extent moved a foot   must FAIL
  * Laurel's export with main_body's extent moved a foot           must FAIL
  * a published extent that runs off its building (verify_index)   must FAIL
  * a published extent whose span disagrees with its width         must FAIL
  * an extent whose axes are not [min, max]                        must FAIL
  * both exports as they are                                       must PASS
"""
from pathlib import Path

from suite import BARN, LAUREL, Case, Run, edit, index_gates, manifest, model_dir

G = "footprint"
FINISH_BARN = "finish_adu.py"
FINISH_LAUREL = "finish.py"


def _patch(work: Path, model: str, name: str, old: str, new: str, what: str) -> None:
    path = model_dir(work, model) / name
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in {name} "
                             f"exactly once (found {text.count(old)}). The case is stale.")
    path.write_text(text.replace(old, new))


def _barn_body_moved(work: Path) -> None:
    # The extent, not the size: a foot along Y, so width and depth still agree
    # with it and only the geometry can object.
    _patch(work, BARN, FINISH_BARN,
           '"extent": kit_manifest.extent_m((0.0, w), (porch, porch + body)),',
           '"extent": kit_manifest.extent_m((0.0, w), (porch + 1.0, porch + body + 1.0)),',
           "the barn cabin's main_body extent moved")


def _laurel_body_moved(work: Path) -> None:
    _patch(work, LAUREL, FINISH_LAUREL,
           '"extent": kit_manifest.extent_m((0.0, w), (0.0, d)),',
           '"extent": kit_manifest.extent_m((1.0, w + 1.0), (0.0, d)),',
           "Laurel's main_body extent moved")


def _set_extent(key, extent):
    def change(m):
        m["dimensions"][key]["extent"] = extent
    return edit(manifest, change)


CASES = [
    Case(G, "barn cabin: main_body's extent a foot off its walls fails the export",
         _barn_body_moved,
         [Run(FINISH_BARN, fails=True, blender=True, model=BARN)],
         contains="dimensions.main_body.extent.z is [-9.449, -2.134] m but Wall_N, Wall_S, Wall_W, Wall_E span [-9.144, -1.829] m"),
    Case(G, "laurel: main_body's extent a foot off its walls fails the export",
         _laurel_body_moved,
         [Run(FINISH_LAUREL, fails=True, blender=True, model=LAUREL)],
         contains="dimensions.main_body.extent.x is [0.305, 7.620] m but Wall_front, Wall_rear, Wall_x0, Wall_x24 span [0.000, 7.315] m"),
    Case(G, "a published extent that runs off its building",
         _set_extent("overall", {"x": [-0.4572, 7.1628], "z": [-9.6012, 1.4572]}),
         index_gates(),
         contains="overall's extent.z [-9.601, 1.457] m runs outside"),
    Case(G, "a published extent whose span disagrees with its width",
         _set_extent("main_body", {"x": [0.0, 7.0], "z": [-9.144, -1.8288]}),
         index_gates(),
         contains="dimensions.main_body.extent spans 7.000 m in x, but its width is 22.0 feet"),
    Case(G, "an extent whose axis is not [min, max]",
         _set_extent("main_body", {"x": [6.7056, 0.0], "z": [-9.144, -1.8288]}),
         index_gates(),
         contains="dimensions.main_body.extent.x must be [min, max], two numbers rising"),
    Case(G, "barn cabin: the export as it is places every footprint",
         None,
         [Run(FINISH_BARN, fails=False, blender=True, model=BARN)],
         contains="configurator manifest targets real materials"),
    Case(G, "laurel: the export as it is places every footprint",
         None,
         [Run(FINISH_LAUREL, fails=False, blender=True, model=LAUREL)],
         contains="[PASS] the manifest meets the page's contract"),
]
