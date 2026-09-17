# Annie's Backyard — Full UI/UX (with first-person + minimap)

The homeowner experience across all modalities, from page load through every lens, with the new **first-person "standing in the backyard"** view + **synced minimap** woven in. One Deck.gl canvas the homeowner never leaves; "modes" are camera + layer + lighting states she dials between. Companion to [`Matched-models presentation - UI-UX spec.md`](./Matched-models%20presentation%20-%20UI-UX%20spec.md) and [`Configurator presentation - UI-UX spec.md`](./Configurator%20presentation%20-%20UI-UX%20spec.md). Tracks issues DG-11/12/13/14/19/25/26 + new **DG-33** (first-person + minimap) and **DG-34** (minimap placement overlay).

---

## 0. The modality model

One canvas, four **lenses**, plus a persistent minimap and info panel. The spike's honesty rule governs which lens is photoreal vs. analytic:

| Lens | Camera | Scene fidelity | Job |
|---|---|---|---|
| **Reveal** (auto) | Aerial → drive-up fly-in | Photoreal (Google tiles) | "That's *my* house." Emotional hook. |
| **Place** | Orbit / ¾ working angle | Analytic (line-drawing + color ADU) | Move it, snap it, prove it fits. |
| **Stand in the yard** ⭐ | First-person, eye-level | Analytic massing + color ADU | Feel the scale; "how does it loom from my patio?" |
| **Sun & shade** | Orbit, locked | Analytic + real shadows | "Will it shade my garden?" |

A **minimap** rides along in *Place* and *Stand*. The **info panel** (price, fit, CTA) is always present. *Stand* and *Sun & shade* are analytic, not photoreal, because Google's aerial mesh goes melty at eye level — so the moment she's "in" the yard we switch to the clean line-drawing + full-color-ADU scene, where there's no photoreal expectation to break.

---

## 1. Page load → the Reveal

- **t = −1s (cold load):** address known (from her report). Near-black frame, Fraunces line *"Building your backyard…"*, thin amber progress hairline; a low-res top-down satellite of her lot is already painted so there's never a blank canvas.
- **t = 0 → 6s (cinematic reveal — photoreal lens):**
  1. **0s** top-down satellite, pulse on her parcel. *"123 Cherry St — let's look at your backyard."*
  2. **1s** world tilts to 67° oblique, range ~120 m; Google photoreal mesh resolves — her roof, trees, the Wasatch. *The gasp.*
  3. **2s** translucent **buildable-envelope** volume rises; label *"Buildable area · 24 × 30 × 18 ft."*
  4. **3s** matched **ADU lands in full color**, terrain-clamped, door to street frontage.
  5. **4.5s** camera drops to a ~3 m "drive-up," ADU framed against her real house (the only near-ground photoreal moment — brief, oblique, where the mesh still holds).
  6. **6s** info panel slides in; **lens switcher** fades in; gentle parallax idle.
- Skippable (`Skip ⏭` at 0.5s); `prefers-reduced-motion` → hard-cut to settled frame.

---

## 2. Resting frame & the lens switcher

A glass segmented control, bottom-center, reading left→right as a journey:

```
◎ Reveal   │   ✥ Place   │   ◉ Stand in yard   │   ☀ Sun & shade
```

Switching is a **camera + opacity + lighting morph in the same canvas** (no page change). **Reveal → Place** is the one fidelity hand-off: the photoreal mesh dissolves to ~10% while the line-drawing analytic scene blooms beneath the same ADU, same spot, same camera — reads as "the scene clarifying into a plan," not "a different app" (productized DG-05 morph).

---

## 3. Lens: **Place** (orbit + minimap)

```
┌──────────────────────────────────────────────────────┬───────────────┐
│  analytic scene: thin parcel lines, gray massing of   │ Maplewood 600 │
│  existing house, faint envelope, COLOR ADU            │ 600 sqft·1/1  │
│        ┌─ envelope ─────────────┐                      │ All-in $186k  │
│   ▭house│   ◇──── ADU ────◇      │← 12 ft to fence     │ ┌Box┬Dirt┬RT┐ │
│        │   ⟲        drag         │                      │ [✦ Start]    │
│        └────────────────────────┘  6 ft to house       │ ♡  ⤓  ▦      │
│  ┌─────────────┐                                       │               │
│  │ ▣ MINIMAP   │  N↑ [⤢]   ◎ Reveal│✥ Place│◉ Stand│☀ Sun            │
│  └─────────────┘                                       │               │
└──────────────────────────────────────────────────────┴───────────────┘
```

