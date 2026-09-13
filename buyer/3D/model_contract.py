"""
model_contract.py — what a valid model identity, index row and .glb look like.

    import model_contract

NO BLENDER, ON PURPOSE. Three programs judge the same data: `finish_adu.py`
(inside Blender) before it writes `variants.json`, `build_index.py` before it
publishes a row, and `verify_index.py` over the committed index. When each
carried its own checks they drifted into three opinions -- one tested only
that a display name was truthy, another that an id was a string, a third
nothing at all -- and every review found a malformed input one of them let
through. One module, imported by all three, is one opinion.

EVERY CHECK RETURNS PROBLEMS OR RAISES ValueError; NOTHING HERE CRASHES ON BAD
INPUT. The callers turn problems into a failed gate with a readable line. A
TypeError from a malformed file is a traceback where a gate should have been.
"""
import json
import re
import struct
from pathlib import PurePosixPath

# `lod0` is full detail and the number climbs as detail drops. Anything else
# after `<id>_` is not a level the page knows how to choose between.
LEVEL_NAME = re.compile(r"^lod\d+$")

IDENTITY_KEYS = ("id", "name", "area_sf", "area_key", "area_source", "storeys")
ROW_KEYS = IDENTITY_KEYS + ("dir", "manifest", "levels", "primary",
                            "thumbnail")


def _text(v):
    return isinstance(v, str) and v.strip() != ""


def _number(v):
    # bool is an int in Python; `area_sf: true` is not an area.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _relative(v, parent_ok):
    """A POSIX path a browser can resolve against a base URL."""
    if not _text(v) or "\\" in v:
        return False
    p = PurePosixPath(v)
    return not p.is_absolute() and (parent_ok or ".." not in p.parts)


def storeys_problems(v, where):
    if not isinstance(v, dict):
        return [f"{where} must be an object with `count` and `loft`, "
                f"found {v!r}"]
    problems = []
    count = v.get("count")
    if not (isinstance(count, int) and not isinstance(count, bool)
            and count >= 1):
        problems.append(f"{where}.count must be an integer >= 1, "
                        f"found {count!r}")
    if not isinstance(v.get("loft"), bool):
        problems.append(f"{where}.loft must be true or false, "
                        f"found {v.get('loft')!r}")
    for k in ("raw", "source"):
        if k in v and not _text(v[k]):
            problems.append(f"{where}.{k} must be a non-empty string when "
                            f"present, found {v[k]!r}")
    return problems


def _identity_fields(d, where):
    problems = []
    for k in ("id", "name", "area_key", "area_source"):
        if not _text(d.get(k)):
            problems.append(f"{where}.{k} must be a non-empty string, "
                            f"found {d.get(k)!r}")
    area = d.get("area_sf")
    if not (_number(area) and area > 0):
        problems.append(f"{where}.area_sf must be a positive number, "
                        f"found {area!r}")
    return problems + storeys_problems(d.get("storeys"), f"{where}.storeys")


def identity_problems(ident, where="model"):
    """The `model` block of a variants.json.

    `thumbnail` is optional (a model with no render yet publishes null) and,
    when present, is relative to the MODEL DIRECTORY and may not climb out of
    it -- the index rebases it, and a `..` would rebase somewhere else.
    """
    if not isinstance(ident, dict):
        return [f"{where} must be an object, found {type(ident).__name__}"]
    problems = _identity_fields(ident, where)
    thumb = ident.get("thumbnail")
    if thumb is not None and not _relative(thumb, parent_ok=False):
        problems.append(f"{where}.thumbnail must be null or a relative path "
                        f"inside the model directory, found {thumb!r}")
    if "note" in ident and not isinstance(ident["note"], str):
        problems.append(f"{where}.note must be a string when present")
    return problems


