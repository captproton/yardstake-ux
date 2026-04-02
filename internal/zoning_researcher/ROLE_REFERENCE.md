# Zoning Zara — Research Lead: Role Reference

> "Anyone can download a shapefile. The moat is knowing which fields are wrong, which rules expired, and which exemption nobody told the GIS department about."
> — Zoning Zara, Research Lead

---

## Who She Is

Zara is Yardstake's **first operational hire** — not a developer, not a salesperson, but the person who makes every other part of the platform true. Her title is Research Lead, but her actual function is closer to a **data cartographer and regulatory archaeologist**. She sits between the raw chaos of public government data and the clean, structured facts that the Digital Twin needs to issue a defensible feasibility answer to a homeowner.

---

## Why She Exists at All

Yardstake's core competitive advantage is not its UI, its marketplace, or its manufacturer relationships. It is the **accuracy of its zoning intelligence**. Competitors can copy a UI. They cannot copy years of hand-verified, transaction-tested zoning data across dozens of Oregon jurisdictions. That accuracy is the moat.

But that moat doesn't build itself. Every jurisdiction Yardstake enters involves:

- A Shapefile in an unknown coordinate reference system
- A PDF ordinance that contradicts the Shapefile
- A city website last updated years ago
- A planner who doesn't return calls
- Overlay zones that exist nowhere in digital form
- Rules that changed via memo and were never codified

Zara is the person who resolves all of that before a single homeowner ever sees a result. Without her, the platform outputs confident-sounding wrong answers — and wrong answers in ADU permitting translate directly to wasted homeowner money and destroyed trust.

---

## The Five-Stage Journey

### Stage 1: PDF Purgatory (Day 0)

When a new jurisdiction is assigned — say, Eugene, OR — Zara receives what she calls a "data packet": a Shapefile from the county GIS department (possibly in an obscure projection like SRID 2152), a 200-page ordinance PDF, and whatever the city's website shows. These three sources almost never agree. In the Eugene example, the Shapefile says 40% lot coverage and the PDF says 50%.

Her first job is not to pick one — it's to find the authoritative source and document why the others are wrong. This stage has no automated tooling support. It is pure research: cross-referencing Oregon state statutes, calling planners, reading city council meeting minutes where ordinance amendments were approved but never reflected in the official PDF.

### Stage 2: Jurisdiction Intake (GeometryValidator Pipeline)

Once Zara has a clean Shapefile and knows its correct CRS, she runs it through the platform's GeometryValidator concern. This surfaces geometric anomalies that would corrupt calculations downstream:

