"""
adu_kit/specread.py -- reading a spec's axis and direction words as untrusted input (#169).

Plain Python; no Blender.

A SPEC IS READ, NOT OBEYED. Both of these used to be `startswith("+")` and
`== "X"` with an else, so `studs_toward: north` built the wall on the
negative side and `runs_along: Z` rotated it, both in silence and both
producing a model that the envelope and door gates would go on to bless.
Review asked what a malformed value does; the answer was "something", and
the answer has to be "a readable failure".

Moved from Laurel's build.py, where the builder and the gates both read them. The
error text is the same, because probes match on it. One change: both now check the
value is a string first, because a YAML list or mapping made `sign()` raise
TypeError (unhashable) instead of the readable SystemExit.
"""
AXES = ("X", "Y")
DIRECTIONS = {"+X": +1, "-X": -1, "+Y": +1, "-Y": -1}


def axis(who, value):
    # A STRING FIRST: a spec is YAML, so `runs_along: [X]` or `{}` is a valid document,
    # and `in` on a dict raises TypeError (unhashable) instead of the readable failure.
    if not isinstance(value, str) or value not in AXES:
        raise SystemExit(f"{who}: runs_along is {value!r}, which is not one of "
                         f"{list(AXES)}. A partition runs along an axis of the frame.")
    return value


def sign(who, value):
    # A STRING FIRST, for the same reason: `studs_toward: []` made `value not in
    # DIRECTIONS` raise TypeError. The original in Laurel's build.py had this bug too
    # (review of #177 found it); the error text for every string is unchanged.
    if not isinstance(value, str) or value not in DIRECTIONS:
        raise SystemExit(f"{who}: studs_toward is {value!r}, which is not one of "
                         f"{sorted(DIRECTIONS)}. It says which way the studs run "
                         "from the cited face.")
    return DIRECTIONS[value]
