# Yardstake Persona Index

**Last updated:** March 25, 2026
**App state:** Oregon Beta implementation complete (14/14 sprints). Launch target: Q3 2026.
**Guidance documents:** All 7 active personas have individual `LAUNCH_GUIDANCE.md` files covering now through Day 100 (October 9, 2026).

This document is the master index for all personas in the `user_experience/` directory. It answers four questions for each persona: who they are, when they activate, which validation criteria they affect, and what codebase surfaces they depend on.

---

## Activation Phases

| Phase | Trigger | Timeline |
|---|---|---|
| **Pre-Launch** | Now — before Oregon Beta opens | Now → July 2026 |
| **Oregon Beta** | Platform open to real homeowners and manufacturers | Q3 2026 (July–Sept) |
| **Decision Gate** | Go/No-Go for Series A | Q4 2026 |
| **Post-Series A** | Funding secured, West Coast expansion begins | 2027+ |

---

## External Personas (Platform Users)

### Referring Rachel — Channel Partner (Realtor / Lender / ADU Consultant)

**Who:** Oregon professional with ongoing homeowner client relationships. Exists in three variants: Realtor Rachel (15–30 transactions/year), Lender Rachel (ADU-focused lender), or Consultant Rachel (permitting consultant / housing advocate). Refers Annie-type homeowners to Yardstake's free check because it makes her look good and helps her close her own deals.

**Activation:** Oregon Beta — Victor activates 3–5 Rachel partners before Day 1. Requires no platform code changes: a referral link (`?ref=name`), a one-page PDF brief, and a 30-minute Victor demo.

**Validation criteria:** #2 (free→paid conversion multiplier), #4 (ADU sales multiplier). Rachel is not a direct validation metric — she is a pipeline that drives Annie volume at near-zero acquisition cost.

**Codebase surfaces:**
| What | Notes |
|---|---|
| `?ref=` UTM param on free check URL | Val configures in Google Analytics. No code change. |
| Weekly referral attribution report | Val produces manually from GA during Oregon Beta. |
| Phase 2: `GET /partners` | Future: self-serve referral link generator + conversion dashboard. ~8–12 hrs post-Series A. |

**The activation ordering matters:** Mike (manufacturers) must be Verified Partners before Rachel is activated, and Rachel must be activated before Annie arrives on Day 1. Rachel sending Annie to a report with zero matched manufacturers destroys Rachel's credibility.

**Documentation:**
- Journey: `partner/_referring_rachel.html` ✅ created March 25, 2026
- Launch guidance: `partner/LAUNCH_GUIDANCE.md` ✅ created March 25, 2026 — three variants, Victor's activation script, Zillow parallel, target partner list, gap dependencies

---

### Anxious Annie — Oregon Homeowner / Buyer

**Who:** Portland-area homeowner, 5,000+ sq ft lot, owned 5+ years, has been researching ADUs for months without a confident answer.

**Activation:** Oregon Beta — she is the core top-of-funnel user. Every platform feature from free check through purchase is built for Annie.

**Validation criteria:** #1 (accuracy she can trust), #2 (free→paid conversion), #4 (ADU sales), #5 (revenue)

**Codebase surfaces:**
| Route | Controller | Notes |
|---|---|---|
| `GET /property_checks/new` | `PropertyChecksController` | Free feasibility check entry |
| `POST /property_checks` | `PropertyChecksController` | Triggers geocode → Digital Twin lookup |
| `GET /property_checks/:id` | `PropertyChecksController` | High/Medium/Low result |
| `GET /feasibility_report_payments/new` | `FeasibilityReportPaymentsController` | $49 Stripe payment |
| `GET /feasibility_reports/:id` | `FeasibilityReportsController` | Premium report + matched models |
| `GET /yardstake/analysis` | `YardstakeController` | Analysis landing |
| `GET /search` | `SearchController` | Address/parcel search |

**Documentation:**
- Journey: `buyer/_anxous_annie.html` ✅ updated Mar 7, 2026
- Dashboard: `buyer/dashboard-phase0.html` ✅ updated Mar 7, 2026
- Launch guidance: `buyer/LAUNCH_GUIDANCE.md` ✅ Mar 7, 2026 — pre-launch dependencies, full journey (free check through sale), financing gap, site GC gap, directory experience by listing state, phase-by-phase experience through Day 100

