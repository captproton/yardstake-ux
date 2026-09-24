"""
adu_kit/manifest.py — the parts of a model's variants.json that know no building.

    from adu_kit import manifest

Moved out of the barn cabin's finish_adu.py for #131, when Laurel became the
second model to need them. A MOVE, not a change: the barn cabin's manifest is
byte-identical before and after.

NO BLENDER. Every function here takes the spec and the names an export
actually contains, and returns what to publish plus a list of problems. The
caller refuses to publish if the list is not empty. Nothing here raises on a
malformed spec: a crash mid-export leaves the caller guessing which key was
wrong, where a problem names it.

What stays with each model: glazing, furniture presence and the dimensions
block, because each reads that building's own spec shape.
"""
from .schema.model_contract import front_problems

VIEWS_NOTE = (
    "Visibility modes for the viewer's SHOW INTERIOR control. Each "
    "lists the glTF node names to HIDE; show everything else. Node "
    "names, not prefixes, so no string matching is needed and a mode "
    "that matches nothing fails the export instead of the page.")


def sets_block(variants, materials_present):
    """`sets`: the finishes rail. Every option is a baseColorFactor, so this
    block is the entire cost of the picker -- no extra geometry, no extra
    textures. Checked against the materials actually exported, so a typo in
    the spec fails here rather than silently doing nothing in the browser."""
    problems, sets = [], []
    for st in variants["sets"]:
        for t in st["targets"]:
            if t not in materials_present:
                problems.append(f"{st['id']} -> unknown material {t}")
        opts = [{"id": o["id"], "label": o["label"],
                 "value": list(o["value"]) + [1.0],
                 "default": bool(o.get("default"))} for o in st["options"]]
        if sum(o["default"] for o in opts) != 1:
            problems.append(f"{st['id']} needs exactly one default")
        sets.append({"id": st["id"], "label": st["label"],
                     "targets": st["targets"],
                     "property": variants.get("property", "baseColorFactor"),
                     "options": opts})
    return sets, problems


def identity_block(spec, lod0, note):
    """The manifest's `model` block, and the problems finding it.

    THE SPEC OWNS EVERY NAME. `"model": "barn_cabin_524"` was once a string
    literal in the builder, and an id is not a display name.

    WHICH AREA, NAMED RATHER THAN PICKED. `areas_declared` holds several
    numbers that mean different things. The spec names the key and the source
    string rides along, so a card that says "528 sf" can say which 528.

    WHICH END IS THE FRONT (#117), declared rather than assumed, and HELD TO
    THE FILE: the entry node must sit at that end of `lod0`, the level just
    staged. A wrong declaration is a building the page opens from behind.

    This only FINDS the records. Whether what it finds is valid is
    model_contract.identity_problems(), which the caller runs on the result,
    as build_index.py and verify_index.py do.
    """
    problems = []
    meta = spec["meta"]
    idx = meta.get("index") or {}
    area_key = idx.get("area_key")
    if not (isinstance(area_key, str) and area_key):
        problems.append("meta.index.area_key is unset; the index cannot "
                        "publish an area it was not told to publish")
        area_key_ok = False
    else:
        area_key_ok = True
    area = (spec.get("areas_declared") or {}).get(area_key) if area_key_ok else None
    if area_key_ok and area is None:
        problems.append(f"meta.index.area_key is {area_key!r}, which is not a "
                        f"key of areas_declared")
    elif area is not None and not isinstance(area, dict):
        problems.append(f"areas_declared.{area_key} must be an object with "
                        f"`value` and `source`, found {area!r}")
    area = area if isinstance(area, dict) else {}

    front = idx.get("front") if isinstance(idx.get("front"), dict) else {}
    if not isinstance(front.get("entry"), str) or not front.get("entry"):
        problems.append("meta.index.front.entry is unset; nothing can prove "
                        "the declared front is the building's front")
    else:
        problems += front_problems(lod0, front.get("glb"), front["entry"])

    model = {
        "id": meta.get("model_id"),
        "name": meta.get("display_name"),
        "area_sf": area.get("value"),
        "area_key": area_key,
        "area_source": area.get("source"),
        "storeys": idx.get("storeys"),
        "front": front.get("glb"),
        "entry_node": front.get("entry"),
        # Relative to the MODEL DIRECTORY, so the index can rebase it. Null
        # for a model with no render yet, rather than a path that 404s.
        "thumbnail": idx.get("thumbnail"),
        "note": note,
    }
    return model, problems


def views_block(display_modes, nodes_present):
    """`views`: the modes behind the page's SHOW INTERIOR control, resolved
    to node NAMES. Returns (views, problems); views is None when the modes
    cannot be resolved at all.

    REQUIRED, NOT OPTIONAL: a model's views.py reads the same block, and one
    consumer tolerant of its absence while the other is fatal is two opinions.

    RESOLVED TO NAMES, NOT SHIPPED AS PREFIXES. A runtime should not have to
    string-match its way to a roof, and a mode that matches nothing FAILS the
    export rather than shipping a button that does not move.

    A mode hides its groups' prefixes, plus any `hide_objects` it names
    exactly -- a single wall, where a prefix would take its neighbours too.
    Every named object must exist, like every prefix.
    """
    dm = display_modes
    problems = []
    if not dm or not dm.get("groups") or not dm.get("modes"):
        problems.append("spec.export.display_modes is missing or empty — "
                        "views.py requires it and the page's SHOW INTERIOR "
                        "control is built from it")
        return None, problems
    groups, views = dm["groups"], []
    # EVERY PREFIX, NOT EVERY GROUP, NOT EVERY MODE. A typo hides inside a
    # group that has other members, and views.py reads the same typo, so the
    # two consumers agree about being wrong. Each prefix must earn its place.
    for gid, prefixes in groups.items():
        dead = [x for x in prefixes
                if not any(n.startswith(x) for n in nodes_present)]
        if dead:
            problems.append(
                f"display-mode group {gid!r} has prefixes that match no "
                f"exported node: {dead}")
    ids = [m["id"] for m in dm["modes"]]
    if len(set(ids)) != len(ids):
        problems.append(f"display modes have duplicate ids: {ids}")
    if sum(bool(m.get("default")) for m in dm["modes"]) != 1:
        problems.append("display modes need exactly one default — the page "
                        "has to open on something, and on one thing")
    # A MISSPELT GROUP FAILS LIKE EVERYTHING ELSE: a readable problem, not a
    # KeyError after the levels were written.
    unknown = sorted({g for m in dm["modes"] for g in m.get("hide", [])
                      if g not in groups})
    if unknown:
        problems.append(f"display modes reference groups that do not "
                        f"exist: {unknown} (have {sorted(groups)})")
    for m in dm["modes"] if not unknown else []:
        pref = tuple(x for g in m.get("hide", []) for x in groups[g])
        named = list(m.get("hide_objects") or [])
        absent = [n for n in named if n not in nodes_present]
        if absent:
            problems.append(f"display mode {m['id']!r} hides objects that were "
                            f"not exported: {absent}")
        hide = sorted({n for n in nodes_present if n.startswith(pref)}
                      | (set(named) & set(nodes_present)))
        if (m.get("hide") or named) and not hide:
            problems.append(
                f"display mode {m['id']!r} hides nothing — its prefixes "
                f"{list(pref)} match no exported node")
        views.append({k: val for k, val in (
            ("id", m["id"]), ("label", m["label"]),
            ("desc", m.get("desc")), ("default", m.get("default")),
            ("hide", hide)) if val is not None})
    return views, problems
