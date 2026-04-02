# Sam — Launch Guidance: Now Through Day 100

**Persona:** System Sam — Lead Developer / Platform Engineer
**Period:** March 7, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 7, 2026

---

## Who Sam Is in This Window

Sam built the platform. He operates it during Oregon Beta. His work in this window has
three distinct modes:

1. **Pre-launch (now → June 30):** Gap closure — 11 identified gaps plus claim layer plus
   financing/site-GC additions. Approximately 42 hours of code and config across 16 weeks.
2. **Phase 1 (Days 1–30):** Production operator — triage, edge case fixes, zero new features.
3. **Phases 2–3 (Days 31–100):** Accuracy corrections, data exports, architecture documentation,
   California scoping.

Every production bug becomes a failing RSpec test before it becomes a fix. That discipline
does not slip during the beta even under operational pressure.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_system_sam.html` | Sam's persona journey |
| `ROLE_REFERENCE.md` | Sam's operating guide — monitoring signals, escalation, weekly rhythm |
| `marketplace_platform/docs/pre_launch_gaps/OVERALL_GAP_ANALYSIS.md` | All 11 gaps with fix detail and priority order |
| `marketplace_platform/docs/LAUNCH_100_DAY_PLAN.md` | Full 100-day operational plan with Sam's schedule |
| `marketplace_platform/docs/MANUFACTURER_ACTIVATION_STATES.md` | Claim layer full spec — `match_eligible?` predicate, three states, implementation summary |
| `marketplace_platform/docs/analyses/ANALYSIS-001-conversion-funnel.md` | Funnel baseline, where fixes have the most conversion impact |

---

## Now → June 30: Pre-Launch — Gap Closure Schedule

Work in strict priority order. Items 1–4 are configuration or 30-minute fixes — do them
this week before touching anything else.

### This Week (March 9–15)

**GAP-010 — Verify Postmark production config (config, ~1 hr)**
Confirm `POSTMARK_API_KEY` is set in the production environment. Verify the sender domain
is authenticated. Send a test email through every critical mailer path: lead nurture,
inquiry notification, manufacturer approval, report failure alert. A misconfigured Postmark
is a complete communications blackout — no homeowner, no manufacturer, no admin email fires.

**GAP-011 — Verify Stripe live keys + webhook (~2 hrs including test)**
Confirm `STRIPE_PUBLIC_KEY` and `STRIPE_SECRET_KEY` use live keys in production. Note:
`ENV.fetch('STRIPE_PUBLIC_KEY', '')` empty string default silently breaks the card element
initialization — there is no visible error. Verify the Stripe webhook is registered at
`yardstake.us/pay/webhooks/stripe` in the Stripe dashboard. Run a live end-to-end $49
payment in production before promoting the platform.

**GAP-008 — Deactivate SLC and BER (30 min)**
```ruby
Jurisdiction.where(city_code: %w[SLC BER]).update_all(active: false)
```
Non-Oregon homeowners should not receive feasibility results at Oregon Beta launch.

**GAP-001 — Wire manufacturer submission notification (30 min)**
Call `ManufacturerMailer.new_submission_notification` from
`Admin::ManufacturersController` when a manufacturer submits the wizard. Victor currently
learns about new submissions only by checking the admin panel.

### March 16–22

**GAP-005 — Fix lead nurture email nil recipient (~2 hrs)**
Add an `email` column to `PropertyCheck`. Update the free check form to capture an
optional email address. Wire `LeadNurtureMailer.feasibility_result` to use the captured
email. Verify end-to-end: submit a free check with an email address, confirm the lead
nurture email arrives.

Context: the guard `if property_check.email.present?` in `ProcessPropertyCheckJob` has
always evaluated false because the column does not exist. Every homeowner who completed a
free check has received no follow-up email. The lead re-engagement sequence has never
fired for a single user.

### March 23 – April 5

**GAP-009 — Auth redirect verification (~2–4 hrs)**
An anonymous homeowner who tries to buy a $49 report hits `authenticate_user!` on
`FeasibilityReportPaymentsController`. Verify that Devise's `stored_location_for`
correctly redirects her back to the payment page after sign-up — not to a generic dashboard.
Test: submit a free check anonymously, click upgrade, complete registration, confirm landing
on the payment page with the correct `feasibility_report_id` parameter. Document the result.

### April 6–20 (Largest Code Item — ~12 hrs)

**GAP-002 — AccuracyAuditRecord + Admin::ZoningResearch**
This is the most important pre-launch engineering item. Without it:
- Zara has no platform tooling — she audits in spreadsheets
- Criteria #1 (90% accuracy) is unmeasurable even if the data is accurate
- Victor cannot answer "how do you know your data is 90% accurate?" with data at the
  Series A pitch

Build:
- `AccuracyAuditRecord` model: parcel reference, jurisdiction, confidence tier, expected
  result, actual result (from manual review), auditor notes, audited_at
- `Admin::ZoningResearch` controller and views: audit entry form, audit history list,
  accuracy rate summary by city and zone
- Give Zara access immediately after delivery so she can begin auditing before launch

### April 20 – May 15

**GAP-004 — Victor's executive dashboard (~5 hrs)**
Replace Madmin's generic SaaS metrics (total revenue, subscriptions, users) with Victor's
5 Oregon Beta KPIs:
1. Accuracy rate (% of audited High-tier parcels confirmed correct)
2. Conversion rate (free checks → $49 purchases, with correct denominator: High + Medium only)
3. Active manufacturer partners (match-eligible count)
4. Completed ADU transactions
5. GTV (token revenue + commission revenue)

**Claim layer (~10 hrs)**
Full spec in `MANUFACTURER_ACTIVATION_STATES.md`. Summary:

New fields on `BuilderProfile`:
- `claimed: boolean, default: false, null: false`
- `claimed_at: datetime, null: true`

New `BuilderProfile` method:
```ruby
def match_eligible?
  manufacturer? && claimed? && approved? &&
    commission_agreement_accepted? && stripe_connected? &&
    homes.active.count >= 2 && manufacturer_service_areas.any?