**Gaps:** GAP-003 ($49 refund credit not wired) affects Annie's purchase funnel.

**Claim layer impact on Annie's experience:** Unclaimed and partially-activated manufacturers must never appear in Annie's matched results inside the $49 report — only `match_eligible?` manufacturers appear there. In the ADU home directory (if built), Annie may browse all listing states, but the inquiry button is hidden on non-verified profiles and an in-page message directs her back to the free check funnel. Visual distinction by state:

| State | Directory badge | Inquiry button | Annie's CTA |
|---|---|---|---|
| Unclaimed | "Unverified" (grey) | Hidden | "Run a free check to find Verified Partners" |
| Claimed — Incomplete | "Activation Pending" (yellow) | Hidden | "Run a free check to find Verified Partners" |
| Verified Partner | "Verified Partner" (green) | Visible | Normal inquiry flow |

---

### Modular Mike — ADU Manufacturer / Supplier

**Who:** Oregon-based prefab/modular ADU manufacturer. Quality product, poor digital presence. Victor closes him personally. He joins commission-only — no upfront cost.

**Activation:** Pre-Launch — Victor needs 5 manufacturers signed before Oregon Beta opens. Mike's onboarding must be complete before Annie can be matched to his catalog.

**Validation criteria:** #3 (5+ manufacturer partnerships), #4 (ADU sales), #5 (revenue)

**Activation states** (see `docs/MANUFACTURER_ACTIVATION_STATES.md` for full spec):

| State | `BuilderProfile` condition | Match eligible? | Mike's experience |
|---|---|---|---|
| Unclaimed | `claimed: false` | No | No dashboard. Public listing with "Claim" CTA. |
| Claimed — Incomplete | `claimed: true`, missing Stripe / approval / listings | No | Dashboard with activation progress bar. Blurred lead inbox preview. Re-engagement emails on days 0, 3, 7, 14. |
| Verified Partner | `match_eligible?` returns true | Yes | Full dashboard. Live lead inbox. Commission reporting. |

**`match_eligible?` requires all of:**
- `manufacturer: true`
- `claimed: true`
- `approved?` (Victor set `admin_approved_at`)
- `commission_agreement_accepted?`
- `stripe_connected?`
- 2+ active `homes`
- At least one `manufacturer_service_area` (Oregon city)

**New claim-layer codebase surfaces:**
| Route | Controller | Notes |
|---|---|---|
| `GET /manufacturers/claim/new` | `Manufacturers::ClaimsController` | Claim initiation — email verification |
| `GET /manufacturers/claim/verify` | `Manufacturers::ClaimsController` | Token verification, sets `claimed: true` |

**Existing codebase surfaces:**
| Route | Controller | Notes |
|---|---|---|
| `GET /manufacturers/registration/new` | `Manufacturers::RegistrationsController` | 5-step onboarding wizard |
| `GET /manufacturers/registration/pending` | `Manufacturers::RegistrationsController` | Holding page awaiting approval |
| `GET /manufacturers/dashboard` | `Manufacturers::DashboardController` | Lead inbox, metrics; shows activation progress bar in State 2 |
| `GET /manufacturers/homes` | `Manufacturers::HomesController` | ADU product listings |
| `GET /manufacturers/stripe/connect` | `Manufacturers::StripeConnectController` | Stripe Express onboarding |
| `GET /manufacturers/commissions` | `Manufacturers::CommissionsController` | Commission reporting |
| `GET /admin/manufacturers` | `Admin::ManufacturersController` | Victor's queue — now four tabs: Verified / Incomplete / Unclaimed / Pending |

**Documentation:**
- Journey: `builder/_modular_mike.html` ✅ updated Mar 7, 2026
- Dashboard: `builder/Builder Dashboard02.html` ✅ updated Mar 7, 2026
- Activation states spec: `marketplace_platform/docs/MANUFACTURER_ACTIVATION_STATES.md` ✅ Mar 7, 2026
- Launch guidance: `builder/LAUNCH_GUIDANCE.md` ✅ Mar 7, 2026 — three activation states, outreach demo and objection playbook, site GC preferred partner field, showrooming and commission agreement, phase-by-phase through Day 100