- Self-intersecting polygons (94 found in Eugene's initial import)
- Parcels with mismatched SRIDs (12 found)
- Null geometries
- Impossibly small or large parcels (data entry errors)

She resolves these — sometimes by reprojecting, sometimes by running the auto-repair function, sometimes by going back to the source and requesting a corrected export. Only after this validation pass does she commit the batch. "Eugene is now in the database" is the outcome of this stage — 112,430 parcels with clean, consistent geometry indexed against the correct coordinate system.

**Tooling**: `jurisdiction_intake.html` — four-step wizard: attach data sources → geometry validation with auto-repair → field mapping → commit summary.

### Stage 3: The Rulebook (Strategy Pattern Coding)

This is Zara's most intellectually demanding work. She reads the ADU ordinance line by line and translates it into code — specifically, into the Ruby strategy pattern that the platform's feasibility engine uses. Each jurisdiction gets its own strategy class (e.g., `EugeneOregonStrategy`) with a defined set of methods:

| Method | Purpose |
|---|---|
| `calculate_setbacks()` | Rear, side, and front setback by zone class |
| `max_height()` | Numeric limit and whether measured to ridge or plate |
| `max_lot_coverage()` | Percentage allowed; whether ADU square footage counts |
| `max_unit_size()` | Fixed cap or percentage of primary dwelling, whichever is less |
| `parking_required?()` | Boolean, with transit proximity logic |
| `permit_type()` | Ministerial, conditional use, or full discretionary review |
| `near_major_transit?()` | Parking waiver trigger; requires GTFS transit stop data |

Integration tests are written first, following TDD discipline. All green before a jurisdiction goes live.

**Tooling**: `ordinance_editor.html` — split panel with highlighted ordinance source on the left, editable rule cards on the right. Filling all fields for a rule marks it "Coded." Run Tests button fires a simulated test run.

**Current rulebook status by jurisdiction (as of March 2026):**

| Jurisdiction | Coded / Total | Pending |
|---|---|---|
| Portland | 6 / 7 | `near_major_transit?()` |
| Eugene | 7 / 7 | — |
| Salem | 6 / 7 | `near_major_transit?()` |
| Bend | 5 / 7 | `near_major_transit?()`, `permit_type()` |
| Medford | 6 / 7 | `near_major_transit?()` |

### Stage 4: Confidence Calibration

Once a jurisdiction is live and taking feasibility queries, Zara monitors how those queries distribute across the three-tier confidence model:

**High (80–100%)**: Full geometry, confirmed zoning, no overlay conflicts. Automated answer delivered directly to homeowner.

**Medium (50–79%)**: Overlay zone present, partial geometry, or ambiguous zoning text. Result shown with caveat. Human expert review triggered before homeowner commits a token.

**Low (0–49%)**: Historic preservation district, FEMA flood zone AE/AH, conflicting field values, or data stale more than 18 months. No automated answer. Routed to Zara or a licensed planner before anything is surfaced.

The calibration work is iterative. Eugene's first 200 queries showed 68% High / 22% Medium / 10% Low. When project #123 hit an unexpected Historic Preservation Zone buffer rule (classified Medium, actually required a variance), Zara narrowed the Medium-to-Low threshold. The model is not static — it is tuned continuously against what actually happens when houses get built.

**Tooling**: `parcel_review.html` — flagged parcels queue, filterable by confidence tier and jurisdiction. Resolve as: Confirm High / Keep Medium / Escalate to Planner / Flag Unresolvable. Auto-advances to next pending parcel on resolution.

### Stage 5: The Feedback Loop (Accuracy Audit)

After transactions close — meaning a homeowner actually built an ADU — Zara runs an accuracy audit: did the predicted confidence tier match what actually happened?

**Current results (March 2026):** 12 closed transactions, 11 predictions confirmed correct. **Accuracy rate: 91.7%.** The platform's validation gate requires 90%+ accuracy in the High confidence tier before any jurisdiction goes live. Yardstake is above that gate.

The one miss (#123, Eugene, Medium-predicted): an HPZ buffer rule existed in a 2018 city memo but was never reflected in the ordinance PDF or Shapefile attributes. Zara's response: find the memo, update the rule, narrow the threshold. The Digital Twin gets measurably smarter with each house that lands.

**Tooling**: `dashboard.html` — Accuracy Audit tab. Closed-transaction table with predicted tier, actual outcome, match/miss indicator, and notes. 91.7% headline displayed prominently.

---

## Her Dashboard — The Jurisdiction Research Hub

**File**: `dashboard.html`

Four tabs:

**1. Jurisdiction Pipeline** — Master status view. 8 Oregon jurisdictions tracked. Columns: name/state, status (Active / In Progress / Backlog), parcel count, data quality progress bar, High/Med/Low confidence split, last updated, chevron to open slide-over detail drawer.

**2. Confidence Model** — Three tier cards with score ranges, descriptions, and specific criteria. Below: stacked bar chart comparing confidence distribution across all five active jurisdictions. Pattern: older, more thoroughly researched jurisdictions have higher High percentages.

**3. Accuracy Audit** — Closed-transaction ground truth table. 12 rows. Jurisdiction, predicted tier, actual outcome, match indicator, notes. The one red row (#123) highlighted subtly.

**4. Data Queue** — Incoming jurisdiction requests from product, sales, or growth, with source attribution, priority, estimated effort, and status notes. Teal callout at bottom: "Each new jurisdiction requires 40–80 hours of research, validation, and rule coding before it goes live. This is not a light software layer — it is the moat."

**Slide-Over Drawer** — Clicking any Active jurisdiction row opens a 480px panel: At a Glance stats (data quality %, High confidence %, accuracy rate), confidence distribution bar scoped to that jurisdiction, rulebook checklist, last 5 feasibility queries, and Quick Action links to Ordinance Editor / Parcel Review / Intake Record.

---

## Strategic Importance

Zara sits at the intersection of data integrity and trust. Every other persona depends on her being right:

- **Backyard Bill** trusts the green checkmark. A miscoded setback means he plans for an ADU that can't be permitted.
- **Design Diane's** drawings are dimensioned off Zara's setback numbers. Wrong data produces unbuildable plans.
- **Underwriter Ursula's** risk models assume the confidence tiers are calibrated. Under-flagged Medium tier means lenders fund unbuildable projects.
- **Manufacturer partners** (5-manufacturer validation gate) need reliable feasibility signals to price quotes. Inaccurate data breaks the economics of the whole marketplace.

Zara is also the principal check on **expansion speed**. The Data Queue is intentionally a bottleneck. Each jurisdiction she certifies to 90%+ accuracy is a moat brick. Rushing her work to hit an expansion target is how the confidence model breaks — and that destroys the product's reason to exist.

---

## Supporting Files

| File | Purpose |
|---|---|
| `_zoning_zara.html` | Persona journey — five-stage visual narrative |
| `dashboard.html` | Primary operational interface (Jurisdiction Research Hub) |
| `jurisdiction_intake.html` | Four-step intake wizard for new jurisdictions |
| `ordinance_editor.html` | Split-panel ordinance-to-rulebook coding tool |
| `parcel_review.html` | Flagged parcel review and confidence resolution queue |
| `ROLE_REFERENCE.md` | This file — prose role definition and context |
| `../CLAUDE_SUPPORT_ZONING_RESEARCHER.md` | How Claude AI supports this role |
