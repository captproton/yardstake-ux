# The Matched-Models Presentation — Full UI/UX Spec

The "matched-models" moment in Annie's journey — the screen the product is engineered around ("show the dream first"). Grounded in the two-pipeline architecture (Google 3D Tiles presentation + COPC LiDAR configurator), the data-driven overlays (buildable envelope, dimension annotations, sun/shadow study), and Annie's anxiety profile (cost-certainty fear, needs reassurance, no manipulative celebration).

Companion mockup: [`matched_models_presentation.html`](./matched_models_presentation.html).

---

## 0. Design language (the emotional frame)

Tuned to **lower an anxious homeowner's heart rate**, not raise it.

- **Canvas:** edge-to-edge 3D scene with a subtle dark vignette so the photoreal neighborhood pops in center. Frame is near-black `#0E1116`.
- **Chrome:** glassmorphic panels — `backdrop-blur(20px)`, ~8% white fill, 1px hairline at 12% white, 16px radius. Glass laid over her backyard, not a dashboard bolted on.
- **Accent:** one warm "stake" amber-green, used *only* for the primary action and "best match" ribbon. Scarcity = intention.
- **Type:** large and humane. Model name 28px, price 22px, body 15px, annotations 13px tabular figures.
- **Motion:** slow, eased, physical. Camera moves like a drone with mass. No confetti here — celebration is reserved for the *act of choosing* (principle #4).

---

## 1. Entry & conditional pacing

Reached from the feasibility report by tapping a matched model, or auto-rendered on **high confidence**.

- **High confidence** → straight into the cinematic reveal.
- **Marginal feasibility** → a quiet pre-roll card first: *"Your lot is tighter than most — here's what genuinely fits."* Then only fitting models. Honesty before desire.

Desktop auto-loads 3D. **Mobile** shows 2D fallback first with `▶ View my backyard in 3D` opt-in (RAM/heat).

---

## 2. The 6-second cinematic reveal (frame-by-frame)

*Here is your home → here is the space → here is the house in it → stand next to it.*

- **t=0.0s — Orientation.** Top-down satellite. Pulsing dot on her parcel. *"123 Cherry St — let's look at your backyard."*
- **t=1.0s — The world tilts up.** Camera to 67° oblique, range ~120 m. Photoreal neighborhood mesh resolves: her house, real trees, mountains. The gasp: *that's my house.*
- **t=2.0s — The space declares itself.** Translucent **buildable-envelope volume** rises from the grass like water filling a glass, extruded to real envelope height. Label tracks top face: *"Buildable area: 24 × 30 × 18 ft."*
- **t=3.0s — The dream lands.** Matched ADU GLB (or procedural massing block) fades + drops the last inches into the envelope, terrain-clamped, correctly scaled and oriented (door to street frontage per `PlacementService`).
- **t=4.5s — Drive-up.** Camera drops to ~3 m AGL, eye-line on the back patio, ADU framed against her real existing house.
- **t=6.0s — The panel arrives.** Right info panel slides in (calm slide, not pop) with name, manufacturer, all-in price, amber CTA. Camera rests; faint parallax keeps it alive.

Skippable (`Skip ⏭` at t=0.5s). Respects `prefers-reduced-motion` → hard-cut to the t=6 frame.

---

## 3. Resting interactive state (wireframe)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ◂ 123 Cherry St    [● High confidence ⓘ]                      ⤢  ⟳  ?       │
├────────────────────────────────────────────────────────────────────────────┤
│                                          ┌──────────────────────────────┐    │
│              ☀ sun glow                  │  Maplewood 600                │    │
│        ╔═══════════════╗                 │  by Pacific Modular           │    │
│      ┌─╨───────────────┐                 │  600 sq ft · 1 bd · 1 ba       │    │
│      │  ┌───────────┐  │← 12 ft to fence │  From  $129,000               │    │
│   ▣  │  │   ADU     │  │                 │  All-in ~$186,000  ⓘ          │    │
│ house│  └───────────┘  │                 │  ┌ Box ┬ Dirt ┬ Red Tape ┐    │    │
│      └──╥────────────┘                   │  └$129k┴ $41k ┴  $16k ────┘    │    │
│      6 ft to house                       │  [ ✦ Start My Project ]        │    │
│                                          │  ♡ Save   ⤓ Share   ▦ Adjust   │    │
│                                          └──────────────────────────────┘    │
│   ☀───────────●─────────  9a ·· noon ·· 5p  | Jun 21 ▾   (shadow study)     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                                         │
│  │Maplewood│ │ Cedar   │ │ Aspen   │   ◂ matched-model carousel ▸           │
│  │ ✓ best  │ │  240    │ │ Studio  │                                         │
│  │ $186k   │ │ $204k   │ │ $221k   │                                         │
│  └─────────┘ └─────────┘ └─────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component-by-component

**a. 3D canvas + camera.** Orbit/zoom/pan, but **leashed** to a dome around the parcel (never lost in the void; eases back if she drifts). View presets `Front · Side · Top · Drive-up` ease over ~1.2s — safe, flattering angles remove the "operate a 3D app" burden. `⟳` resets; `?` one-time coachmark.

**b. Buildable-envelope volume.** Persistent but **dimmable** (~8% at rest, blooms to 22% on Adjust/hover). Truth, not decor: footprint = `parcel − existing_footprint − setbacks` (PostGIS), height = zoning limit. Over-limit face glows red + inline note: *"This model is 2 ft taller than your zone allows — Cedar 240 fits."*

**c. Dimension & setback annotations.** Leader lines + tabular labels (*"12 ft to rear fence," "6 ft to house," "5 ft side setback"*) via `ST_Distance`. Fade in only after camera settles; auto-declutter on overlap (collapse to tappable dot). Group toggle (ruler icon).

**d. Sun/shadow study scrubber.** Time-of-day slider; sun glyph arcs; directional light + cast shadow update live on house/garden/fence. Date dropdown pre-set to `Jun 21` / `Dec 21` / Today. First-use copy: *"Drag to see how the shadow moves — handy if you've got a garden back here."* Configurator-scene only (can't relight a photogrammetry mesh honestly).

**e. Carousel (in-place swap).** 2–3 cards; active lifts + amber underline. Tapping swaps the model **camera-locked** — cross-fade in the same spot; envelope/annotations recompute. `✓ Best Match` ribbon on primary. Card price enables affordability self-filter with zero financing friction.

**f. Info panel & price (Annie's #1 fear).** Range + all-in, never a lone scary number. **Box / Dirt / Red Tape** mini-bar inline + tappable; each opens a *why* tooltip (Dirt is slope-aware from the same LiDAR terrain that grounds the model — visual and price agree).

**g. Confidence pill.** Calm `● High confidence ⓘ`, green/amber by `EnvelopeCalculation`. `ⓘ` explains what confidence means and what would raise it. Honesty as a feature.

**h. "Step inside" (future splat).** `▶ Step inside` chip → modal Gaussian-splat walkthrough of the *built* manufacturer model (separate showroom context). Deferred per roadmap.

**i. Primary CTA `✦ Start My Project`.** Only amber element, full-width. Opens a lightweight sheet (email, optional phone, optional note) — **not** a payment. On submit: earned, restrained celebration (soft warm rim-light on the ADU) + *"Fiona will reach out within 24 hours,"* then the pre-filled account-save nudge.

---

## 5. Microcopy & tone
First-person-plural and reassuring (*"let's look," "here's what fits"*). Numbers always carry context (*"all-in, including the crane and permits"*). No urgency timers, no "3 people viewing," no dark patterns. Errors gentle and non-blaming.

## 6. Motion & transitions
Camera 800–1200 ms `easeInOutCubic`; rest parallax. Model swap 350 ms dissolve + 6 cm settle. Panels 250 ms slide+fade. Envelope bloom 200 ms. All gated by `prefers-reduced-motion`.

## 7. States
- **Loading:** instant t=0 satellite frame + thin amber hairline, *"Building your backyard…"* Reveal fires only when tiles+GLB ready.
- **No-coverage fallback:** silent 2D Mapbox satellite + isometric SVG ADU + envelope polygon, same `Match` data/panel/CTA. *"3D isn't available for your street yet — here's the overhead view."*
- **Error:** procedural massing block stands in for a failed GLB; user may never know.
- **Empty / nothing fits:** envelope alone + *"Your buildable area is compact — let's talk options"* → concierge.

## 8. Mobile
2D fallback + `▶ View in 3D` opt-in. Landscape lock + rotate coachmark. Big touch targets; carousel = swipe filmstrip; info panel = bottom sheet (peek = price+CTA, expand = full breakdown); sun scrubber on the sheet's top edge; persistent pinned **Start My Project** bar.

## 9. Accessibility
Fully usable without 3D (2D fallback is the a11y baseline). Every overlay has a text equivalent (expandable "Details": dims, all-in + breakdown, all setbacks, fit verdict). Keyboard-reachable controls; presets are buttons. Focus rings; contrast ≥ 4.5:1 (text scrim behind glass). Color never the only signal (red face + text note; pill color + word).

## 10. Handoff to configurator
`▦ Adjust` eases to a ¾ working angle, then navigates to the **COPC + Deck.gl configurator** with model + placement + envelope in state — lands on the same model, same spot, same framing, now with drag/rotate/resize/roof-pitch + survey-grade LiDAR ground. Continuity makes the pipeline switch invisible.

## 11. The emotional arc
**See my house → see the space → see the house *in* the space → stand next to it → trust the number → choose it.** Annie sees her own backyard with the ADU in it — correctly sized and shadow-true — before she reads a single dollar figure, and every overlay is a real fact from data already held.
