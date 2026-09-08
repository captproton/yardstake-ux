"""Foundation vents as DRAWN on A2.0 FOUNDATION PLAN.

Calibration, anchored on interior faces because the drawn band is line-weight
inflated (tools/tier3/frame.py documents the same effect on A1.1):

    interior north face y=375 -> interior south face y=1511
        = 1136 px over 24'-0" less two 8" stemwalls = 22'-8"
        -> 50.119 px/ft, against the 50.0 that 1/4"=1'-0" at 200 dpi must give.

Cross-checks that did NOT feed the calibration:
    east stemwall band measures 30 px = 7.2" against its 8" callout
    outer width 191..1288 = 1097 px = 21.9' against 22'-0"

A vent is drawn as a white box with an X through it; the stemwall is a grey
concrete hatch. An opening is therefore a run of columns that is mostly PURE
WHITE across the band.
"""
import numpy as np
from PIL import Image

a = np.asarray(Image.open("found_plan_full.png").convert("L")).astype(float)

T = 0.667                                  # 8" stemwall
S = 50.119                                 # px/ft, derived above
N_IN, S_IN = 375.0, 1511.0                 # interior north / south faces
W_OUT = 191.0                              # west outer face (ink, clean)
N_OUT = N_IN - T * S
S_OUT = N_OUT + 24.0 * S
E_OUT = W_OUT + 22.0 * S
W_IN, E_IN = W_OUT + T * S, E_OUT - T * S


def runs(mask, lo, hi):
    out, st = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and st is None:
            st = i
        elif not v and st is not None:
            if lo <= i - st <= hi:
                out.append((st, i))
            st = None
    return out


LO, HI = int(0.9 * S), int(1.9 * S)
PAD = 4


def scan(sub, base, origin):
    prof = (sub >= 248).mean(axis=0)
    return [((p + base - origin) / S, (q + base - origin) / S)
            for p, q in runs(prof > 0.55, LO, HI)]


walls = {
    "NORTH": (a[int(N_OUT + PAD):int(N_IN - PAD), int(W_OUT):int(E_OUT)],
              int(W_OUT), W_OUT, 22.0, "X measured EAST from the west outer face"),
    "SOUTH": (a[int(S_IN + PAD):int(S_OUT - PAD), int(W_OUT):int(E_OUT)],
              int(W_OUT), W_OUT, 22.0, "X measured EAST from the west outer face"),
    "WEST": (a[int(N_OUT):int(S_OUT), int(W_OUT + PAD):int(W_IN - PAD)].T,
             int(N_OUT), N_OUT, 24.0, "Y measured SOUTH from the north outer face"),
    "EAST": (a[int(N_OUT):int(S_OUT), int(E_IN + PAD):int(E_OUT - PAD)].T,
             int(N_OUT), N_OUT, 24.0, "Y measured SOUTH from the north outer face"),
}

print("=" * 72)
print("FOUNDATION VENTS DRAWN ON A2.0")
print("=" * 72)
total, widths = 0, []
for name, (sub, base, origin, span, datum) in walls.items():
    v = scan(sub, base, origin)
    total += len(v)
    print(f"\n{name} wall — {len(v)} vent(s)")
    print(f"    {datum}")
    for p, q in v:
        widths.append(q - p)
        print(f"      {p:6.2f} .. {q:6.2f} ft   width {(q - p) * 12:4.1f}\"   "
              f"nearest corner {min(p, span - q):5.2f} ft")

print("\n" + "-" * 72)
print(f"TOTAL: {total} vents")
if widths:
    print(f"drawn width: mean {np.mean(widths) * 12:.1f}\", "
          f"min {min(widths) * 12:.1f}\", max {max(widths) * 12:.1f}\"")
    area = total * np.mean(widths) * 0.667
    print(f"if each is 8\" tall: {area:.2f} sf gross = {area * 144:.0f} sq in")
