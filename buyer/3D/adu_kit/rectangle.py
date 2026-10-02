"""
adu_kit/rectangle.py -- where the walls of a one-storey rectangle sit, from its spec (#172).

Plain Python; no Blender, so it can be unit-tested anywhere.

The helpers here are the ones Laurel's build.py and Willow's build both need and that know no
building: they read a partition's row and the wall thickness, and nothing about a roof, a window
or a scene. Laurel keeps its own copies until the second batch of the gate move (docs/
GATES-BATCH-2.md, 2a) points it here, with a golden-output check; Willow is the second consumer
that shows these are shared.
"""
from adu_kit.specread import sign as _sign


def partition_band(row, it):
    """(lo, hi): where a partition sits across its run -- its cited face and the face its studs
    run toward. ONE DEFINITION for the wall and the trim on it, so a partition that moves takes
    its casing and baseboard along.

    `row` is a spec partition ({id, at_ft, studs_toward, ...}) and `it` the interior wall's
    thickness in feet. A direction that is not one of +X -X +Y -Y is a readable SystemExit (the
    spec is read, not obeyed), from the same `sign` Laurel's build reads it with.
    """
    near = row["at_ft"]
    far = near + it if _sign(row["id"], row["studs_toward"]) > 0 else near - it
    return tuple(sorted((near, far)))