def row_problems(row, where=None):
    """One row of models.json. Paths are relative to the index, so `..` is
    expected here; what is not allowed is a row the page cannot load at
    full detail."""
    if not isinstance(row, dict):
        return [f"{where or 'row'} must be an object, "
                f"found {type(row).__name__}"]
    where = where or f"row {row.get('id')!r}"
    problems = [f"{where} is missing `{k}`" for k in ROW_KEYS if k not in row]
    problems += _identity_fields(row, where)
    for k in ("dir", "manifest"):
        if not _relative(row.get(k), parent_ok=True):
            problems.append(f"{where}.{k} must be a relative path, "
                            f"found {row.get(k)!r}")
    for k in ("primary", "thumbnail"):
        v = row.get(k)
        if v is not None and not _relative(v, parent_ok=True):
            problems.append(f"{where}.{k} must be null or a relative path, "
                            f"found {v!r}")
    levels = row.get("levels")
    if not isinstance(levels, dict):
        problems.append(f"{where}.levels must be an object, found {levels!r}")
        levels = {}
    for name, path in levels.items():
        if not LEVEL_NAME.match(name):
            problems.append(f"{where}.levels has an unknown level {name!r}")
        if not _relative(path, parent_ok=True):
            problems.append(f"{where}.levels.{name} must be a relative path, "
                            f"found {path!r}")
    if "lod0" not in levels and row.get("primary") is None:
        problems.append(f"{where} has neither `levels.lod0` nor `primary`; "
                        f"the page has no full-detail file to load")
    return problems


def glb_json(path):
    """The JSON chunk of a binary glTF, as an object. Raises ValueError."""
    b = path.read_bytes()
    if len(b) < 20 or b[:4] != b"glTF":
        raise ValueError("not a binary glTF (no glTF magic)")
    length, kind = struct.unpack("<I4s", b[12:20])
    if kind != b"JSON" or 20 + length > len(b):
        raise ValueError("first chunk is not a complete JSON chunk")
    try:
        g = json.loads(b[20:20 + length])
    except ValueError as e:  # includes UnicodeDecodeError
        raise ValueError(f"JSON chunk does not parse: {e}")
    if not isinstance(g, dict):
        raise ValueError(f"JSON chunk root is a {type(g).__name__}, "
                         f"not an object")
    return g


def glb_names(path):
    """(material names, node names) of a .glb. Raises ValueError."""
    g = glb_json(path)
    out = []
    for key in ("materials", "nodes"):
        items = g.get(key, [])
        if not isinstance(items, list) or not all(isinstance(x, dict)
                                                  for x in items):
            raise ValueError(f"`{key}` is not a list of objects")
        out.append({x.get("name") for x in items})
    return tuple(out)


def manifest_names(manifest):
    """(material targets, node names) a variants.json asks the page to touch:
    the materials its `sets` tint, and the nodes its `presence` options show
    and its `views` modes hide. Raises ValueError on a manifest whose blocks
    have the wrong shape, rather than a TypeError from iterating one."""
    def objects(v, where):
        if not isinstance(v, list) or not all(isinstance(x, dict) for x in v):
            raise ValueError(f"`{where}` is not a list of objects")
        return v

    def strings(v, where):
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise ValueError(f"`{where}` is not a list of strings")
        return v

    if not isinstance(manifest, dict):
        raise ValueError(f"root is a {type(manifest).__name__}, not an object")
    mats = {t for st in objects(manifest.get("sets", []), "sets")
            for t in strings(st.get("targets", []), "sets[].targets")}
    nodes = set()
    for st in objects(manifest.get("presence", []), "presence"):
        for o in objects(st.get("options", []), "presence[].options"):
            for key in ("show", "hide"):
                nodes.update(strings(o.get(key, []),
                                     f"presence[].options[].{key}"))
    # A view mode that hides a node the file lacks hides nothing, silently.
    for v in objects(manifest.get("views", []), "views"):
        nodes.update(strings(v.get("hide", []), "views[].hide"))
    return mats, nodes


