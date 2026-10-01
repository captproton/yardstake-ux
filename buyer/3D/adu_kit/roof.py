"""
adu_kit/roof.py -- the roof as a list of planes, and the ceiling as its own thing (#167).

Plain Python; no Blender, so it can be tested anywhere.

WHY A LIST OF PLANES. Laurel's roof was one surface: `Shed.under(y)`. Willow's
preflight (docs/WILLOW-PREFLIGHT.md) found two gables that meet, a 5:12 main roof
and a 3:12 porch roof, and a function of Y alone cannot say which of them covers a
point. A roof here is a list of `Plane`s, each with a slope and an extent. Laurel is
a list of one.

WHY THE CEILING IS SEPARATE. Laurel's walls and partitions run to the roof underside
because its ceilings follow the roof (A-1.0, "CEILINGS FOLLOW ROOF LINE"). That is a
fact about Laurel, not about roofs: a truss roof over an attic stops its partitions at
a ceiling below the roof. So code that builds a wall asks the CEILING for its head
height, and code that builds the roof, or checks it, asks the ROOF. For Laurel the two
give the same number, by construction (`FollowsRoof` delegates), which is what lets
this move be proved byte-identical. Willow's ceiling form is not yet confirmed (see
the preflight); `Flat` is here because a flat ceiling is the likely answer, not
because it has been decided.

WHAT IS NOT DECIDED HERE. Two planes that overlap (where Willow's porch gable meets
its main roof) are given the LOWER underside at a shared point, which is what
someone standing under them would meet. That rule has only been exercised on
synthetic planes. The Willow build (#172) is the real test of this interface, and it
may need to change; do not treat it as frozen.

THE FLOAT EXPRESSIONS ARE LAUREL'S. `Plane.under_y(y)` is `z0 + dz_dy * y`, the
expression `Shed.under` used, so a model that moves onto this gets the same numbers
to the last bit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class RoofError(ValueError):
    """A roof or ceiling that cannot answer the question asked."""


@dataclass(frozen=True)
class Plane:
    """One planar roof surface: underside z = z0 + dz_dx*x + dz_dy*y, over a rectangle.

    `x` and `y` are (low, high) in the model's frame, in feet. A plane does not exist
    outside its rectangle, and asking it for a point there is an error, not a guess.
    """
    z0: float
    dz_dx: float
    dz_dy: float
    x: tuple
    y: tuple

    def __post_init__(self):
        for name, span in (("x", self.x), ("y", self.y)):
            if len(span) != 2 or not span[0] < span[1]:
                raise RoofError(f"plane {name} extent {span!r} must be (low, high) with low < high")

    @property
    def x_independent(self) -> bool:
        return self.dz_dx == 0.0

    def covers(self, x: float, y: float) -> bool:
        return self.x[0] <= x <= self.x[1] and self.y[0] <= y <= self.y[1]

    def covers_y(self, y: float) -> bool:
        return self.y[0] <= y <= self.y[1]

    def under(self, x: float, y: float) -> float:
        if not self.covers(x, y):
            raise RoofError(f"({x}, {y}) is outside this plane's extent x {self.x}, y {self.y}")
        return self.z0 + self.dz_dx * x + self.dz_dy * y

    def under_y(self, y: float) -> float:
        """The underside at `y`, for a plane that does not vary with X."""
        if not self.x_independent:
            raise RoofError("under_y() asked of a plane that slopes in X; use under(x, y)")
        if not self.covers_y(y):
            raise RoofError(f"y {y} is outside this plane's extent {self.y}")
        return self.z0 + self.dz_dy * y

    def yz_solid(self, thickness: float):
        """(profile, x0, x1): this plane thickened upward, as a YZ prism to extrude along X.

        The profile's order and expressions are the ones Laurel's roof was built with.
        Only a plane that does not vary with X is a YZ prism.
        """
        if not self.x_independent:
            raise RoofError("yz_solid() asked of a plane that slopes in X")
        y0, y1 = self.y
        profile = [(y0, self.under_y(y0)), (y1, self.under_y(y1)),
                   (y1, self.under_y(y1) + thickness), (y0, self.under_y(y0) + thickness)]
        return profile, self.x[0], self.x[1]


class Roof:
    """A list of planes. Laurel's is a list of one."""

    def __init__(self, planes: Sequence[Plane]):
        planes = tuple(planes)
        if not planes:
            raise RoofError("a roof needs at least one plane")
        if not all(isinstance(p, Plane) for p in planes):
            raise RoofError("a roof is a list of Plane objects")
        self.planes = planes

    @property
    def x_independent(self) -> bool:
        return all(p.x_independent for p in self.planes)

    def extent(self) -> tuple:
        """((x_low, x_high), (y_low, y_high)): the box all planes fit in."""
        return ((min(p.x[0] for p in self.planes), max(p.x[1] for p in self.planes)),
                (min(p.y[0] for p in self.planes), max(p.y[1] for p in self.planes)))

    def covers_y(self, y: float) -> bool:
        """Is there any roof at this Y? A gate asking "is this below the roof?" has
        nothing to check where there is none (a condenser beyond the rear overhang),
        and must say so, not extrapolate a surface that does not exist."""
        return any(p.covers_y(y) for p in self.planes)

    def under(self, x: float, y: float) -> float:
        """The underside at a point: the lowest of the planes covering it."""
        zs = [p.under(x, y) for p in self.planes if p.covers(x, y)]
        if not zs:
            raise RoofError(f"no plane of this roof covers ({x}, {y})")
        return min(zs)

    def under_y(self, y: float) -> float:
        """The underside at `y`, for a roof no plane of which slopes in X.

        Refuses a roof that does, instead of returning an answer that is true for one
        X only. That refusal is the guard: a builder that draws every wall as a YZ
        prism cannot silently accept Willow's porch gable.
        """
        if not self.x_independent:
            raise RoofError("under_y() asked of a roof with a plane that slopes in X; "
                            "this builder draws YZ profiles and cannot represent it")
        zs = [p.under_y(y) for p in self.planes if p.covers_y(y)]
        if not zs:
            raise RoofError(f"no plane of this roof covers y {y}")
        return min(zs)

    def yz_solids(self, thickness: float) -> list:
        """[(profile, x0, x1), ...]: one thickened YZ prism per plane."""
        return [p.yz_solid(thickness) for p in self.planes]


class FollowsRoof:
    """A vaulted ceiling: its head height is the roof's underside (Laurel)."""
    kind = "follows_roof"

    def __init__(self, roof: Roof):
        self.roof = roof

    def under(self, x: float, y: float) -> float:
        return self.roof.under(x, y)

    def under_y(self, y: float) -> float:
        return self.roof.under_y(y)

    def covers_y(self, y: float) -> bool:
        return self.roof.covers_y(y)


class Flat:
    """A flat ceiling at one height, below the roof (a truss roof over an attic)."""
    kind = "flat"

    def __init__(self, z: float):
        self.z = z

    def under(self, x: float, y: float) -> float:
        return self.z

    def under_y(self, y: float) -> float:
        return self.z

    def covers_y(self, y: float) -> bool:
        return True


def ceiling_for(follows, roof: Roof):
    """The ceiling a spec's `roof.ceiling.follows` names. The spec is read, not obeyed:
    anything but a form this module knows is a readable error."""
    if follows == "roof":
        return FollowsRoof(roof)
    raise RoofError(f"roof.ceiling.follows is {follows!r}; this builder knows only 'roof'. "
                    "A flat ceiling needs its height from the spec: add it when a model has one.")
