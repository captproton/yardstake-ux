"""
finish_adu.py — P4. Materials, glazing, LODs, Draco-compressed glTF.

Builds the model from spec.yaml via build_adu.build(), applies the material
library and assignment map from spec.yaml (no colours hardcoded here), fills the
openings with glazing and door panels, then exports three LOD levels as .glb
with Draco mesh compression for the Three.js track.

    blender --background --python finish_adu.py -- [--out DIR]

Scene is authored at 1 Blender unit = 1 foot, and the export is in metres per
glTF convention.

Setting `scene.unit_settings.scale_length` does NOT achieve that: the glTF
exporter ignores it and writes raw Blender units. `to_metres()` scales the mesh
data explicitly instead, and that is what makes the export correct. This
docstring used to credit scale_length for it, contradicting both the code and
`to_metres()`'s own docstring a hundred lines below. scale_length is still set,
because it makes Blender's own UI read in feet, but it is not load-bearing.
"""
import sys
import json
import struct
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import (load_spec, build, box, multibox, collection,  # noqa: E402
                       ft)

FOOT_M = 0.3048


# ---------------------------------------------------------------------------
def make_materials(spec, textured=True):
    lib = spec["materials"]["library"]
    tdir = HERE / spec.get("textures", {}).get("dir", "textures/")
    out = {}
    for name, m in lib.items():
        mat = bpy.data.materials.new(f"adu_{name}")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        r, g, b = m["base_color_linear"]
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)

        # Textures, where the spec declares them. A base-colour map carries the
        # colour itself, so the factor is left white and not double-tinted.
        maps = (m.get("maps") or {}) if textured else {}
        for slot, fname in maps.items():
            path = tdir / fname
            if not path.exists():
                raise SystemExit(f"[tex] missing {path}")
            img = bpy.data.images.load(str(path), check_existing=True)
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            tex.location = (-600, {"base_color": 300, "normal": -300,
                                   "roughness": 0}.get(slot, 0))
            if slot == "base_color":
                img.colorspace_settings.name = "sRGB"
                if m.get("neutral_albedo"):
                    # The map carries luminance only; the colour stays on the
                    # factor so a configurator can swap it without new textures.
                    mix = nt.nodes.new("ShaderNodeMixRGB")
                    mix.blend_type = "MULTIPLY"
                    mix.location = (-300, 300)
                    mix.inputs["Fac"].default_value = 1.0
                    mix.inputs["Color2"].default_value = (r, g, b, 1.0)
                    nt.links.new(tex.outputs["Color"], mix.inputs["Color1"])
                    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
                else:
                    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
                    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
            elif slot == "normal":
                img.colorspace_settings.name = "Non-Color"
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.location = (-300, -300)
                nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
            elif slot == "roughness":
                img.colorspace_settings.name = "Non-Color"
                nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])
        bsdf.inputs["Roughness"].default_value = m.get("roughness", 0.8)
        bsdf.inputs["Metallic"].default_value = m.get("metallic", 0.0)
        if m.get("emissive_linear"):
            # The look of a lit lamp. Blender's glTF exporter turns Emission
            # into emissiveFactor, and a strength above 1 into
            # KHR_materials_emissive_strength — so day/night at runtime is the
            # same kind of swap the colour variants already do, on a different
            # property. No KHR_lights_punctual is written and none is wanted:
            # see materials.lamp_glow.
            # Socket name moved between Blender versions the same way
            # Transmission did below — "Emission" in 3.x, "Emission Color" in
            # 4.x and later. Probe rather than assume, so this does not become
            # a silent no-emission material on an LTS build.
            er, eg, eb = m["emissive_linear"]
            for key in ("Emission Color", "Emission"):
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = (er, eg, eb, 1.0)
                    break
            else:
                raise SystemExit(f"[mat] {name}: no emission colour socket on "
                                 "Principled BSDF; emissive_linear cannot be applied")
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = m.get(
                    "emissive_strength", 1.0)
        if m.get("transmission"):
            for key in ("Transmission Weight", "Transmission"):
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = m["transmission"]
                    break
            mat.blend_method = "BLEND"
        out[name] = mat
    return out


