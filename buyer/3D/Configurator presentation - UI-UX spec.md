# The Configurator — Full UI/UX Spec

Companion to [`Matched-models presentation - UI-UX spec.md`](./Matched-models%20presentation%20-%20UI-UX%20spec.md). Where the presentation moment is *"see the dream,"* the configurator is *"make it yours and prove it fits."* Per the approved direction it is **not a separate app** — it's a **mode of the same Deck.gl canvas**, entered by tapping **Configure** / **Adjust** on the presentation panel. No page reload; same model, same spot, camera eases to a clean working ¾ angle.

Design ethos (from `BUYER_EXPERIENCE_VISION.md`): **"online shopping, not architecture"** — browsing IKEA, not meeting an architect. ADUs are pre-designed modular products, so configuration = *choosing options on a fixed product* (like car trims), never free-form design.

---

## 0. The two-axis structure

| Axis | Where it lives | Page transition? |
|---|---|---|
| **Exterior / placement** | In the 3D scene (the same Deck.gl canvas) | **No** |
| **Interior / finishes** | A different *view* (tab/drawer/floor plan), same page | **No** (optional "Step inside" modal is the only true scene change) |

Everything updates **price** (data delta) and **feasibility** (PostGIS fit check) in real time.

---

## 1. Resting layout (configurator mode)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ◂ 123 Cherry St   [● Fits your lot ✓]                         ⤢  ⟳  ?       │
├──────────────────────────────────────────────┬─────────────────────────────┤
│                                               │  [ Exterior ] [ Interior ]  │ ← view tabs
│        ╔═══ buildable envelope ═══╗           │  ───────────────────────── │
│        ║   ┌───────────────┐      ║           │  Maplewood 600              │
│        ║   │   ◇ ADU ◇      │◄──┐  ║           │  Choose your look           │
│   ▣    ║   └───────────────┘   │  ║           │                             │
│ house  ║      ⟲ rotate    drag │  ║           │  Siding   ▢▣▢▢  (4 swatches)│
│        ╚══════════════════════════╝           │  Roof     ▣ gable ▢ flat    │
│         6 ft to house · 12 ft to fence        │  Add-ons  ☑ Deck +$8k        │
│                                               │           ☐ Covered porch    │
│   ◇ snap-to-envelope · turns red on setback   │  Model    ◂ 600 · 480 · 340 ▸│
│                                               │  ─────────────────────────  │
│                                               │  All-in  ~$194,000  ▲ +$8k  │
│  [ ⟲ Reset placement ]      [ Compare ▢▢ ]    │  [ ✦ Continue to financing ]│
└──────────────────────────────────────────────┴─────────────────────────────┘
```

The 3D occupies the left ~⅔; the **config panel** is a persistent right rail (becomes a bottom sheet on mobile). The envelope is **always visible here** (unlike presentation, where it's dimmed) because fitting is the job.

---

## 2. Exterior axis — lives in the 3D scene

Tapping **Configure** reveals manipulation affordances on the model. No navigation.

### 2.1 Placement
- **Drag** the ADU across the lot — motion **locked to the ground plane** (terrain-clamped to LiDAR ground Z; it rides the slope, never floats/buries).
- **Snap-to-envelope:** as she drags, the footprint **snaps to legal positions** inside the buildable envelope. Drag toward a boundary and the box **turns red + the violated setback edge glows** the instant the footprint crosses it; the placement won't "stick" outside the envelope. This is the configurator's core purpose — live feasibility, not decoration.
- **Rotate** via a ⟲ ring handle (or two-finger twist) — updates heading/door-facing; setback check re-runs at the new orientation.
- **Reset placement** returns to the `PlacementService` default (backyard centroid, perpendicular to street frontage).

> Deck.gl has no built-in gizmos — drag/rotate are implemented via layer picking + pointer events writing to scene state. Custom work, not a checkbox.

### 2.2 Massing / variants (NOT free-scale)
Because the product is modular, "size" is a **variant swap**, not a stretch:
- **Model stepper** (`◂ 600 · 480 · 340 ▸`) swaps the whole GLB to another standardized footprint; envelope fit + price recompute. The swap is a **camera-locked cross-fade in the same spot** (same pattern as the presentation carousel).
- **Roof option** (gable / flat / shed) → variant or sub-model swap.
- **Add-ons** (deck, covered porch) → attachable sub-models that extend the footprint; the fit check includes them.

### 2.3 Exterior color / material
Three implementation tiers (pick per budget — `PRESENTATION_LAYER_ARCHITECTURE.md` §5 asset reality applies):
1. **Color tint** on the `ScenegraphLayer` model — cheap, fine for the massing-block MVP.
2. **Variant GLBs** per siding/roof combo — robust; cap the option matrix to avoid asset explosion.
3. **Three.js custom layer inside Deck.gl** — full PBR material swaps on one base model; most engineering, no asset blow-up. Only if rich material config becomes a selling point.

Swatches live in the panel; selecting one updates the model material live.

---

## 3. Interior axis — a different view, same page

The exterior scene physically can't show interiors, so the **Interior** tab swaps the *right-rail content* (and optionally the main view), without leaving the route. Three tiers, cheapest first:

1. **Finish board (baseline).** Swatch groups — flooring, counters, cabinets, fixtures — plus **accessibility upgrades** (grab bars, roll-in shower, wider doors; surfaced warmly for the "aging parents" dream). Each choice updates price + a running **spec sheet**. Almost pure data; no interior 3D. This *is* the "IKEA, not architecture" experience.
2. **2D floor plan with hotspots.** The main view swaps from the lot scene to the manufacturer's floor plan (existing PDF/SVG asset); click a room → set its finishes. Legible, cheap.
3. **"Step inside" walkthrough (premium).** A modal loading a separate interior GLB or a **Gaussian-splat walkthrough of the built model**. This is the *only* true scene change in the whole flow — and it's *meant* to feel like entering a different space, so the modal framing is honest.

---

## 4. Price & feasibility — always live, everywhere
- **Price** updates on every choice (Box / Dirt / Red Tape model carried from the report; Dirt stays slope-aware from LiDAR). A small `▲ +$8k` delta animates on change so cause↔effect is obvious.
- **Feasibility pill** (top-left) flips between `● Fits your lot ✓` and `▲ Doesn't fit here` with a one-line reason (*"2 ft into the rear setback"*). It's the same PostGIS envelope check the report used — now interactive.
- If a configured price drifts above her earlier estimate, the panel **gently suggests a simpler variant or finish downgrade** (vision principle: honest design, don't let her overcommit).

---

## 5. Motion, states, mobile, a11y
- **Entry transition:** camera eases presentation → ¾ working angle (~1s); envelope blooms from dim to solid; handles fade in. Reverse on exit back to presentation.
- **Model/variant swap:** 350 ms cross-fade, camera locked.
- **Mobile:** right rail → bottom sheet (peek = price + Continue; expand = full options); drag/rotate via touch with larger hit areas; landscape lock for the 3D.
- **Accessibility:** every exterior choice has a non-3D control (steppers, swatches, checkboxes are real form controls); placement has a numeric/cardinal fallback ("nudge 1 ft N/S/E/W"); interior is inherently 2D/text-friendly. Live region announces fit changes ("Now fits — 6 ft from house"). Color never the only signal (red face + text reason).
- `prefers-reduced-motion` → cross-fades instant, camera moves cut.

---

## 6. Exit / handoff
**Continue to financing** carries the fully-configured model (variant, finishes, add-ons, placement, all-in price) forward to Phase 3 — financing estimation, then verification + deposit. Per the vision, **model selection earns the celebration; debt acquisition is sober.** The configurator's emotional peak is the moment she sees the finished, fitted unit sitting correctly in her real yard with her finishes — *that's* hers.

---

## 7. The whole flow, no page breaks
Fly into the yard (presentation) → **Configure** (handles appear on the same model, same spot) → dress the exterior + snap it where it fits → **Interior** tab for finishes → **Step inside** (optional modal) → **Continue to financing**. The only scene change in the entire arc is the optional interior walkthrough — everything else is one continuous Deck.gl canvas, which is exactly why unifying on one engine matters.
