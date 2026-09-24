"""
adu_kit/publish.py — staged publishing of a model's export directory (#131).

    from adu_kit.publish import stage, promote

No Blender, so test_publish.py runs in CI. adu_kit.finish re-exports both.

EVERYTHING IS WRITTEN BESIDE THE REAL DIRECTORY AND MOVED IN AT THE END.
This was fixed artefact by artefact three times in the barn cabin before it
was fixed once: a run that failed a gate still published some files beside
older ones, a generation mix that never existed as a set.
"""
import os
import shutil
from pathlib import Path


def stage(final_out):
    """A fresh, empty staging directory beside `final_out`, which is created
    if it does not exist. Nothing in `final_out` changes until promote()."""
    final_out = Path(final_out)
    final_out.mkdir(parents=True, exist_ok=True)
    out = final_out.parent / (final_out.name + ".staging")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    return out


def promote(out, final_out):
    """Make `final_out` hold exactly the staged files. Returns the names of
    files removed because the new generation did not write them.

    os.replace is atomic per file on one filesystem, and the staging
    directory is a sibling of the real one, so it always is: a reader between
    two replaces sees two whole files, never a half-written one.

    THEN THE LEFTOVERS GO. Replacing only what was staged left any file the
    new run did not write -- a level an earlier run exported and this one
    dropped -- beside the new ones, and build_index.py reads every .glb it
    finds. The export directory is generated output and nothing else, so a
    file this run did not write is a file from another generation.
    Directories are left alone: an export writes none.
    """
    out, final_out = Path(out), Path(final_out)
    staged = sorted(out.iterdir())
    names = {p.name for p in staged}
    for src in staged:
        os.replace(src, final_out / src.name)
    removed = []
    for old in sorted(final_out.iterdir()):
        if old.is_file() and old.name not in names:
            old.unlink()
            removed.append(old.name)
    shutil.rmtree(out, ignore_errors=True)
    return removed
