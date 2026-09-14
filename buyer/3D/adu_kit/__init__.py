"""
adu_kit — what every ADU model shares, and nothing any one model knows.

Extracted from the barn cabin (#126) as a MOVE, not a change: the barn
cabin's export is byte-identical before and after, and every gate and probe
passes unchanged.

    kernel.py      the geometry kernel: boxes, prisms, welds, sweeps, lofts,
                   booleans, reveals, in-plane UVs, reading a spec
    export.py      feet to metres, the Draco .glb writer, the .glb reader
    verify_lib.py  inside_mesh(), for a model's gates
    sheets.py      harvest dimension CANDIDATES from a plan set PDF, never a
                   spec (#127). Plain Python, needs pdftotext:
                   python3 -m adu_kit.sheets PLANS.pdf --pages 4,6
    spec_lint.py   every number in a model spec is cited, and every drawn
                   length is on the sheet it cites (#128):
                   python3 -m adu_kit.spec_lint models/<id>/spec.yaml --pdf PLANS.pdf
    schema/        model_contract.py: what a valid identity, index row, .glb,
                   manifest, configuration and estimate are. No Blender, so
                   build_index.py, the verify scripts and the page's
                   fixtures import it too.

NOT HERE YET, ON PURPOSE. The plan (models/laurel_a1_460/docs/PLAN.md) names
more, but only what knows no building moves:
    views.py            names this building's rooms (Floor_bath, the kitchen)
    textures            the generators are generic; the barn cabin's main() is
                        not. They move when a second model uses them.
    inside_mesh_cases   known answers about the barn cabin's own objects

kernel, export and verify_lib run inside Blender (bpy, bmesh, mathutils);
schema does not. A script puts buyer/3D on sys.path and imports
`adu_kit.<module>`.
"""