**Gaps:** GAP-001 (submission notification unwired; Victor doesn't know when Mike submits). Claim layer not yet built — see `LAUNCH_100_DAY_PLAN.md` pre-launch Sam schedule (April–May).

---

### Backyard Bill — Site General Contractor

**Who:** Local Oregon GC who handles site prep, foundation, utility stubs, and crane coordination for ADU installations.

**Activation:** Post-Series A — Bill is a construction management persona. Oregon Beta validates the marketplace model (match + transact). On-site coordination tooling is a Phase 2 build.

**Validation criteria:** None directly. Supports #4 (sales completion) in Phase 2.

**Codebase surfaces:** None in Oregon Beta. Field interface is a future build.

**Documentation:**
- Journey: `site_gc/_backyard_bill.html` — v1, not updated (Phase 2 persona, not priority)
- Dashboard: `site_gc/field_interface.html` — v1

---

### Design Diane — Architect

**Who:** Oregon architect who handles permit drawings and site plans for ADU projects.

**Activation:** Post-Series A — like Bill, Diane enters the picture post-transaction during permitting. Oregon Beta does not include permit management tooling.

**Validation criteria:** None in Oregon Beta.

**Codebase surfaces:** None in Oregon Beta.

**Documentation:**
- Journey: `architect/_design_diane.html` — v1, not updated (Phase 2 persona)

---

### Underwriter Ursula — ADU Lender

**Who:** Lender or underwriter financing the ADU purchase. Needs permit status, project milestones, and appraisal data.

**Activation:** Post-Series A — financing integration is a Phase 2 feature. Oregon Beta homeowners arrange their own financing.

**Validation criteria:** None in Oregon Beta. Supports #5 (revenue at scale) in Phase 2.

**Codebase surfaces:** None in Oregon Beta.

**Documentation:**
- Journey: `underwriter/_underwriter_ursula.html` — v1, not updated (Phase 2 persona)
- Dashboard: `underwriter/lender_milestones.html` — v1

---

### Legal Clara — Real Estate Attorney

**Who:** Attorney handling title, easements, and deed restrictions that affect ADU eligibility.

**Activation:** Post-Series A — legal integration is not an Oregon Beta feature.

**Validation criteria:** None in Oregon Beta.

**Codebase surfaces:** None in Oregon Beta.

**Documentation:**
- Journey: `legal/_clara.html` — v1, not updated (Phase 2 persona)

---

## Internal Personas (Yardstake Team)

### Visionary Victor — Founder

**Who:** Sole decision-maker during Oregon Beta. Owns manufacturer relationships, investor narrative, expansion prioritization, and the 5 validation criteria. The only person who can close manufacturer partnerships.

**Activation:** Pre-Launch and Oregon Beta. Victor is active now.

**Validation criteria:** Owns all 5, directly responsible for #3 (manufacturer partnerships).

**Codebase surfaces:**
| Route | Purpose |
|---|---|
| `GET /admin/manufacturers` | Manufacturer approval queue |
| `GET /admin` | Madmin infrastructure dashboard |
| `GET /admin/commissions` | Commission audit |

**Gaps:** GAP-004 (executive dashboard showing 5 KPIs missing — Victor uses Madmin generic metrics instead).

**Documentation:**
- Journey: `internal/founder/_visionary_victor.html` ✅ updated Mar 7, 2026
- Role reference: `internal/founder/ROLE_REFERENCE.md` ✅ created Mar 7, 2026
- Dashboard prototype: `internal/founder/dashboard.html` — not reviewed
- Launch guidance: `internal/founder/LAUNCH_GUIDANCE.md` ✅ Mar 7, 2026 — manufacturer outreach schedule (starts March 9), claim layer warm outreach, site GC gap, financing gap, Series A thesis, phase-by-phase through Day 100 including Day 100 decision framework

---

### Zoning Zara — Research Lead

**Who:** Zara researches Oregon municipal ordinances, encodes them as jurisdiction strategy specifications, audits feasibility results for accuracy, and flags parcels that need investigation. She is the human engine behind Criteria #1.

**Activation:** Pre-Launch — Zara must be hired and operational before Oregon Beta opens. Without her, the Digital Twin does not improve and Criteria #1 cannot be formally measured.

**Validation criteria:** #1 (90%+ Digital Twin accuracy). Every other criteria depends on the accuracy she maintains.

**Codebase surfaces:** None yet — entirely blocked by GAP-002 (Admin::ZoningResearch namespace not built).

**Gaps:** GAP-002 is the highest-priority pre-launch gap. Zara's entire workflow is off-platform until it is resolved.

**Documentation:**
- Journey: `internal/zoning_researcher/_zoning_zara.html`
- Role reference: `internal/zoning_researcher/ROLE_REFERENCE.md` ✅ created Mar 7, 2026
- Claude support guide: `internal/CLAUDE_SUPPORT_ZONING_RESEARCHER.md` ✅ created Mar 7, 2026
- Dashboard prototype: `internal/zoning_researcher/dashboard.html`
- Tool prototypes: `jurisdiction_intake.html`, `ordinance_editor.html`, `parcel_review.html`
- Launch guidance: `internal/zoning_researcher/LAUNCH_GUIDANCE.md` ✅ Mar 7, 2026 — GAP-002 dependency, strategy class review schedule (EUG/HIL/SAL), parcel data verification, audit cadence, 50-parcel formal audit for Series A data room, California jurisdiction research in Phase 3

---

### System Sam — Lead Developer

**Who:** Sam built the platform and operates it during Oregon Beta. He monitors production, translates Zara's research into strategy class updates, and triages edge cases. Every production bug becomes a failing RSpec test before it becomes a fix.

**Activation:** Active now and throughout.

**Validation criteria:** Supports all 5 through platform reliability. Directly enables #1 via strategy class accuracy.

**Codebase surfaces:** The entire codebase. Key monitoring surfaces:
| Tool | Signal |
|---|---|
| SolidQueue / MissionControl | Parcel import job success rate |
| Admin::Executive dashboard (GAP-004) | Feasibility score tier distribution |
| Stripe dashboard | Webhook reliability |

**Documentation:**
- Journey: `internal/lead_developer/_system_sam.html` ✅ updated Mar 7, 2026
- Role reference: `internal/lead_developer/ROLE_REFERENCE.md` ✅ created Mar 7, 2026
- Launch guidance: `internal/lead_developer/LAUNCH_GUIDANCE.md` ✅ Mar 7, 2026 — week-by-week gap closure schedule (GAP-001 through GAP-011), claim layer implementation (~10 hrs), financing and site GC additions to $49 report, `match_eligible?` predicate, production operations Phase 1, data exports for Series A

---

### Viral Val — Growth Marketer

**Who:** Val owns the free→paid conversion funnel, Oregon SEO content, and the manufacturer referral loop. During Oregon Beta, Victor proxies her role through direct outreach and the existing content infrastructure.

**Activation:** Oregon Beta (proxied by Victor pre-Series A). A contract marketer could activate Val's role at any point using existing platform infrastructure.

**Validation criteria:** #2 (12%+ free→paid conversion).

**Codebase surfaces:**
| Route | Purpose |
|---|---|
| `GET /oregon/:city` | City landing pages (SEO) |
| `GET /articles` | Educational content (11 articles seeded) |
| `GET /pricing` | Report upgrade pricing page |

**Documentation:**
- Journey: `internal/growth_marketer/_viral_val.html` ✅ updated Mar 7, 2026
- Dashboard prototype: `internal/growth_marketer/dashboard.html` — not reviewed
- Launch guidance: `internal/growth_marketer/LAUNCH_GUIDANCE.md` ✅ Mar 7, 2026 — measurement framework (analytics events, correct conversion denominator), email sequences (lead nurture, claim onboarding, post-purchase), claim layer sourcing, city landing pages, financing and site GC content pages, weekly funnel report template, conversion tier analysis, California waitlist

---

### Ledger Larry — CFO / Accountant

**Who:** Larry owns commission reconciliation, revenue reporting, and financial controls post-Series A.

**Activation:** Post-Series A. Commission tracking is automated through Stripe Connect during Oregon Beta — Sam monitors it. Larry takes over at scale.

**Validation criteria:** #5 (revenue) at scale. Not needed to validate it during Oregon Beta.

**Codebase surfaces:** `Admin::CommissionsController`, Stripe dashboard. No dedicated Larry interface.

**Documentation:**
- Journey: `internal/accountant/_ledger_larry.html` — v1, not updated (deferred)
- Dashboard: `internal/accountant/dashboard-tax.html` — v1

---

### Highway Harry — Logistics Lead

**Who:** Harry coordinates crane scheduling, DOT wide-load routing, and delivery logistics for ADU installations.

**Activation:** Post-Series A — Harry is a construction management persona. Not relevant to Oregon Beta marketplace validation.

**Validation criteria:** None in Oregon Beta.

**Codebase surfaces:** None in Oregon Beta.

**Documentation:**
- Journey: `internal_logistics_lead/_highway_harry.html` — v1, not updated (deferred)
- Dashboard: `internal_logistics_lead/dashboard.html` — v1

---

### Splat Steve — 3D / AR Pipeline Specialist

**Who:** Steve builds the Gaussian Splatting pipeline that converts manufacturer video into photorealistic AR models. His work is the "acceleration layer" for Phase 2 — it amplifies the Digital Twin but is not the moat.

**Activation:** Post-Series A — explicitly deferred until Oregon Beta validates all 5 criteria.

**Validation criteria:** None in Oregon Beta. Supports #2 (conversion) and #4 (sales) at scale in Phase 2.

**Codebase surfaces:** None. Luma AI API integration, SolidQueue AR job pipeline — all future builds.

**Documentation:**
- Journey: `internal/3d_artist/_steve_splat.html` ✅ updated Mar 7, 2026 (Phase 2 deferral banner added)

---

## Summary Table

| Persona | Type | Activation | Criteria | Docs Complete | Codebase Ready |
|---|---|---|---|---|---|
| Referring Rachel | External | Oregon Beta | #2 #4 (multiplier) | ✅ | ✅ (UTM param only) |
| Anxious Annie | External | Oregon Beta | #1 #2 #4 #5 | ✅ | ✅ |
| Modular Mike | External | Pre-Launch | #3 #4 #5 | ✅ | ✅ (GAP-001 minor) |
| Backyard Bill | External | Post-Series A | — | ❌ v1 | ❌ |
| Design Diane | External | Post-Series A | — | ❌ v1 | ❌ |
| Underwriter Ursula | External | Post-Series A | — | ❌ v1 | ❌ |
| Legal Clara | External | Post-Series A | — | ❌ v1 | ❌ |
| Visionary Victor | Internal | Pre-Launch | All 5 | ✅ | ⚠️ GAP-004 |
| Zoning Zara | Internal | Pre-Launch | #1 | ✅ | ❌ GAP-002 |
| System Sam | Internal | Active now | All 5 | ✅ | ✅ |
| Viral Val | Internal | Oregon Beta | #2 | ⚠️ no ROLE_REF | ✅ |
| Ledger Larry | Internal | Post-Series A | — | ❌ v1 | ✅ partial |
| Highway Harry | Internal | Post-Series A | — | ❌ v1 | ❌ |
| Splat Steve | Internal | Post-Series A | — | ✅ (deferred) | ❌ |

---

## Pre-Launch Checklist (Personas)

Before Oregon Beta opens, the following must be true:

- [ ] Victor has 5+ manufacturers approved in `/admin/manufacturers`
- [ ] Zara is hired and GAP-002 (Admin::ZoningResearch) is implemented
- [ ] GAP-001 (manufacturer submission notification) is wired
- [ ] GAP-003 ($49 refund credit) is implemented
- [ ] GAP-004 (Victor's executive dashboard) is implemented
- [ ] Val's ROLE_REFERENCE is written (if contract marketer is engaged)
- [ ] Val configures `?ref=` UTM param tracking in Google Analytics (Rachel activation)
- [ ] Victor drafts Rachel one-page partner brief PDF
- [ ] Victor identifies and demos Yardstake to 3–5 Rachel targets before Day 1
- [ ] **Ordering enforced:** Mike verified → Rachel activated → Annie arrives (Day 1)

---

## Related Documents

| Document | Location |
|---|---|
| MVP plan + sprint history | `marketplace_platform/docs/YARDSTAKE_MVP_PLAN.md` |
| Pre-launch gap analysis | `marketplace_platform/docs/pre_launch_gaps/` |
| Admin authorization architecture | `marketplace_platform/docs/architecture/ADR-002-admin-authorization-architecture.md` |
| Endless aisle strategy (AR deferral) | `marketplace_platform/docs/ENDLESS_AISLE_STRATEGY.md` |
| Persona test flows (QA) | `marketplace_platform/docs/PERSONA_TEST_FLOWS.md` |
