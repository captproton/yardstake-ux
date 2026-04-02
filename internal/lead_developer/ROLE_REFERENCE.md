# System Sam — Lead Developer: Role Reference

> "The beauty of Yardstake isn't in the 3D visuals; it's in the underlying Rails logic that turns physical construction into an immutable ledger."
> — System Sam, Lead Developer

---

## Who He Is

Sam built the platform. All 14 sprints of Oregon Beta implementation exist because of his decisions about Rails 8, PostGIS, the Strategy Pattern, Stripe Connect, and SolidQueue. During Oregon Beta he shifts from builder to operator — maintaining, monitoring, and evolving a production system processing real homeowner money.

His most important Oregon Beta relationship is with Zara. She finds the edge cases in the data. He turns them into failing tests before he turns them into fixes. That loop is how the Digital Twin gets more accurate with every closed transaction.

---

## What Sam Built (Oregon Beta Foundation)

### Track 1 — Digital Twin Engine
- `Parcel` model with PostGIS geometry, SRID mapping, `near_major_transit?()`
- `GeometryValidator` concern — surfaces self-intersections, mismatched SRIDs, null geometries
- `ImportFromShapefileService` / `DownloadAndValidateService` — parcel import pipeline
- Strategy Pattern: `AduCalculator::Strategies::*` — per-jurisdiction Ruby strategy classes encoding ADU rules as testable code
- `FeasibilityScoreService` — geocode → parcel lookup → strategy → envelope → confidence tier

### Track 2 — Feasibility Engine
- Free property check (PropertyCheck model, ProcessPropertyCheckJob)
- Premium $49 feasibility report (FeasibilityReport, PDF generation, Stripe payment)
- Confidence scoring: High / Medium / Low tier assignment

### Track 3 — Marketplace
- Manufacturer onboarding (BuilderProfile, BuilderServiceArea)
- Lead quality scoring and routing (LeadScoringService, LeadRoutingService)
- Commission tracking with Stripe Connect (SaleTransaction, Commission, CalculateCommissionJob)

### Track 4 — UX & Admin
- Hotwire (Turbo + Stimulus) throughout
- Admin namespace: jurisdictions, parcel imports, manufacturers, commissions
- SolidQueue background job infrastructure

---

## What Sam Does During Oregon Beta

### Production Monitoring
Sam watches three things that matter for the 5 validation criteria:

| Signal | Why it matters | Tool |
|---|---|---|
| Parcel import job success rate | Failed imports = missing parcels = missed feasibility queries | SolidQueue / MissionControl |
| FeasibilityScore tier distribution | Unexpected Low spike = data quality issue | Admin::Executive dashboard |
| Stripe webhook reliability | Failed webhook = commission not recorded | Stripe dashboard + logs |

A production incident during Oregon Beta is not a technical failure — it is a threat to Criteria #1 through #5. Sam treats uptime as a validation metric.

### Zara's Technical Interlocutor
Sam is Zara's entry point to the codebase. She needs to understand:
- How strategy classes work and where to find the one for her jurisdiction
- What `rulebook_status` fields mean on the Jurisdiction model
- Why a parcel is landing in Medium instead of High (tracing through FeasibilityScoreService)
- What a geometry error message means and whether it requires her intervention or his

Sam does not need to do Zara's research work. He does need to make sure she can do it without hitting technical blockers.

### New Jurisdiction Tooling (Admin::ZoningResearch)
As Zara expands to additional Oregon jurisdictions, Sam builds the admin infrastructure she needs:
- `Admin::ZoningResearch` namespace (per ADR-002)
- `ParcelFlag` model and review queue
- `AccuracyAuditRecord` for closing the accuracy feedback loop
- `Jurisdiction.research_status` and `rulebook_status` fields

This work is Phase B of ADR-002 implementation.

### Edge Case Triage from Production
The first 20 sales will generate edge cases nobody anticipated:
- A parcel whose geometry is valid but whose lot area calculation returns zero
- A jurisdiction whose ordinance changed mid-beta (Zara finds it; Sam updates the strategy)
- A homeowner address that geocodes to the street centerline instead of the parcel

Sam's discipline: every production bug becomes a failing RSpec test before it becomes a fix. This is how the test suite grows with the product rather than lagging behind it.

---

## Sam's Relationship to the Strategy Pattern

The Strategy Pattern is the bridge between Zara's research work and the platform's calculations. Each jurisdiction strategy class (`PortlandOregonStrategy`, `EugeneOregonStrategy`, etc.) implements seven methods:

| Method | Encodes |
|---|---|
| `calculate_setbacks()` | Rear, side, front setback by zone class |
| `max_height()` | Height limit in feet |
| `max_lot_coverage()` | Percentage; whether ADU counts against it |
| `max_unit_size()` | Fixed cap or % of primary dwelling |
| `parking_required?()` | Boolean + transit proximity logic |
| `permit_type()` | Ministerial / conditional / discretionary |
| `near_major_transit?()` | Parking waiver trigger; requires GTFS data |

Zara researches and specifies the values. Sam writes the tests first, then the implementation. Neither can do the other's job — Zara cannot write the Ruby and Sam cannot read the ordinances.

---

## What Sam Does NOT Own

- Zoning research (Zara owns it — Sam's job is to make her work expressible in code)
- Manufacturer relationships (Victor owns it)
- Growth and content (Val; deferred for Oregon Beta)
- Commission accounting (Larry; deferred post-Series A)

If Sam is spending time on business development or content strategy, something is wrong with the team structure.

---

## Key Architectural Decisions to Preserve

Sam made these decisions deliberately. They should not be reversed without understanding the reasoning:

| Decision | Rationale |
|---|---|
| Rails 8 monolith, no microservices | Velocity at Oregon Beta scale; microservices complexity inappropriate for <20 sales/month |
| PostGIS in PostgreSQL, not a separate GIS service | Single database to reason about; spatial queries co-located with business logic |
| Strategy Pattern per jurisdiction | Each city's rules are isolated and testable independently; adding a new city doesn't touch existing ones |
| SolidQueue over Sidekiq | No Redis dependency; simpler ops for a team of one during Oregon Beta |
| Pundit for customer-facing authorization, before_action gates for admin | Account-scoped permissions (Pundit) vs. system-role permissions (before_action) are different problems |

---

## Supporting Files

| File | Purpose |
|---|---|
| `_system_sam.html` | Persona journey — five-stage visual narrative |
| `ROLE_REFERENCE.md` | This file |
| `../zoning_researcher/ROLE_REFERENCE.md` | Zara — Sam's primary operational collaborator |
| `../../docs/architecture/ADR-002-admin-authorization-architecture.md` | Admin structure Sam implements |
| `../../docs/architecture/ADU_CALCULATOR_STRATEGY_ARCHITECTURE.md` | Strategy Pattern Sam built |
| `../../app/controllers/admin/base_controller.rb` | Existing admin gate pattern |