def default_furniture(spec, coll):
    """Only the arrangements flagged `default`, one per room.

    All of them are BUILT -- the presence-swap work can only toggle what
    already exists -- but two of them share the bedroom floor and are
    alternatives, so exporting both puts a desk through a bed. Until switching
    exists there is nothing to do the choosing, and this flag is the choice.
    """
    fx = spec["fixtures"]["furniture"]["arrangements"]
    wanted = tuple(f"Furn_{a['id']}_" for a in fx if a.get("default"))
    return [o for o in coll.objects if o.name.startswith(wanted)]


def assign(spec, mats):
    """Apply spec.materials.assignment by object-name prefix. First match wins."""
    rules = list(spec["materials"]["assignment"].items())
    unmatched = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for prefix, mname in rules:
            if ob.name.startswith(prefix):
                # materials.clear() RESETS every polygon's material_index to 0,
                # which silently discarded the reveal tagging from
                # build_adu.mark_reveals(). Capture the indices first and put
                # them back once both slots exist.
                # slot 1 = trim (reveals), slot 2 = drywall (inward face)
                EXTRA = {1: "trim", 2: "drywall"}
                tagged = {i: poly.material_index
                          for i, poly in enumerate(ob.data.polygons)
                          if poly.material_index in EXTRA}
                ob.data.materials.clear()
                ob.data.materials.append(mats[mname])
                if tagged:
                    for slot in sorted(EXTRA):
                        ob.data.materials.append(mats[EXTRA[slot]])
                    for i, slot in tagged.items():
                        ob.data.polygons[i].material_index = slot
                break
        else:
            unmatched.append(ob.name)
    return unmatched