end
```

New controller: `Manufacturers::ClaimsController` (claim initiation via email token,
verification sets `claimed: true`).

New mailer: `ManufacturerClaimMailer` (Day 0, Day 3, Day 7 automated emails).

Updated `LeadRoutingService`: use `match_eligible?` instead of `approved_manufacturers`
scope. Current scope checks only `admin_approved_at` — a manufacturer who is approved but
not Stripe-connected can currently appear in lead routing incorrectly.

Updated `/admin/manufacturers`: four-tab layout — Verified Partners / Claimed-Incomplete /
Unclaimed / Pending Approval.

Admin import tooling: seed unclaimed listings from Val's sourced manufacturer list.

**Financing and site GC additions to $49 report (~3 hrs combined)**

Add two sections to the premium PDF report:

1. **"How to Finance Your ADU"** — covers HELOC, cash-out refinance, OHCS ADU programs,
   Fannie Mae HomeStyle / FHA 203k. No lender recommendations. Educational content only.
   No RESPA exposure.

2. **"Site Preparation — What Happens After Contract Signing"** — explains what site prep
   involves (grading, utility stubs, foundation, crane day), what CCB license types to look
   for in an Oregon GC, and (if the manufacturer has a preferred GC partner from the
   onboarding wizard) the name of the manufacturer's recommended site prep GC.

Add to manufacturer onboarding wizard (Step 3 or a new step): "Do you have a preferred
GC partner for site prep work in your service area?" Single text field, optional. Surfaces
in the matched result and in the $49 report.

Add to inquiry form: "How are you planning to finance your ADU?" (Cash / Home equity /
Looking for options / Not sure yet). Feed this as a signal into `LeadScoringService` — a
homeowner who selects "Cash" or "Home equity" should score higher than "Not sure yet."

**Define `SaleTransaction#completed` semantics**
Confirm with Victor what "completed" means for commission trigger and Criteria #4 counting.
Document the decision. If it means "contract signed and deposit paid," add a comment to the
model making this explicit. If it means "installation complete," the 100-day timeline needs
adjustment.

### May 15 – June 1

**GAP-006 — Parcel imports for Eugene, Hillsboro, Salem (data ops)**
Coordinate with Zara on data vintage verification before running imports:
- Eugene: ODF MapServer
- Hillsboro: RLIS Washington County filter (not Multnomah County)
- Salem: City of Salem dataset (confirm boundary vs. Marion County)

Monitor import jobs. Verify parcel count and null geometry rate after each import. Run
`bin/rails oregon:validate` after all three are complete.

