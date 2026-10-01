"""
adu_kit/specread.py -- reading a spec's axis and direction words as untrusted input (#169).

Plain Python; no Blender.

A SPEC IS READ, NOT OBEYED. Both of these used to be `startswith("+")` and
`== "X"` with an else, so `studs_toward: north` built the wall on the
negative side and `runs_along: Z` rotated it, both in silence and both
producing a model that the envelope and door gates would go on to bless.
Review asked what a malformed value does; the answer was "something", and
the answer has to be "a readable failure".

Moved unchanged from Laurel's build.py, where the builder and the gates both read
them. The error text is the same, because probes match on it.
"""
AXES = ("X", "Y")
DIRECTIONS = {"+X": +1, "-X": -1, "+Y": +1, "-Y": -1}


def axis(who, value):
    if value not in AXES:
        raise SystemExit(f"{who}: runs_along is {value!r}, which is not one of "
                         f"{list(AXES)}. A partition runs along an axis of the frame.")
    return value


def sign(who, value):
    if value not in DIRECTIONS:
        raise SystemExit(f"{who}: studs_toward is {value!r}, which is not one of "
                         f"{sorted(DIRECTIONS)}. It says which way the studs run "
                         "from the cited face.")
    return DIRECTIONS[value]