# ---------------------------------------------------------------------------
def add_glazing(spec, geo, coll):
    """A thin slab in each opening: glass for windows, a trim panel for doors."""
    t, W = geo["t"], geo["W"]
    NY, SY = geo["NY"], geo["SY"]
    loft_sf = spec["levels"]["loft_top_of_subfloor"]["ft"]
    dsill = loft_sf + spec["construction"]["dormer_window_sill_above_loft_floor"]["ft"]
    op = spec["openings"]["main_floor"]
    d = 0.04                      # pane thickness, ft
    made = []

    def pane(name, x0, x1, y0, y1, z0, z1):
        made.append(box(name, x0, x1, y0, y1, z0, z1, coll))

    def yn(v):
        return NY - v

    for o in op["north_wall"]["openings"]:
        c = NY - t / 2
        pane(f"Glazing_{o['id']}", o["offset"], o["offset"] + o["w"],
             c - d / 2, c + d / 2, o["sill"], o["sill"] + o["h"])
    for o in op["south_wall"]["openings"]:
        c = SY + t / 2
        if o["type"].startswith("half_lite"):
            # A HALF-LITE DOOR GETS SIX PANES, NOT ONE SHEET.
            #
            # This line used to read
            #     nm = ("Door_" if o["type"].endswith("door") else "Glazing_") ...
            # which built a full-height pane and then renamed it so the material
            # map would make it opaque. Same geometry, same footprint; only the
            # NAME differed, and the name is what picks the material. So the
            # entry door had a working glazing slot that a single ternary
            # deliberately blanked, and the model shipped a door that was two
            # flat boxes.
            #
            # Replacing it with one pane would have been the other wrong answer:
            # a single sheet across the upper half is a windscreen, not the door
            # A1.1 draws. The lites are placed in the grid the leaf leaves open.
            #
            # The discriminator is the DECLARED TYPE. Keying on whether a
            # `construction` block exists would make the glazing follow the
            # metadata's shape instead of the opening's identity -- the same
            # mistake as the ternary above, one level quieter. build_adu.py
            # raises on a half-lite typed without one, so by here it exists.
            cn = o["construction"]
            st, mw = cn["stile"]["ft"], cn["muntin_width"]["ft"]
            gx0, gx1 = o["offset"] + st, o["offset"] + o["w"] - st
            gz0 = o["sill"] + cn["lite_grid"]["bottom_z"]
            gz1 = o["sill"] + cn["lite_grid"]["top_z"]
            cols, rows = cn["lites"]["cols"], cn["lites"]["rows"]
            lites = []
            for i in range(cols):
                for j in range(rows):
                    a = gx0 + (gx1 - gx0) * i / cols
                    b = gx0 + (gx1 - gx0) * (i + 1) / cols
                    p = gz0 + (gz1 - gz0) * j / rows
                    q = gz0 + (gz1 - gz0) * (j + 1) / rows
                    # Inset by half a muntin, so a lite meets its bar rather
                    # than overlapping it.
                    lites.append((
                        a + (mw / 2 if i else 0), b - (mw / 2 if i < cols - 1 else 0),
                        c - d / 2, c + d / 2,
                        p + (mw / 2 if j else 0), q - (mw / 2 if j < rows - 1 else 0)))
            # ONE mesh, not six. They share a material, they never toggle
            # apart, and six objects is six draw calls for one door.
            #
            # This does mean the lite COUNT can no longer be read off the
            # object list. That is a good thing: counting names was always the
            # weaker test, and the gate now samples the six lite centres and
            # the muntins between them instead. Position, not naming.
            made.append(multibox(f"Glazing_{o['id']}_lites", lites, coll))
            continue
        nm = ("Door_" if o["type"].endswith("door") else "Glazing_") + o["id"]
        pane(nm, o["offset"], o["offset"] + o["w"],
             c - d / 2, c + d / 2, o["sill"], o["sill"] + o["h"])
    for o in op["west_wall"]["openings"]:
        c = t / 2
        pane(f"Glazing_{o['id']}", c - d / 2, c + d / 2,
             yn(o["offset"] + o["w"]), yn(o["offset"]),
             o["sill"], o["sill"] + o["h"])
    # The south gable window sits in a prism, not a wall, so its pane is placed
    # from the gable's own depth (y 0..t) rather than from a wall datum.
    for o in spec["openings"]["loft"]["south_gable"]["windows"]:
        c = t / 2
        pane(f"Glazing_{o['id']}", o["offset"], o["offset"] + o["w"],
             c - d / 2, c + d / 2, o["sill"], o["sill"] + o["h"])
    for o in spec["openings"]["loft"]["windows"]:
        for side, c in (("W", t / 2), ("E", W - t / 2)):
            pane(f"Glazing_{o['id']}_{side}", c - d / 2, c + d / 2,
                 yn(o["offset"] + o["w"]), yn(o["offset"]),
                 dsill, dsill + o["h"])
    return made


# ---------------------------------------------------------------------------
def to_metres(objects):
    """The glTF exporter writes raw Blender units as metres and ignores
    scene.unit_settings.scale_length, so convert the mesh data explicitly.
    The scene is authored at 1 unit = 1 foot."""
    done = set()
    for ob in objects:
        if ob.data.name in done:
            continue
        done.add(ob.data.name)
        for v in ob.data.vertices:
            v.co *= FOOT_M