**Scene:** parcel boundary as thin amber-white lines, existing house as gray massing (footprint + LiDAR height), envelope as a faint tinted volume, setbacks dotted — and the **ADU in full lit color**, the hero.

**Placement (DG-19):**
- **Drag** the ADU, locked to the LiDAR ground plane; **magnet-snaps** to legal positions inside the envelope.
- **Rotate** via `⟲` ring (or two-finger twist).
- **Violation:** offending setback edge flares red, ADU tints red, tag *"2 ft into the rear setback,"* won't "stick"; releases back to nearest legal spot; feasibility pill flips to `▲ Doesn't fit here`.
- Every move **autosaves** (DG-32) and updates distance annotations.

**Minimap (DG-34):** bottom-left plan view — boundary, gray house, tinted envelope, dotted setbacks, **ADU footprint in amber**. Drag the ADU footprint on the minimap to move it (synced to the 3D view, re-runs fit check) — often more precise than perspective drag. `⤢` expands to a full plan overlay; north arrow + scale bar.

---

## 4. Lens: **Stand in the yard** ⭐ (first-person + minimap) — DG-33

**Entering:** tapping **◉ Stand in yard** eases the camera to eye level (~1.6 m) at a default standpoint (back patio, looking at the ADU); scene stays analytic massing (color ADU, gray house form, simple graded ground, gradient sky). One-time coachmark: *"You're standing in your backyard. Drag to look around; tap the map to move."*

```
┌──────────────────────────────────────────────────────────────────────┐
│            (sky gradient)                                              │
│                                  ╱▔▔▔▔▔▔╲                              │
│                            ╱▔▔▔▔  COLOR  ▔▔╲     ← ADU at true scale,  │
│        ▟▙ gray             │      ADU      │       eye level           │
│      ▟███▙ existing        │   ▢ door  ▢   │                           │
│   ───────────────────────── ground / grade ──────────────────────     │
│   ⟳ vantage:  ◉ Patio   ○ Far corner   ○ Side yard   ○ Kitchen window  │
│  ┌─────────────┐                                                       │
│  │ ▣ MINIMAP   │   you-are-here wedge + ADU footprint                  │
│  └─────────────┘     ◎ Reveal │ ✥ Place │ ◉ Stand │ ☀ Sun             │
└──────────────────────────────────────────────────────────────────────┘
```

- **Look:** drag to pan/tilt the head (mobile: optional device-orientation); horizon stays level (no roll → no nausea).
- **Move — deliberately *not* free-roam** (sparse analytic scene + no ground texture would be disorienting): two affordances —
  1. **Vantage presets** — *Patio · Far corner · Side yard · Kitchen window* — each a curated standpoint that frames the ADU; one tap eases there (~1s).
  2. **Tap the minimap** — sets her standpoint; the **you-are-here wedge** (camera frustum) updates; the main view eases to that eye-line.
- **Where she looks (so she never faces a fence):** a tap only sets *position* — the look-direction is explicit. The standpoint **snaps to a valid standing zone** (not inside the house, off-parcel, or jammed against a boundary) with a **minimum standoff** from the ADU/structures, then the camera **auto-aims at the ADU** (look-at its centroid ~mid-height, pitch framing its full height, horizon level). To look elsewhere: drag the **minimap view-wedge** to rotate heading, free-look after landing, or use the **`Look at:` toggle** (`ADU` default / `Existing house` / `Out the yard`) for sightline & privacy checks ("will it block my mountain view?").
- **Minimap** shows her **standpoint + view wedge**, ADU footprint, envelope, house — she always knows where she stands and looks. Drag the ADU footprint here to reposition and immediately feel, from where she stands, whether it's now too close.
- **Payoff line** (info panel): *"From your patio, the ADU's ridge is about 4 ft above your fence line."*
- **Honesty chip** (once): *"This is a scale model, not a photo — it's for judging size and distance."*

---

## 5. Lens: **Sun & shade** (analytic + real shadows) — DG-26

Same analytic scene; camera locks to ¾ overview; the **shadow scrubber** appears:

```
☀───────────●─────────  9a ·· noon ·· 5p     |   Jun 21 ▾
```

Dragging the sun arcs it across the sky; ADU + existing house cast **real shadows** on grade, garden, fence. Date presets **Jun 21 / Dec 21 / Today**. *"Drag to see how the shadow falls — handy if you've got a garden back here."* Analytic-only (can't honestly relight Google's mesh; shadows live where we own the light).

---

## 6. The minimap, specified once (Place + Stand)

- **Position/size:** bottom-left inset ~220×220 px, glass frame, 14 px radius; collapsible to a tab; `⤢` → half-screen plan overlay.
- **Layers (plan):** parcel boundary (line), existing house (gray fill), envelope (tint), setbacks (dotted), **ADU footprint (amber)**, and in *Stand* the **camera frustum wedge** + standpoint dot; north arrow + scale bar.
- **Interactions:** drag ADU footprint → move ADU (synced, re-runs fit check); in *Stand*, tap empty ground → move standpoint; pinch to zoom.
- **Sync:** a second Deck.gl `MapView` sharing the same geo-coordinates as the main view, so the two never disagree (coordinate consistency handled by one source of truth).

---

## 7. Interior (the one true scene change)

The info panel's **▦ Adjust** exposes an **Interior** tab → swaps the right rail to a finish board (flooring, counters, cabinets, accessibility upgrades) with live price deltas + spec sheet, and optionally swaps the main view to a 2D floor plan with room hotspots. **"Step inside"** opens a modal Gaussian-splat walkthrough of the built model — the only genuinely separate scene, framed as entering a different space (DG-22/23).

---

## 8. Persistent chrome (all lenses)

- **Info panel** (right): name/specs, **all-in price with Box / Dirt / Red Tape** (Dirt slope-aware from LiDAR), **feasibility pill**, **✦ Start My Project**, ♡ Save / ⤓ Share / ▦ Adjust. Price + fit update live.
- **Top bar:** address, feasibility pill, view-reset `⟳`, measurements toggle `⌗`, help `?`.
- **Lens switcher** (bottom-center) — always available except during the Reveal.

---

## 9. Transitions

- **Reveal → Place:** photoreal mesh dissolves to ~10%, analytic line-drawing blooms beneath the unchanged ADU; camera idle → ¾. ~900 ms.
- **Place → Stand:** camera ¾ → eye level at default vantage; envelope/annotations fade faint; minimap gains the view-wedge. ~1 s.
- **Stand → Sun & shade:** camera lifts to ¾; shadow scrubber slides up; sun engages.
- **Any → Reveal:** photoreal mesh blooms back; camera lifts to oblique.
- All eased (`easeInOutCubic`); all gated by `prefers-reduced-motion` (→ cuts).

---

## 10. States, mobile, accessibility

- **Loading:** instant low-res satellite + hairline; lenses disabled until ready; analytic geometry can load while photoreal streams.
- **No photoreal coverage:** Reveal degrades to a stylized top-down→tilt of the analytic scene; Place/Stand/Sun unaffected (already analytic). *"3D photo view isn't available for your street yet."*
- **Mobile:** lens switcher → bottom-sheet segmented control; minimap docks to a corner (tap-to-expand); *Stand* offers device-orientation look; landscape lock; perf budget gates photoreal (opt-in "View in 3D").
- **Accessibility:** every lens has a non-3D equivalent — plan view + text "Details" (dimensions, all-in + breakdown, setbacks, fit verdict, and in *Stand* the "ridge ~4 ft above fence" line as text). Placement reachable by keyboard ("nudge 1 ft N/S/E/W") and by minimap. Live region announces fit changes. Color never the only signal. Reduced-motion honored.

---

## 11. The emotional arc

**See it (Reveal) → place it (Place) → stand in it (Stand) → check the sun (Sun) → make it hers (Interior) → start the project.** Photoreal earns desire; the analytic lenses earn trust and felt scale — and **Stand-in-the-yard + minimap** closes the gap between "looks nice from above" and "won't loom over my patio," the anxiety that stalls an ADU decision. Every spatial claim on screen is a real fact (LiDAR grade, parcel lines, setbacks), and the one place we drop photorealism is the one place photorealism would lie.