### June 1–15

**GAP-007 — Transit stops for Eugene, Hillsboro, Salem (~2 hrs)**
Seed representative major transit stops using coordinates verified by Zara against official
GTFS data:
- Eugene: EmX BRT (3–5 major corridor stops)
- Hillsboro: MAX Blue Line western terminus stops
- Salem: Cherriots key stops

Without these, every parcel in these cities returns `parking_required: true` regardless of
actual transit proximity.

### June 15–30

**GAP-003 — $49 refund credit logic (~6 hrs)**
Wire `FeasibilityReport#credited_to_sale_transaction_id` through `CommissionCalculationService`
so the $49 paid for the report credits toward the ADU purchase commission. This is a
conversion incentive and a trust signal — Annie's $49 is a deposit, not a sunk cost.

**June 30 — Launch rehearsal (~2 hrs)**
End-to-end test in production: Portland address → free check → lead nurture email fires →
$49 payment (live Stripe) → PDF report generated with Oregon manufacturer matches → inquiry
submitted → manufacturer receives notification → commission calculation correct.

---

## Phase 1: Days 1–30 (July) — Production Operations

Sam shifts from builder to operator. No new features. Triage only.

**Day 1:**
- Monitor SolidQueue (`/admin/jobs` or MissionControl) for stuck jobs
- Confirm Postmark delivery in Postmark dashboard logs
- Confirm `YardstakeController#analysis` hardcoded SLC mock data is unreachable from
  any navigation path — this is a trust-breaker if any homeowner reaches it

**Daily (first two weeks):**
- `ProcessPropertyCheckJob` success rate — a spike in failures signals geocoding issues
  or a strategy class error
- Geocoding miss rate — what percentage of submitted addresses fail to match a parcel?
  Above 10% in any city needs investigation
- Stripe webhook delivery in Stripe dashboard

**Within 48 hours of any production error:**
- Reproduce the error in development
- Write a failing RSpec test that captures it
- Fix, verify test passes, deploy

**Week 2:** Report geocoding miss rate by city to Victor. A high miss rate in Eugene or
Hillsboro may indicate the parcel imports need correction.

---

## Phase 2: Days 31–60 (August)

- Implement accuracy corrections from Zara's Phase 1 audit findings. Each strategy class
  error becomes a failing test before it becomes a fix.
- Build feasibility tier distribution monitoring — alert if Portland's High confidence rate
  drops more than 5 percentage points week-over-week (signals a strategy class regression).
- Investigate auth redirect edge cases surfaced in Phase 1 (GAP-009 follow-up if needed).
- Optimize geocoding for Eugene, Hillsboro, Salem based on Phase 1 miss rate data.

---

## Phase 3: Days 61–100 (September–October)

**Series A data exports (Victor needs these — do not make him extract manually):**
- Parcel count by city and confidence tier
- Conversion funnel: free checks → High/Medium/Low → upgrades → purchases (by week)
- Completed sale log: date, city, manufacturer, sale price, commission amount
- Revenue breakdown: token revenue vs. commission revenue by month
- Accuracy audit summary: parcels audited, correct/incorrect by city and zone (from Zara)

**Production architecture documentation:**
A one-page diagram covering PostGIS at scale, SolidQueue job infrastructure, Stripe Connect
pipeline, Active Storage, multi-database setup. Sufficient for Series A technical diligence.

**Performance audit:**
How does the PostGIS parcel lookup perform at 5x current free check volume? Run a load test
against a staging environment. Document results. This is planning for West Coast expansion,
not optimization work for Oregon Beta.

**California infrastructure scoping:**
What is the delta between Oregon and California data infrastructure? Key questions:
- SRID differences for California parcel data
- CalHFA ADU loan integration complexity (if financing integration is prioritized post-Series A)
- Strategy class architecture for California jurisdictions (how many cities, which state
  base class approach per `strategy_pattern/state_city_hierarchy.md`)
- PostGIS performance at 10M+ parcels (California has 7M+ owner-occupied homes)
Document as an estimate for the Series A "use of funds" section.

**Claim layer scaling assessment:**
Does the current claim infrastructure support bulk pre-population at California scale?
The Oregon claim layer handles 20–30 manufacturers. California may require 500+. Assess
whether the admin import tooling needs to become a self-service pipeline.