def export_glb(path, objects, draco=True):
    to_metres(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    kw = dict(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_materials="EXPORT",
    )
    if draco:
        kw.update(
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=6,
            export_draco_position_quantization=14,
            export_draco_normal_quantization=10,
        )
    bpy.ops.export_scene.gltf(**kw)


def patch_base_color_factors(path, spec):
    """Write baseColorFactor for the neutral-albedo materials.

    Blender's exporter does not recognise a multiply node feeding Base Color,
    so it emits baseColorTexture with no factor — which would ship the model
    untinted, since those maps carry luminance only. Two node types were tried
    before settling on patching the file, which is deterministic and does not
    depend on the exporter matching a graph pattern.
    """
    lib = spec["materials"]["library"]
    raw = path.read_bytes()
    assert raw[:4] == b"glTF"
    chunks, off = [], 12
    while off < len(raw):
        clen, ctype = struct.unpack_from("<II", raw, off)
        chunks.append([ctype, raw[off + 8: off + 8 + clen]])
        off += 8 + clen
    n = 0
    for c in chunks:
        if c[0] != 0x4E4F534A:
            continue
        js = json.loads(c[1].decode("utf-8"))
        for m in js.get("materials", []):
            # removeprefix, NOT replace: replace() strips "adu_" anywhere in the
            # name, so a material called "adu_wall_adu_trim" would map to the
            # wrong spec key. Unnamed materials are skipped rather than raising.
            name = m.get("name")
            if not name:
                continue
            key = name[4:] if name.startswith("adu_") else name
            spec_m = lib.get(key, {})
            if not spec_m.get("neutral_albedo"):
                continue
            r, g, b = spec_m["base_color_linear"]
            m.setdefault("pbrMetallicRoughness", {})["baseColorFactor"] = [r, g, b, 1.0]
            n += 1
        blob = json.dumps(js, separators=(",", ":")).encode("utf-8")
        blob += b" " * ((4 - len(blob) % 4) % 4)          # pad with spaces
        c[1] = blob
    body = b"".join(struct.pack("<II", len(c[1]), c[0]) + c[1] for c in chunks)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
    return n


def arrangement_nodes(spec, arr_id):
    """The object names build_furniture creates for one arrangement.

    Derived the same way the builder derives them -- one mesh per
    (arrangement, material) -- so the manifest cannot name a node the build
    does not make. A gate then checks these against what lod0 actually
    exported, which is the analogue of "manifest targets real materials".
    """
    for a in spec["fixtures"]["furniture"]["arrangements"]:
        if a["id"] == arr_id:
            mats = sorted({pc["material"] for pc in a["pieces"]})
            return [f"Furn_{arr_id}_{m.removeprefix('furn_')}" for m in mats]
    return None


def emit_variants(out, spec, materials_present, nodes_present=frozenset()):
    """Write the configurator manifest the Three.js runtime reads.

    Every option is a baseColorFactor, so this file is the entire cost of the
    finishes picker — no extra geometry, no extra textures. Validated against
    the materials actually exported, so a typo in the spec fails here rather
    than silently doing nothing in the browser.
    """
    v = spec.get("variants")
    if not v:
        return None, []
    problems = []
    sets = []
    for st in v["sets"]:
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
                     "property": v.get("property", "baseColorFactor"),
                     "options": opts})
    # ---- presence: a SIBLING of sets, never an overload of it -------------
    pres_spec = v.get("presence")
    presence = []
    if pres_spec:
        for st in pres_spec["sets"]:
            opts = []
            for o in st["options"]:
                arr = o.get("arrangement")
                if arr is None:                       # the "unfurnished" option
                    show = []
                else:
                    show = arrangement_nodes(spec, arr)
                    if show is None:
                        problems.append(
                            f"{st['id']}.{o['id']} -> unknown arrangement {arr}")
                        show = []
                    else:
                        missing = [n for n in show if n not in nodes_present]
                        if missing:
                            problems.append(
                                f"{st['id']}.{o['id']} -> nodes not exported: "
                                f"{missing}")
                opts.append({"id": o["id"], "label": o["label"],
                             "show": show, "default": bool(o.get("default"))})
            if sum(o["default"] for o in opts) != 1:
                problems.append(f"{st['id']} needs exactly one default")
            presence.append({"id": st["id"], "label": st["label"],
                             "room": st["room"],
                             "property": pres_spec.get("property", "visible"),
                             "options": opts})

        # Every node named anywhere in presence must be hidden unless some
        # option shows it. A runtime that ignores `presence` would otherwise
        # render two bedroom arrangements through each other.
        owned = sorted({n for st in presence for o in st["options"]
                        for n in o["show"]})
        stray = sorted(n for n in nodes_present
                       if n.startswith("Furn_") and n not in owned)
        if stray:
            problems.append(f"furniture nodes no presence set controls: {stray}")

    manifest = {
        "model": "barn_cabin_524",
        "note": ("Runtime material swaps. Each option sets baseColorFactor on the "
                 "named materials; the albedo maps are neutral, so no textures "
                 "need loading and none ship per option."),
        "sets": sets,
    }
    if presence:
        manifest["presence"] = presence
        manifest["presence_note"] = (
            "Visibility swaps, and a SEPARATE mechanism from `sets`. Each option "
            "lists the glTF node names to show; every other node named anywhere "
            "in this block must be hidden. THE MODEL SHIPS ALL ARRANGEMENTS, so "
            "a runtime that ignores this block renders a bed and a desk through "
            "each other -- honour `default` on first load.")
        # A missing or blank disclosure is a validation problem, not a
        # KeyError: everything else here reports through `problems` and gets a
        # readable gate line, and a crash mid-export would leave the caller
        # guessing which of the manifest's many keys was wrong.
        disc = (pres_spec.get("disclosure") or "").strip()
        if disc:
            manifest["disclosure"] = disc
        else:
            problems.append(
                "presence block has no `disclosure` text — the UI obligation "
                "is the reason presence exists, so it may not be dropped")
    path = out / v.get("emit", "variants.json")
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path, problems


