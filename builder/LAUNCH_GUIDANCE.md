# Mike — Launch Guidance: Now Through Day 100

**Persona:** Modular Mike — ADU Manufacturer / Supplier
**Period:** March 7, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 7, 2026

---

## Who Mike Is

Oregon-based prefab or modular ADU manufacturer. Quality product. Weak digital presence.
He gets most of his leads through word of mouth and the occasional contractor referral.
He is not actively seeking a new lead platform, but he responds to a compelling demo.

Mike's business needs: qualified leads (homeowners whose lot actually works for his product),
fast sales cycles (prefab/modular has shorter lead times than site-built), and minimal
administrative overhead. He does not want a subscription fee for a platform that might
not deliver.

The Yardstake pitch meets all three needs: zero cost until sale, leads pre-qualified by
the Digital Twin, and a self-service dashboard for lead management.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_modular_mike.html` | Mike's journey — updated March 7, 2026 |
| `Builder Dashboard02.html` | Mike's manufacturer dashboard — updated March 7, 2026 |
| `marketplace_platform/docs/MANUFACTURER_ACTIVATION_STATES.md` | Three activation states, match eligibility predicate, re-engagement sequence, Victor's admin view |
| `marketplace_platform/docs/analyses/ANALYSIS-002-manufacturer-pipeline.md` | Victor's outreach targets, commission structure, objection playbook |
| `marketplace_platform/docs/pre_launch_gaps/GAP-001-manufacturer-onboarding.md` | Submission notification gap |

---

## Mike's Three Activation States

Mike exists in one of three states at any point during the pre-launch and beta windows.
His experience is entirely different depending on which state he occupies.
Full spec in `MANUFACTURER_ACTIVATION_STATES.md`.

### State 1: Unclaimed

Val pre-populated a listing from public Oregon contractor data. Mike may not know it exists.

- No dashboard access
- Public listing page with "Unverified" badge and "Claim this listing" CTA
- Page is indexed by search engines (SEO value)
- Does not appear in any homeowner's matched results
- Val sends one cold outreach email to Mike's public contact address

Mike discovers his listing via: Val's outreach email, a Google search, or Victor's warm call.

### State 2: Claimed — Activation Incomplete

Mike has verified email ownership. He has a dashboard but is not yet match-eligible.

- Activation progress bar is the dominant element on every dashboard page
- Lead inbox shows blurred sample leads: "These are the leads you'd receive as a Verified Partner"
- Parcel count motivator: "847 Portland R5 parcels qualify for an ADU — you're not in their reports yet"
- Automated re-engagement emails on Days 0, 3, 7 of the claim
- Victor's personal plain-text email on Day 14 if still incomplete

Mike is not receiving real leads and is not contributing to Criteria #3 or #4.
His priority is completing the four remaining activation steps.

**Four steps to `match_eligible?` status:**
1. Service areas confirmed (Oregon cities, not California zip codes)
2. Commission agreement accepted (`commission_agreement_accepted_at` set)
3. Stripe Express connected (`stripe_account_id` present)
4. 2+ active `Home` listings with real photos, accurate square footage, Oregon pricing

The dashboard progress bar links directly to each incomplete step.

### State 3: Verified Partner — Match Eligible

All four steps complete. `match_eligible?` returns true.

- Full dashboard: real lead inbox, LeadScore tier display, commission summary
- "Verified Partner" badge (green) on public listing
- Appears in matched results in every relevant homeowner's $49 report
- Inquiry button visible on listing page
- Lead notifications fire via email when homeowners submit inquiries

This is Mike's active operating state during Oregon Beta.

---

## Pre-Launch: Getting Mike to Verified Partner

### Victor's Outreach (Starting March 9)

For Tier 1 targets (Adobu, Dweller), Victor calls in Week 1. For other targets, Week 2–3.
Full outreach schedule in `ANALYSIS-002-manufacturer-pipeline.md`.

**The demo that closes:**
Victor pulls up Yardstake, enters Mike's own neighborhood as a test address, shows the
High confidence result, shows where matched models would appear.
"Every homeowner who gets a High confidence result and buys the $49 report sees matched
manufacturers in their zip code. You'd be on that list."

**The pitch:** Zero cost until a sale closes. 3% commission. No subscription.
Per `ANALYSIS-002`: "The platform's commission model is zero-cost to the manufacturer
until a sale closes. This dramatically lowers the barrier to sign."

**Commission structure:**
| Tier | Rate | Trigger |
|---|---|---|
| Commission Only (start) | 3% | Sales 1–5 |
| Tier 2 | 2.5% | Sale #6+ |
| Tier 3 | 2% | Sale #16+ |

**Objection playbook** (from `ANALYSIS-002`):

| Objection | Response |
|---|---|
| "We already get leads from our website" | "We send pre-qualified leads — homeowners who already know their lot qualifies and have paid $49 for a report. Your close rate will be 3–5x higher." |
| "3% is too high" | "Our average Oregon ADU is $150K. That's $4,500 per sale, and you only pay when you close." |
| "We don't want to be on another lead platform" | "This isn't a lead platform — it's a marketplace where the Digital Twin matches homeowners to manufacturers who can actually build on their lot." |
| "We need to think about it" | "Let me show you how many Portland lots in your service area already have High confidence results. This is your pipeline today." |

### Onboarding Wizard (Mike's Self-Service Path)

Once Mike agrees, he registers through the 5-step wizard:

1. Company info (name, email, phone, website)
2. Oregon service areas (Portland, Eugene, Bend, Salem, Hillsboro — select all that apply)
3. Commission agreement acceptance (timestamped)
4. Catalog intent description
5. Review and submit

Victor receives a submission notification (GAP-001 fixed) and approves within 24 hours.

### What Mike Provides That Most Manufacturers Don't

The manufacturer onboarding wizard now includes one additional field:
**"Do you have a preferred GC partner for site prep work in your service area?"**

This is optional but strategically important. Most prefab/modular manufacturers already
have a GC they trust for foundation, utility stubs, and crane coordination. Capturing this
relationship means:
- The homeowner's $49 report includes a recommended site prep GC alongside Mike's models
- Crane day is managed by a GC who has done it with Mike's products before
- Post-sale coordination friction is dramatically reduced
- Mike's close rate improves because homeowners arrive to the site visit without "who
  handles site prep?" as an open question

If Mike names a preferred GC, Sam surfaces this in the report. No GC onboarding required.
No additional Yardstake vetting. Mike has already done the vetting.

### Service Area Verification (Critical)

Victor verifies that every manufacturer's service areas are set to Oregon cities in
`manufacturer_service_areas` — not California zip codes from seed data. A manufacturer
with California service areas does not appear in any Oregon homeowner's matched results
regardless of approval status.

---

## Phase 1: Days 1–30 (July) — First Leads Arrive

### Day 1: Victor Briefs Mike

Victor calls every Verified Partner individually before the platform opens.
Expectations set on this call:
- Respond to every inquiry within 48 hours
- The inquiry contains the homeowner's parcel data — use it. The homeowner has already
  paid $49 for their feasibility report. They are a qualified, motivated lead.
- Any sale to a homeowner who first discovered Mike through Yardstake is covered by the
  commission agreement — even if the homeowner contacted Mike directly after seeing his
  listing. The agreement covers origination, not just the inquiry channel.

### Mike's Lead Inbox

Each lead notification contains:
- Homeowner address and Oregon city
- Confidence tier (High / Medium / Low)
- Buildable envelope (square footage)
- Which of Mike's models was matched
- LeadScore tier (Hot / Warm / Cool) and score (0–100)
- Financing readiness (if homeowner indicated it on the inquiry form)

**LeadScore tiers:**
- Hot (75–100): High confidence result, indicated financing readiness or strong intent signals.
  Same-day response. These homeowners close at the highest rate.
- Warm (50–74): Medium confidence or some intent signals. Respond within 24 hours.
- Cool (below 50): Low confidence or no intent signals. Templated response, longer cycle.

Mike's dashboard displays all three tiers with color coding. Victor monitors whether Mike
is responding within the expected timeframes — a manufacturer who consistently ignores Hot
leads gets a call from Victor.

### Showrooming Risk for Mike

Some homeowners who find Mike's listing in the ADU home directory may contact him directly
(not through the Yardstake inquiry button). This is the showrooming risk.

Mike's commission agreement covers these originations. If a homeowner first discovered
Mike through Yardstake — whether through the directory, a $49 report, or a free check —
and that homeowner closes a sale, the 3% commission is owed.

Practically: Mike reports these sales honestly because the ongoing lead flow is worth
more than a single hidden sale. A manufacturer who hides Yardstake-originated sales loses
access to the Digital Twin lead pipeline — which is their primary value from the platform.

---

## Phase 2: Days 31–60 (August) — First Sales, First Reviews

### 30-Day Review with Victor

Victor meets with Mike individually at approximately Day 30.

Questions Victor asks:
- How many inquiries received?
- How many site visits completed?
- How many deals in negotiation?
- What's blocking conversion from site visit to contract?

Common blockers and diagnoses:
- **Homeowner financing not in place**: Ask whether homeowners are selecting "Not sure yet"
  on the financing readiness question. Surface Val's financing content page in Mike's
  follow-up email template.
- **Site prep confusion**: Is the homeowner unclear about who handles foundation/utility work?
  Mike should lead with his preferred GC partner in the site visit conversation.
- **Price point hesitation**: If multiple homeowners are stalling at price, Mike may need
  to offer a smaller model, a payment structure, or a phased scope.

### First Sale

Mike's first Yardstake sale triggers:
- `SaleTransaction` transition to `completed`
- `CommissionCalculationService` calculates 3% at closing
- `CreatePaymentIntentService` creates a Stripe Connect transfer
- Mike receives commission payout minus Yardstake's take via Stripe Express

This is the validation of the entire commission and payout infrastructure. Sam monitors
the first transfer in real time. Any webhook failure or transfer issue is day-one priority.

### Val's Success Story

Once Mike's first sale closes, Val interviews him (and optionally his homeowner) for the
Oregon Beta success narrative. A manufacturer who can articulate the value of Digital
Twin pre-qualified leads is the most powerful recruitment tool for the next manufacturer
cohort — and a trust signal for homeowners considering a $49 report.

---

## Phase 3: Days 61–100 (September–October) — The Close

### The 20-Sale Target

20 sales across 5 manufacturers over 100 days = 4 sales per manufacturer. Mike needs to
close roughly one sale every 25 days. A Phase 1 inquiry that progressed to a site visit
in Week 2–3 should be approaching contract territory in Phase 2–3.

Victor monitors each manufacturer's pipeline. A manufacturer at 1 sale by Day 80 gets
a direct conversation: what's blocking? Is it lead quality (accuracy issue)? Price point
(homeowners can't afford the product)? Site prep complexity (no GC solution)?

Each has a different fix. Victor's job in Phase 3 is to diagnose and unblock.

### Mike's Long-Term Value

Mike closing 4+ sales during Oregon Beta has two downstream effects:

1. **Commission tier progression:** Per `ANALYSIS-002`, the rate drops from 3% to 2.5%
   at Sale #6. A manufacturer approaching the tier threshold in beta is proof the
   model produces volume, not just one-time transactions.

2. **Claim layer proof-of-concept:** If Mike activated from an unclaimed listing without
   Victor's direct involvement, this is a data point for the Series A pitch: the
   self-service claim-and-activate model works and scales to California without Victor
   personally making 500+ calls.

### Mike's Listing Quality Checkup

By Day 60, Mike's listing should have:
- 2+ active `Home` listings with real photos, accurate Oregon pricing, and current dimensions
- At least one review (if the ADU directory is built and the first sale closed early)
- Video embed of his product (if available on YouTube)
- Preferred GC partner named in the listing
- All 5 Oregon cities confirmed in service areas (if he serves all 5)

A listing with a single placeholder photo and no pricing is a weak match even if the model
fits the parcel. The match quality of the $49 report depends on Mike's listing quality —
Victor reviews every Verified Partner's listing at the 30-day mark and flags gaps.