# ── the two blocks the page renders controls from (#108) ─────────────────────
# WHOLE OR NOT AT ALL. The page refuses a `views` or `dimensions` block that is
# malformed anywhere rather than acting on the entries that parse, so these
# report every problem in a block, and any problem means the block is refused.
# An absent block (None) is fine: a model need not describe what it lacks.
# The rules mirror viewsProblem() and dimensionsProblem() in prototype/app.js.

# Keep in step with UNITS in prototype/app.js -- verify_prototype.py gate 4
# fails if they differ, since a unit only one side knows is a manifest one side
# passes and the other refuses.
DIMENSION_UNITS = ("feet", "foot", "ft", "metres", "meters", "m")
DIMENSION_FIELDS = ("units", "note", "height_to_ridge")


def views_problems(views, where="views"):
    if views is None:
        return []
    if not isinstance(views, list):
        return [f"{where} must be a list, found {type(views).__name__}"]
    problems, ids, defaults = [], set(), 0
    for i, v in enumerate(views):
        at = f"{where}[{i}]"
        if not isinstance(v, dict):
            problems.append(f"{at} must be an object")
            continue
        if not _text(v.get("id")):
            problems.append(f"{at}.id must be a non-empty string, found {v.get('id')!r}")
        elif v["id"] in ids:
            problems.append(f"{at}.id {v['id']!r} repeats an earlier id")
        else:
            ids.add(v["id"])
        if not _text(v.get("label")):
            problems.append(f"{at}.label must be a non-empty string, found {v.get('label')!r}")
        if "desc" in v and not isinstance(v["desc"], str):
            problems.append(f"{at}.desc must be a string when present")
        if "default" in v and not isinstance(v["default"], bool):
            problems.append(f"{at}.default must be true or false when present")
        if v.get("default") is True:
            defaults += 1
        hide = v.get("hide")
        if not isinstance(hide, list) or not all(isinstance(n, str) for n in hide):
            problems.append(f"{at}.hide must be a list of strings")
    if defaults > 1:
        problems.append(f"{where} has {defaults} defaults; at most one")
    return problems


def dimensions_problems(dims, where="dimensions"):
    if dims is None:
        return []
    if not isinstance(dims, dict):
        return [f"{where} must be an object, found {type(dims).__name__}"]
    problems = []
    units = dims.get("units")
    if not isinstance(units, str) or units.lower() not in DIMENSION_UNITS:
        problems.append(f"{where}.units must be one of {list(DIMENSION_UNITS)}, "
                        f"found {units!r}")
    if "note" in dims and not isinstance(dims["note"], str):
        problems.append(f"{where}.note must be a string when present")
    if "height_to_ridge" in dims and not (
            _number(dims["height_to_ridge"]) and dims["height_to_ridge"] > 0):
        problems.append(f"{where}.height_to_ridge must be a positive number, "
                        f"found {dims['height_to_ridge']!r}")
    footprints = 0
    for key, v in dims.items():
        if key in DIMENSION_FIELDS:
            continue
        if not isinstance(v, dict):
            problems.append(f"{where}.{key} is neither a footprint object nor "
                            f"one of {list(DIMENSION_FIELDS)}")
            continue
        footprints += 1
        for f in ("width", "depth"):
            if not (_number(v.get(f)) and v.get(f) > 0):
                problems.append(f"{where}.{key}.{f} must be a positive number, "
                                f"found {v.get(f)!r}")
        if "note" in v and not isinstance(v["note"], str):
            problems.append(f"{where}.{key}.note must be a string when present")
    if not footprints:
        problems.append(f"{where} has no footprint")
    return problems


def display_problems(manifest):
    """Every problem in a manifest's `views` and `dimensions` blocks."""
    if not isinstance(manifest, dict):
        return [f"manifest must be an object, found {type(manifest).__name__}"]
    return (views_problems(manifest.get("views"))
            + dimensions_problems(manifest.get("dimensions")))