def glb_info(path):
    """Read a GLB's JSON chunk: extension use, mesh/accessor counts, bbox."""
    raw = path.read_bytes()
    assert raw[:4] == b"glTF", "not a GLB"
    off, n = 12, len(raw)
    js = None
    while off < n:
        clen, ctype = struct.unpack_from("<II", raw, off)
        if ctype == 0x4E4F534A:
            js = json.loads(raw[off + 8: off + 8 + clen].decode("utf-8"))
            break
        off += 8 + clen
    # POSITION accessors only — NORMAL is also VEC3 and would inflate the bbox
    pos_idx = {prim["attributes"]["POSITION"]
               for m in js.get("meshes", []) for prim in m["primitives"]
               if "POSITION" in prim.get("attributes", {})}
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for i_a, a in enumerate(js.get("accessors", [])):
        if i_a in pos_idx and "min" in a and len(a["min"]) == 3:
            for i in range(3):
                lo[i] = min(lo[i], a["min"][i])
                hi[i] = max(hi[i], a["max"][i])
    return dict(
        size_kb=len(raw) / 1024.0,
        meshes=len(js.get("meshes", [])),
        materials=len(js.get("materials", [])),
        extensions=js.get("extensionsUsed", []),
        bbox=[round(hi[i] - lo[i], 3) for i in range(3)],
    )


# ---------------------------------------------------------------------------
def save_viewable_blend(spec, dest):
    """Save a textured lod0 as a .blend you can actually open and look at.

    build_adu.py saves the geometry, but the materials and textures are made
    here and were only ever exported, never saved -- so opening
    barn_cabin_524.blend showed a grey model and looked like the texturing had
    failed. It had not; there was simply nothing to see.

    This cannot reuse whatever is in memory at the end of main(): the export
    loop rebuilds the scene per level and finishes on lod2, which is flat and
    has no openings cut. So rebuild lod0 explicitly.

    .blend is gitignored, so this is a local convenience and costs the repo
    nothing. Image paths are made relative, or the file only opens on the
    machine that wrote it.
    """
    geo, colls = build(spec, cut_openings=True)
    bpy.context.scene.unit_settings.scale_length = FOOT_M
    mats = make_materials(spec, textured=True)
    add_glazing(spec, geo, collection("Glazing"))
    assign(spec, mats)

    # Non-default arrangements are BUILT but hidden, so this file shows what
    # lod0 actually ships. Two arrangements share the bedroom floor and are
    # alternatives; without this, opening the .blend shows a desk growing
    # through a bed and looks like a placement bug. They stay in the file so
    # the presence-swap work has something to switch, and so views.py can
    # reveal them.
    keep = {o.name for o in default_furniture(spec, colls["furniture"])}
    for ob in colls["furniture"].objects:
        hidden = ob.name not in keep
        ob.hide_set(hidden)
        ob.hide_render = hidden

    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    return dest


