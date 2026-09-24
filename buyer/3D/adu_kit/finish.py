"""
adu_kit/finish.py — the finishing steps every model's export takes, in Blender.

    from adu_kit.finish import make_materials, assign, closure_problems, ...

Moved out of the barn cabin's finish_adu.py for #131, when Laurel became the
second model to export. A MOVE, not a change: the barn cabin's four .glb files
and its manifest are byte-identical before and after.

What stays with each model: glazing (it reads that building's openings),
furniture, the dimensions block, and the scale gate.
"""
import os
import shutil
from pathlib import Path

import bpy
import bmesh


def make_materials(spec, texture_dir, textured=True):
    """One Principled material per spec.materials.library entry, named
    `adu_<key>`. Colours, maps, roughness, emission and transmission all come
    from the spec; nothing is hardcoded here."""
    lib = spec["materials"]["library"]
    _sd = spec["materials"].get("sidedness") or {}
    two_sided = set(_sd.get("double_sided") or {})
    # THE DEFAULT HAS TO DO SOMETHING OR IT SHOULD NOT BE THERE. It was once
    # published and ignored: the builder hard-coded single and read only the
    # exception list.
    _default_single = _sd.get("default", "single") == "single"
    tdir = Path(texture_dir)
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
        # SINGLE-SIDED UNLESS THE SPEC SAYS OTHERWISE. Blender writes
        # glTF `doubleSided = not use_backface_culling`, and the default left
        # every material double-sided by omission rather than by decision.
        mat.use_backface_culling = _default_single != (name in two_sided)

        bsdf.inputs["Roughness"].default_value = m.get("roughness", 0.8)
        bsdf.inputs["Metallic"].default_value = m.get("metallic", 0.0)
        if m.get("emissive_linear"):
            # Blender's exporter turns Emission into emissiveFactor, and a
            # strength above 1 into KHR_materials_emissive_strength. The socket
            # was renamed between Blender versions, so probe rather than assume.
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


def assign(spec, mats, extra_slots=None):
    """Apply spec.materials.assignment by object-name prefix. First match
    wins. Returns the names of meshes no rule matched.

    `extra_slots` maps a polygon material_index to a library key, for faces a
    build tagged -- the barn cabin's reveals are slot 1 (trim) and inward faces
    slot 2 (drywall). materials.clear() RESETS every polygon's index to 0,
    which once silently discarded that tagging, so the indices are captured
    first and restored once the slots exist.
    """
    extra = extra_slots or {}
    rules = list(spec["materials"]["assignment"].items())
    unmatched = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for prefix, mname in rules:
            if ob.name.startswith(prefix):
                tagged = {i: poly.material_index
                          for i, poly in enumerate(ob.data.polygons)
                          if poly.material_index in extra}
                ob.data.materials.clear()
                ob.data.materials.append(mats[mname])
                if tagged:
                    for slot in sorted(extra):
                        ob.data.materials.append(mats[extra[slot]])
                    for i, slot in tagged.items():
                        ob.data.polygons[i].material_index = slot
                break
        else:
            unmatched.append(ob.name)
    return unmatched


def closure_problems(objects, lod):
    """Every exported mesh a closed solid, wound outwards.

    THE SAFETY PRECONDITION FOR SINGLE-SIDED MATERIALS, checked on what
    ships. CLOSURE IS NOT ENOUGH: glTF culls by WINDING, so a sealed mesh
    wound inside out has its exterior culled and vanishes. Signed volume is
    the test: positive means the faces face out.
    """
    problems = []
    for o in objects:
        if not o.data.polygons:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_e = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        vol = bm.calc_volume(signed=True)
        bm.free()
        if open_e:
            problems.append(f"{lod}:{o.name} is not closed ({open_e} edges)")
        elif vol <= 0:
            problems.append(f"{lod}:{o.name} is wound inside out "
                            f"(signed volume {vol:.4f})")
    return problems


def lod2_contract_nodes(spec):
    """The declared lod2 node list, or None if the spec declares none.

    lod2 is the placement developer's handoff, and what is at risk is its
    INTERFACE: how many nodes, and the names they address objects by.
    `(spec.get("export") or {})`, not `spec.get("export", {})`: deleting the
    contract block leaves `export:` present and null.
    """
    contract = (spec.get("export") or {}).get("lod2_contract") or {}
    return sorted(contract.get("nodes") or []) or None


def report_lod2_contract(want, got):
    """Print the verdict. True only if the contract is satisfied.

    FAILS CLOSED: no contract is not "nothing to check", it is the check
    missing.
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


def stage(final_out):
    """A fresh staging directory beside `final_out`.

    EVERYTHING IS WRITTEN BESIDE THE REAL DIRECTORY AND MOVED IN AT THE END.
    Fixed artefact by artefact three times before it was fixed once: a run
    that failed a gate still published some files beside older ones, a
    generation mix that never existed as a set. Nothing in `final_out`
    changes until every gate has passed.
    """
    final_out = Path(final_out)
    final_out.mkdir(parents=True, exist_ok=True)
    out = final_out.parent / (final_out.name + ".staging")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    return out


def promote(out, final_out):
    """Move every staged file into `final_out`, as a set.

    os.replace is atomic per file on one filesystem, and the staging
    directory is a sibling of the real one, so it always is. A reader between
    two replaces sees two consistent files, never a half-written one.
    """
    for src in sorted(Path(out).iterdir()):
        os.replace(src, Path(final_out) / src.name)
    shutil.rmtree(out, ignore_errors=True)
