# Victor — Launch Guidance: Now Through Day 100

**Persona:** Visionary Victor — Founder / CEO
**Period:** March 7, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 7, 2026

---

## Who Victor Is in This Window

Victor is the sole decision-maker during Oregon Beta. He owns manufacturer relationships,
the investor narrative, and direct accountability for all 5 validation criteria. No other
person can close manufacturer partnerships. No other person can make the Series A judgment
call at Day 100.

His work in this window is three overlapping tracks running simultaneously:
1. **Sales manager** — recruiting, activating, and supporting 5 manufacturer partners
2. **Operator** — monitoring the 5 criteria weekly and intervening when any falls behind
3. **Storyteller** — building the Series A narrative in real time as the data accumulates

The risk is that Track 3 pulls attention from Tracks 1 and 2 before the criteria are met.
Structure prevents this: Monday–Wednesday is manufacturer pipeline and sales operations.
Thursday–Friday is Series A narrative and investor relationship-building.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_visionary_victor.html` | Victor's journey — role context and operating style |
| `ROLE_REFERENCE.md` | Victor's operating guide — decision rights, escalation, weekly rhythm |
| `dashboard.html` | Executive dashboard prototype (5 KPIs — not yet built in production) |
| `marketplace_platform/docs/LAUNCH_100_DAY_PLAN.md` | Full 100-day operational plan |
| `marketplace_platform/docs/analyses/ANALYSIS-002-manufacturer-pipeline.md` | Outreach targets, demo script, objection playbook |
| `marketplace_platform/docs/analyses/ANALYSIS-005-series-a-narrative-readiness.md` | What the Q4 pitch needs, what doesn't exist yet |
| `marketplace_platform/docs/MANUFACTURER_ACTIVATION_STATES.md` | Three manufacturer states, match eligibility, Victor's admin workflow |
| `marketplace_platform/docs/pre_launch_gaps/GAP-001-manufacturer-onboarding.md` | Submission notification gap |
| `marketplace_platform/docs/pre_launch_gaps/GAP-004-victor-executive-dashboard.md` | 5-KPI dashboard gap |

---

## Now → June 30: Pre-Launch

### Manufacturer Outreach — Starts March 9. No Exceptions.

This is the only pre-launch item with a 4–6 week lead time that no one else can close.
Every other gap is Sam's or Zara's work. This one is Victor's alone.

**Target sequence** (from `ANALYSIS-002-manufacturer-pipeline.md`):

| Week | Target | Goal |
|---|---|---|
| Week 1 (Mar 9) | Adobu (Portland) | Meeting + live demo |
| Week 1 (Mar 9) | Dweller (Portland) | Meeting + live demo |
| Week 2 (Mar 16) | Oregon Cottage Company | Meeting + demo |
| Week 2 (Mar 16) | DC Structures (Hood River) | Meeting + demo |
| Week 3 (Mar 23) | Wind River Built or Studio Shed | Meeting + demo |
| Week 4–6 | Follow-up all 5, begin wizard onboarding | 3+ registered and pending |
| May 15 | 5 manufacturers approved, Stripe connected, Oregon listings live | Hard gate met |

**The demo that closes:** Pull up Yardstake, enter the manufacturer's own neighborhood as a
test address, show the High confidence result, point to where their models would appear.
"Every homeowner who gets a High confidence result and buys the $49 report sees matched
manufacturers in their zip code. You'd be on that list."

**The pitch:** Zero upfront cost. 3% commission only when a sale closes. No subscription.

**The warm call (claim layer):** Once Sam builds the claim layer in April, some manufacturers
will have pre-populated unclaimed listings. Victor's call becomes: "You already have a listing
on Yardstake. I want to show you what a claimed, activated listing delivers." This is
materially warmer than a cold platform pitch.

**Service area check (critical):** Every manufacturer Victor approves must have Oregon cities
set in their service areas — not California zip codes from seed data. Victor personally
verifies this before clicking approve in `/admin/manufacturers`.

### Addressing the Site GC Gap

When meeting with manufacturers, Victor asks one operational question: "Who do you typically
work with for site prep?" Most prefab/modular manufacturers have a trusted GC partner for
foundation, utility stubs, and crane coordination. Victor captures this relationship and
ensures Sam adds it to the onboarding wizard as a "preferred GC partner" field.

This is not a GC recruitment program. It is surfacing existing relationships so homeowners
arrive at site visits knowing who handles site prep. One field in the wizard, enormous
reduction in post-sale friction.

Separately, Victor ensures the $49 report includes a site preparation section (Sam's task,
~2 hours) so Annie understands what happens after contract signing before she engages a
manufacturer.

### Addressing the Financing Gap

Victor does not need to recruit lenders. He ensures three things are in place before launch:

1. The $49 report includes a financing options section covering HELOC, cash-out refi, OHCS
   ADU programs, and Fannie Mae HomeStyle (Sam's task, ~2 hours).
2. Val publishes a "How to Finance Your ADU in Oregon" content page.
3. The inquiry form asks Annie about financing readiness — this feeds into LeadScore and
   makes the gap visible in analytics if deals are stalling there.

### Series A Thesis Document

Victor drafts a 1–2 page document before July 1 articulating the Digital Twin moat in
investor language. From `ANALYSIS-005`:

> "A competitor can clone our marketplace in 6 months. They cannot clone five years of
> hand-verified Oregon zoning data."

This document does not need to be finished — it needs to exist so it matures alongside the
beta data. Victor edits it monthly as criteria progress accumulates.

### Victor's Admin Tooling

Until Sam delivers GAP-004 (executive dashboard), Victor monitors through:
- `/admin/manufacturers` — approval queue, submission notifications (once GAP-001 is fixed)
- Madmin dashboard for revenue and payment data
- Val's weekly Friday report (template in `LAUNCH_100_DAY_PLAN.md`)

---

## Phase 1: Days 1–30 (July) — "Prove the Funnel"

**Day 1 checklist:**
- [ ] Confirm all 5 manufacturers are `match_eligible?` in production
- [ ] Run a personal end-to-end test: Portland address → free check → $49 report → confirm
      Oregon manufacturer matches appear (not California seed data)
- [ ] Confirm lead nurture email fires after a test free check submission
- [ ] Confirm Stripe payment processes in live mode

**Days 1–7:** Brief every manufacturer individually. One call per partner. Expectations:
- Respond to every inquiry within 48 hours
- Provide the homeowner's parcel data from the inquiry to the site visit team
- Report any direct contact from Yardstake-sourced homeowners (commission agreement covers these)

**Days 1–14:** Monitor the lead inbox for each manufacturer via `/admin/manufacturers`.
Any inquiry that goes 72 hours without a manufacturer response gets a Victor phone call to
the manufacturer. First impressions set the quality standard for the entire beta.

**Showrooming watch:** Monitor whether homeowners who view manufacturer directory pages are
converting through the Yardstake inquiry button or contacting manufacturers directly. A
manufacturer listing page with high traffic and zero inquiries is a showrooming signal. The
fix is ensuring manufacturer direct contact information is not displayed — only the inquiry
button is actionable.

**Week 2:** Begin the Series A weekly narrative update. Even with zero sales in Week 1,
document what's building: how many free checks, what the confidence tier distribution looks
like, which manufacturers are responding to leads. The Q4 pitch is built from this log.

**Week 4:** Review Phase 1 against the Day 30 targets in `LAUNCH_100_DAY_PLAN.md`. Is the
inquiry-to-site-visit rate producing enough pipeline to reach 20 sales by Day 100?

---

## Phase 2: Days 31–60 (August) — "Find the Lever"

**30-day manufacturer reviews:** Meet individually with each partner.
- How many leads received?
- How many site visits completed?
- How many deals in negotiation?
- What's blocking conversion from site visit to contract?

If a manufacturer has received 10 inquiries and converted zero to site visits, the problem
is theirs to identify — but Victor diagnoses it with them. Is the lead quality wrong (a
data accuracy issue)? Is the price point out of reach? Is the manufacturer's response time
the problem? Each has a different fix.

**Replace underperformers early.** A manufacturer who is non-responsive at Day 35 still
leaves 65 days for a replacement to generate sales. Waiting until Day 70 leaves nothing.

**Oregon TAM analysis.** Work with Sam to pull qualifying parcel counts by city from the
platform database. Per `ANALYSIS-005`: "Qualifying parcel counts by city, average ADU
prices in the market, estimated annual ADU permit volumes." This becomes a section of the
Series A narrative document.

**California warm-up (2–3 calls).** Not signing anyone — learning. What would California
manufacturers need to see before committing to a commission-only arrangement? What are the
key differences from Oregon? These conversations inform the Series A "use of funds" framing.

---

## Phase 3: Days 61–100 (September–October) — "Build the Story"

**Chase every open sale.** The 20-sale target is Victor's personal responsibility in Phase 3.
If the pipeline shows 14 closings by Day 85, Victor needs 6 more in 15 days. He is personally
involved in every stalled deal — calling manufacturers, asking what's blocking, offering to
join a homeowner call if it helps move things forward.

**"Completed sale" definition.** Victor must be clear with Sam and with investors about what
counts as a sale: contract signed and deposit paid, or ADU installed and certificate of
occupancy issued. The Series A pitch must use consistent language. Investors who later learn
that "sales" means contracts (not installations) will feel misled if not told upfront.

**Data room assembly.** Victor needs Sam and Zara to produce exports; he writes the framing.
Per `ANALYSIS-005`, the data room requires:
- Accuracy audit summary (Zara's 50-parcel formal audit)
- Conversion funnel actuals (Val's 100 days of analytics)
- Revenue breakdown (Sam's Stripe export)
- Completed sale log (Sam's `SaleTransaction` export)
- Competitive positioning one-pager (Victor writes)
- Oregon TAM analysis (Victor + Sam)
- Use of funds breakdown ($4M allocation — from `ANALYSIS-005`, Victor formalizes)

**Investor warm-up conversations.** 3–5 West Coast seed investors. Not pitching — relationship
building. Victor's ask: "What would you need to see for a $4M raise?" The answers shape the
Q4 pitch framing. Conversations started in Phase 3 are relationships that exist before the
formal pitch in Q4.

**Claim layer evaluation.** How many of the 20–30 unclaimed listings activated to
`match_eligible?` without Victor's direct involvement? Per `LAUNCH_100_DAY_PLAN.md`:
this is the proof-of-concept for the self-service model that drives California and Washington
expansion. Even 3–4 self-activated manufacturers is a data point for the Series A pitch.

**Day 100 judgment.** From `LAUNCH_100_DAY_PLAN.md`:

| Scenario | Criteria Met | Action |
|---|---|---|
| Full validation | All 5 | Series A, Q4 2026 |
| Strong validation | 4 of 5 | Series A with honest trajectory narrative |
| Partial validation | 3 of 5 | Re-examine assumptions before proceeding |
| Soft failure | 2 of 5 | Identify the broken assumption, test alternatives |
| Failure | 0–1 of 5 | Pivot to B2B SaaS or shutdown conversation |

---

## Victor's Biggest Risk in Each Phase

| Phase | Biggest risk | Early signal | Response |
|---|---|---|---|
| Pre-launch | Fewer than 3 manufacturers signed by June 30 | Week 3: only 1 meeting taken | Double outreach pace, lower bar to a 6th candidate |
| Phase 1 | Manufacturer non-response to leads | 72-hour inbox check shows dead leads | Victor calls manufacturer same day |
| Phase 2 | No sales closing — financing is the silent blocker | Manufacturers report good site visits, no contracts | Ask manufacturers: "Where are deals dying?" If financing, surface the content Val built |
| Phase 3 | Series A prep pulls attention from sales close | Victor spending Thursday + Friday on pitch instead of pipeline | Keep Mon–Wed for sales operations until 20-sale target is confirmed |