def lod2_contract_nodes(spec):
    """The declared lod2 node list, or None if the spec declares none.

    lod2 is the placement developer's handoff. The plan has said for twelve
    PRs that it must not change without a conversation -- and #98 changed it
    anyway, by welding three objects that happened to live in the `shell` and
    `roof` collections lod2 keeps. Nothing failed, because the guarantee was
    written in a document and checked by nobody.

    Geometry is not the thing at risk -- welding preserves every vertex -- the
    INTERFACE is: how many nodes, and the names they address objects by.

    `(spec.get("export") or {})` rather than `spec.get("export", {})`: the
    default only fires on a MISSING key, and deleting the contract block
    leaves `export:` present and null.
    """
    contract = (spec.get("export") or {}).get("lod2_contract") or {}
    return sorted(contract.get("nodes") or []) or None


def report_lod2_contract(want, got):
    """Print the verdict. True only if the contract is satisfied.

    FAILS CLOSED, and that is the whole point. A guard of the form
    `if contract:` would make deleting the spec block a silent way to switch
    off the only enforcement the handoff has -- the same shape of mistake #98
    made, one level up. No contract is not "nothing to check"; it is the
    check missing.
    """
    if not want:
        print("lod2 CONTRACT MISSING - spec.export.lod2_contract declares no nodes.")
        print("    This gate is the only thing holding the placement developer's"
              " handoff. Absent, it fails.")
        return False
    if got is None:
        print("lod2 CONTRACT UNCHECKABLE - lod2 was never exported, so the"
              " contract could not be compared.")
        return False
    if sorted(got) == want:
        print(f"lod2 contract: {len(want)} nodes, unchanged")
        return True
    print("lod2 CONTRACT BROKEN - this is the placement developer's file")
    for n in sorted(set(want) - set(got)):
        print(f"    GONE: {n}")
    for n in sorted(set(got) - set(want)):
        print(f"     NEW: {n}")
    print("    If this change is intended, it is a CONVERSATION first,"
          " then spec.export.lod2_contract, then the commit.")
    return False


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else HERE / "export"
    out.mkdir(parents=True, exist_ok=True)

    spec = load_spec(HERE / "spec.yaml")
    results = {}
    lod0_nodes = set()
    lod2_nodes = None

    # Checked BEFORE the first export, so a build with no contract writes no
    # artefacts at all rather than publishing first and complaining after.
    want2 = lod2_contract_nodes(spec)
    if not want2:
        report_lod2_contract(want2, None)
        print("\nnothing exported: the lod2 contract is the precondition,"
              " not a post-check.")
        raise SystemExit(1)

    for lod in ("lod0", "lod1", "lod2"):
        geo, colls = build(spec, cut_openings=(lod != "lod2"))
        bpy.context.scene.unit_settings.scale_length = FOOT_M

        tex_cfg = spec.get("textures", {})
        textured = lod not in tex_cfg.get("untextured_levels", [])
        mats = make_materials(spec, textured=textured)
        glaz = colls["shell"] if lod == "lod2" else collection("Glazing")
        if lod != "lod2":
            add_glazing(spec, geo, glaz)
        unmatched = assign(spec, mats)

        keep = list(colls["shell"].objects) + list(colls["roof"].objects) \
            + list(colls["porch"].objects)
        if lod == "lod0":
            keep += list(colls["interior"].objects)
            keep += list(colls["finish"].objects)   # Tier 1: ceilings, floors, doors
            keep += list(colls["casework"].objects)  # Tier 3: cabinets, counter
            keep += list(colls["foundation"].objects)  # footing, crawl grade, vents
            # ALL arrangements, not just the defaults. A runtime can only
            # toggle what is in the file, so presence swapping requires every
            # arrangement to ship. `default` in the manifest now carries what
            # this filter used to: which arrangement is visible on first load.
            # The viewable .blend still hides the rest, because nothing is
            # doing the choosing when a person opens it in Blender.
            keep += list(colls["furniture"].objects)
            keep += list(colls["lighting"].objects)  # Tier 3: exterior sconce
        if lod != "lod2":
            keep += [o for o in glaz.objects]

        p = out / f"barn_cabin_524_{lod}.glb"

        # BEFORE the write, not after. The gate used to run down at the report,
        # by which time barn_cabin_524_lod2.glb -- the handoff file itself --
        # had already been overwritten with the very node list the gate
        # rejects, and the primary .glb copied beside it. A consumer picking
        # those up between runs would get exactly the artefact the build said
        # no to. Checked here, a broken contract leaves the last good lod2
        # where it was.
        if lod == "lod2":
            lod2_nodes = sorted(o.name for o in keep)
            print("-" * 76)
            if not report_lod2_contract(want2, lod2_nodes):
                print("\nlod2 NOT written, and neither is the primary .glb:"
                      " the files on disk are still the last ones that passed.")
                raise SystemExit(1)

        export_glb(p, keep)
        if textured:
            patch_base_color_factors(p, spec)
        info = glb_info(p)
        info["objects"] = len(keep)
        info["unmatched_materials"] = unmatched
        info["textured"] = textured
        results[lod] = info
        if lod == "lod0":
            lod0_nodes = {o.name for o in keep}

    all_mats = sorted(m.name for m in bpy.data.materials)
    vpath, vproblems = emit_variants(out, spec, set(all_mats), lod0_nodes)

    # primary deliverable is a copy of lod0
    (out / "barn_cabin_524.glb").write_bytes((out / "barn_cabin_524_lod0.glb").read_bytes())

    print("\n" + "=" * 76)
    print("P4 EXPORT REPORT")
    print("=" * 76)
    print(f"{'level':7} {'objects':>8} {'meshes':>7} {'mats':>5} {'size KB':>9}  "
          f"{'bbox (m)':>22}  draco")
    print("-" * 76)
    ok = True
    for lod, i in results.items():
        draco = "KHR_draco_mesh_compression" in i["extensions"]
        ok &= draco
        bb = "x".join(f"{v:.2f}" for v in i["bbox"])
        print(f"{lod:7} {i['objects']:>8} {i['meshes']:>7} {i['materials']:>5} "
              f"{i['size_kb']:>9.1f}  {bb:>22}  {'yes' if draco else 'NO'}"
              f"  {'tex' if i['textured'] else 'flat'}")
        if i["unmatched_materials"]:
            print(f"        unmatched: {i['unmatched_materials']}")
            ok = False

    budget = spec.get("textures", {}).get("budget_kb", {})
    over = [f"{k} {results[k]['size_kb']:.0f} KB > {v} KB"
            for k, v in budget.items() if results[k]["size_kb"] > v]
    print("-" * 76)
    for k, v in budget.items():
        print(f"  budget {k}: {results[k]['size_kb']:8.1f} KB / {v:5d} KB ceiling"
              f"   {'OK' if results[k]['size_kb'] <= v else 'OVER'}")
    ok &= not over

    # ---- lod2 is a PROMISE, and until now it was only prose ---------------
    # lod2 is the placement developer's handoff. The plan has said for twelve
    # PRs that it must not change without a conversation -- and #98 changed it
    # anyway, by welding three objects that happened to live in the `shell`
    # and `roof` collections lod2 keeps. Nothing failed, because the guarantee
    # was written in a document and checked by nobody.
    #
    # The contract is now DECLARED in spec.export.lod2_contract and compared
    # against what was actually exported. Geometry is not the thing at risk --
    # welding preserves every vertex -- the INTERFACE is: node count and the
    # names they address objects by.
    # Already enforced above, before anything was written. Repeated here so
    # the report says so, and so an edited LOD tuple that never reaches lod2
    # is caught rather than passing by omission.
    print("-" * 76)
    ok &= report_lod2_contract(want2, lod2_nodes)

    W = spec["envelope"]["main_body_width"]["ft"]
    exp_x = (W + 2 * spec["roof"]["eave_overhang"]["ft"]) * FOOT_M
    got_x = results["lod0"]["bbox"][0]
    print("-" * 76)
    print(f"expected X span (22'-0\" + 2 x 18\" eave) = {exp_x:.3f} m   got {got_x:.3f} m")
    scale_ok = abs(got_x - exp_x) < 0.01
    if vpath:
        nsets = len(spec["variants"]["sets"])
        nopts = sum(len(x["options"]) for x in spec["variants"]["sets"])
        print(f"\nconfigurator manifest: {vpath.name} — {nsets} sets, {nopts} options, "
              f"{vpath.stat().st_size} bytes, 0 extra texture bytes")
        for p_ in vproblems:
            print(f"  PROBLEM: {p_}")
        ok &= not vproblems

    # ---- presence: every shipped furniture node is controlled -------------
    # The manifest is read back from disk, not from the objects that wrote it,
    # so this checks the artefact the runtime will actually load.
    man = json.loads(vpath.read_text()) if vpath else {}
    pres = man.get("presence", [])
    shipped = {n for n in lod0_nodes if n.startswith("Furn_")}
    owned = [n for st in pres for o in st["options"] for n in o["show"]]
    uncontrolled = sorted(shipped - set(owned))
    twice = sorted({n for n in owned if owned.count(n) > 1})
    one_default = all(sum(o["default"] for o in st["options"]) == 1 for st in pres)
    pres_ok = pres and not uncontrolled and not twice and one_default

    print(f"\n  [{'PASS' if not vproblems else 'FAIL'}] configurator manifest targets real materials")
    print(f"  [{'PASS' if pres_ok else 'FAIL'}] every shipped furniture node is controlled "
          f"by exactly one presence option"
          + (f" — UNCONTROLLED {uncontrolled}" if uncontrolled else "")
          + (f" — CLAIMED TWICE {twice}" if twice else "")
          + (" — a set lacks exactly one default" if pres and not one_default else "")
          + ("" if pres else " — no presence block emitted"))
    ok &= bool(pres_ok)
    print(f"  [{'PASS' if not over else 'FAIL'}] every level within its size budget")
    print(f"  [{'PASS' if scale_ok else 'FAIL'}] glTF exported in metres at the right scale")
    print(f"  [{'PASS' if ok else 'FAIL'}] Draco applied and every object matched a material")
    print("=" * 76)

    # Only write the viewable .blend if the export actually passed. The file
    # carries no indication of validity, so writing it after a failure invites
    # someone to open a model that failed its gates believing it is good —
    # silent wrongness, which is worse than the inconvenience of not having it.
    # (For inspecting a failing build, run build_adu.py and open
    # barn_cabin_524.blend; it has the geometry, just not the materials.)
    if ok and scale_ok:
        blend = save_viewable_blend(spec, HERE / "barn_cabin_524_textured.blend")
        print(f"\nviewable: {blend}"
              f"  (textured lod0 — open this, not barn_cabin_524.blend)")
    else:
        print("\nviewable .blend NOT written: the export did not pass its gates.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
