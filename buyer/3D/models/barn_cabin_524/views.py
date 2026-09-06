"""
views.py — interior viewing modes for the Blender GUI.

Run from Blender's Text Editor (Open -> views.py -> Run Script), or from the
Python Console:

    exec(open("/full/path/to/views.py").read())
    dollhouse()

then one of:

    full()        everything visible, as exported
    dollhouse()   roof and ceilings off -- look down into the rooms
    cutaway()     dollhouse, plus the south wall and porch off
    walkthrough() dollhouse, plus near-clip pulled in for first-person walking
    interior_only()  just the interior surfaces, no shell at all

Nothing here changes geometry or materials, only visibility, so it cannot
affect an export. `full()` restores.

Why a script rather than outliner checkboxes: the roof is its own collection
and does toggle in one click, but the ceilings are not -- they live in `Finish`
alongside the floors, doors and trim, and a verify_tier1 gate asserts that. So
hiding "everything above head height" is a per-object job, which is exactly
what a script is for.

Visibility keys off the object-name prefixes declared in spec.yaml, the same
convention the display modes and the glTF export rely on. New prefixes must be
declared there or these modes silently stop covering them.
"""
import bpy

# Prefix groups. Kept as prefixes, not names, so new trim or ceiling objects
# are picked up without editing this file.
ROOF = ("Roof_",)
CEILING = ("Ceil_", "Porch_ceiling")
SOUTH = ("Wall_S", "Porch_", "Gable_S")
SHELL = ("Wall_", "Gable_", "Dormer_", "Eave_", "Roof_", "Porch_", "Glazing_")


def _matches(ob, prefixes):
    return any(ob.name.startswith(p) for p in prefixes)


def _show(prefixes=(), hide=()):
    """Hide objects matching `hide`; show everything else."""
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        ob.hide_set(_matches(ob, hide))
        ob.hide_render = _matches(ob, hide)


def _viewport(near=None, shading="MATERIAL"):
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for sp in area.spaces:
                if sp.type != "VIEW_3D":
                    continue
                sp.shading.type = shading
                if near is not None:
                    sp.clip_start = near


def full():
    """Everything visible, exactly as exported."""
    _show()
    _viewport(near=0.1)
    print("[view] full")


def dollhouse():
    """Roof and ceilings off — the view a buyer spends most time in."""
    _show(hide=ROOF + CEILING)
    _viewport(near=0.1)
    print("[view] dollhouse — roof and ceilings hidden")


def cutaway():
    """Dollhouse with the south wall and porch removed, for a sectional look."""
    _show(hide=ROOF + CEILING + SOUTH)
    _viewport(near=0.1)
    print("[view] cutaway — roof, ceilings, south wall and porch hidden")


def walkthrough():
    """First-person, with everything visible and the near clip pulled in.

    Deliberately NOT the dollhouse hiding: standing inside a room, you want the
    ceiling above you. Hiding it is right for looking down into the model and
    wrong for walking through it -- the vaulted living ceiling is one of the
    better things in here and the loft reads as open sky without it.

    The near clip matters. The scene is authored at 1 unit = 1 foot, so the
    default 0.1 sits about an inch from the eye once the unit scale is applied
    and slices through door casings as you pass them. 0.01 is comfortable.

    Then press Shift+` in the viewport to walk: W/A/S/D, mouse to look,
    Q and E for down and up, Shift to move faster. Esc or right-click exits
    without keeping the move; left-click or Enter keeps it.
    """
    _show()
    _viewport(near=0.01)
    print("[view] walkthrough — now press Shift+` in the viewport, W/A/S/D to move")


def interior_only():
    """Interior surfaces alone — floors, ceilings, partitions, doors, trim."""
    _show(hide=SHELL)
    _viewport(near=0.01)
    print("[view] interior only — shell hidden")


if __name__ == "__main__":
    dollhouse()
