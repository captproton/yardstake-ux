"""
adu_kit — what every ADU model shares, and nothing any one model knows.

Extracted from the barn cabin (#126) as a MOVE, not a change: the barn
cabin's export is byte-identical before and after, and every gate and probe
passes unchanged.

    kernel.py      the geometry kernel: boxes, prisms, welds, sweeps, lofts,
                   booleans, reveals, in-plane UVs, reading a spec
    export.py      feet to metres, the Draco .glb writer, the .glb reader
    verify_lib.py  inside_mesh(), for a model's gates

NOT HERE YET, ON PURPOSE. The plan (models/laurel_a1_460/docs/PLAN.md) names
more, but only what knows no building moves:
    views.py            names this building's rooms (Floor_bath, the kitchen)
    textures            the generators are generic; the barn cabin's main() is
                        not. They move when a second model uses them.
    inside_mesh_cases   known answers about the barn cabin's own objects
    schema/             model_contract.py moves in its own PR, because the
                        configurator page and its probes depend on it

A module runs inside Blender (bpy, bmesh, mathutils). A model's scripts put
buyer/3D on sys.path and import `adu_kit.<module>`.
"""
