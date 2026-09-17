# Improving the 3D Presentation to the Homeowner — Using Data We Already Have

How to get more out of the data already in hand (PostGIS parcels, building footprints, `EnvelopeCalculation`, zoning setbacks, ADU catalog dimensions) plus free streamable USGS 3DEP COPC LiDAR — without acquiring new data or requiring site access.

---

## The constraint that shapes everything

The two pipelines (per [`adr/0001-two-3d-pipelines.md`](../../../../dev/marketplace_platform_20251031_132510/docs/adr/0001-two-3d-pipelines.md)) have opposite strengths:

- **Google Photorealistic 3D Tiles already contain the real house, trees, and terrain** — baked from aerial capture. You can't *relight* a photogrammetry mesh convincingly, so dynamic sun/shadow does **not** belong here. The presentation win is **correct placement + annotation**, not adding geometry.
- **The LiDAR/COPC configurator is a scene you build** — heights, terrain, trees, shadows are all things *you* control from data. This is where the analytically impressive work lives.

---

## Highest-leverage improvements, ranked

### 1. Sun & shadow study — the standout (configurator scene)
Biggest emotional + decision win, and needs **zero new data**: sun position (lat/long + date/time, e.g. SunCalc) plus heights you already have. Show the ADU's shadow on the main house, garden, and neighbor's yard at **9am / noon / 5pm on Jun 21 and Dec 21**.
- *Data:* parcel lat/long, ADU height from catalog, existing-house height from LiDAR Class 6.
- *Why it matters:* answers the worry homeowners actually voice — *"will it shade my garden / will my neighbor object?"* — which a photoreal flythrough never addresses.
- *Where:* a Three.js/Deck.gl scene where you own the directional light. Not the Google mesh.

### 2. True existing-house massing from LiDAR (configurator)
Replace the guessed extrusion height with **LiDAR Class 6 max-Z** (actual ridge height) and **Class 2 (ground)** for the real pad elevation. The ADU then sits next to a correctly-proportioned house on correctly-sloped ground — believability jumps, and it feeds #1.

### 3. Terrain-clamped, slope-aware placement (configurator)
Clamp the ADU to real grade from the LiDAR ground surface. If the yard slopes, *show* the step/foundation condition.
- *Why it matters:* slope is a real cost driver (retaining, foundation). Showing it honestly builds trust and pre-qualifies the lead — matches the "feasibility tool" framing in the ADR.

### 4. Live setback & clearance annotations (both pipelines)
Draw dimension lines computed from PostGIS: *"12 ft to rear fence · 6 ft to house · 5 ft side setback."* `ST_Distance` between the placed ADU footprint and the boundary/footprint geometry already stored.
- *Why it matters:* converts "pretty" into "I believe it fits." Nearly free — the geometry already exists.

### 5. Confidence-colored buildable envelope + in-place model swap (both)
`EnvelopeCalculation` already carries confidence scores. Render the envelope as a glowing box colored **green/amber/red** by that confidence, label it with real dimensions, and animate the matched ADU snapping inside it. Let the carousel swap GLBs **with the camera locked**, so the homeowner compares 2–3 models *in the same spot*.

### 6. Tree-canopy proxies from LiDAR (configurator)
Drop simple canopy volumes where LiDAR Classes 3–5 indicate trees. Context for the homeowner, clearance/root-zone flags for feasibility, and shade casters for the #1 shadow study.

---

## A pragmatic near-term move

The presentation doc flags **GLB sourcing as the highest-risk item** — photoreal models may not exist for every catalog ADU yet. Don't wait on them:

> **Ship a "massing-block" MVP first.** Extrude each ADU from its catalog `width × depth × height` as a clean, branded block. That instantly gives correct **scale, placement, heading, envelope fit, dimension labels, and shadow studies** — everything above except photorealism. Swap in detailed GLBs per model as they're produced, with no architecture change.

---

## Recommended build order (all from data in hand)

1. **Massing-block + envelope + dimension annotations** in the configurator scene — correct, trustworthy, no GLB dependency.
2. **Sun/shadow study** on top of it — the differentiator.
3. **LiDAR true-heights + terrain clamp** for believability, then **GLBs** for photoreal polish.

This turns the 3D from a "spinning model" into a *feasibility-and-feeling* tool, every step powered by data already in hand (parcels, footprints, envelope, zoning setbacks, catalog dimensions) or streamable for free (USGS 3DEP COPC).
