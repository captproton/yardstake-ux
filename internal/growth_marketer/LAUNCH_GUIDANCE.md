# Val — Launch Guidance: Now Through Day 100

**Persona:** Viral Val — Growth Marketer
**Period:** March 7, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 7, 2026

---

## Who Val Is in This Window

Val owns the free-to-paid conversion funnel, Oregon SEO content, and the manufacturer
referral loop. During Oregon Beta, Victor proxies her role through direct outreach and
the existing content infrastructure. A contract marketer could activate Val's full role
at any point — the platform infrastructure for SEO, email, and analytics is in place.

Val's work in this window has two modes:
1. **Pre-launch (now → June 30):** Build the measurement and content infrastructure so
   that Day 1 data is clean, attributable, and actionable. Without this, the beta produces
   numbers that cannot be trusted or acted on.
2. **Beta (Days 1–100):** Weekly reporting, conversion optimization, content publishing,
   and building the Series A demand evidence.

Val also has two new responsibilities introduced by strategic decisions made in this session:
- **Claim layer sourcing:** Val sources 20–30 Oregon ADU manufacturers for pre-populated
  unclaimed listings before Sam imports them into the platform.
- **Financing and site GC content:** Val publishes educational content pages that reduce
  the two most significant post-sale friction points (financing gap, site prep gap) without
  requiring lender partnerships or GC onboarding.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_viral_val.html` | Val's persona journey |
| `marketplace_platform/docs/LAUNCH_100_DAY_PLAN.md` | Full 100-day plan with Val's schedule |
| `marketplace_platform/docs/analyses/ANALYSIS-001-conversion-funnel.md` | Conversion funnel baseline — current estimated rate, main levers, correct denominator |
| `marketplace_platform/docs/MANUFACTURER_ACTIVATION_STATES.md` | Claim layer — Val's sourcing and outreach role |

**Note:** Val does not have a `ROLE_REFERENCE.md`. If a contract marketer is engaged before
launch, one should be created. The PERSONA_INDEX.md flags this as an open gap.

---

## Now → June 30: Pre-Launch

### Priority 1: Lock in the Measurement Framework

Nothing Val produces during the beta is credible without confirmed analytics event tracking.
This must be verified before launch — not assumed.

**Confirm these analytics events fire correctly:**
- Free check submitted (with city and zone data)
- Result viewed — with confidence tier (High / Medium / Low) as a property
- Upgrade CTA shown (this is only shown to `qualified: true` results — not all homeowners)
- Upgrade CTA clicked
- $49 report purchased
- Inquiry submitted (homeowner → manufacturer)

Without the confidence tier on the result view event, conversion rate by tier is
unmeasurable. This is the most important analytical split of the entire beta.

**Lock in the conversion rate denominator with Victor and Sam.**
The correct denominator is: `$49 purchases / (High + Medium free checks)`.
Low confidence homeowners are shown no upgrade CTA — they cannot convert. Using total
free checks as the denominator produces a misleadingly low rate and obscures the real
conversion performance. Per `ANALYSIS-001-conversion-funnel.md`: current estimated
conversion without fixes is 2–4% using the correct denominator.

Document the agreed denominator in writing. Val, Victor, and Sam must report the same
number to investors. Disagreement on the denominator is a credibility risk.

**Configure UTM parameters** on all outbound channels — email links, city landing page
social shares, any paid channels. Without UTM tracking, Day 1 conversion data has no
source attribution.

### Priority 2: Email Sequences

All three sequences must be drafted and configured before Day 1. GAP-005 (the lead nurture
nil recipient bug) must be fixed by Sam before these sequences can fire — Val writes the
content, Sam wires the trigger.

**Sequence 1: Lead nurture (homeowner post-free-check)**
- Email 1 (within 1 hour of free check): "Here's what your result means" — explains the
  confidence tier, what the buildable envelope means, and what the $49 report adds.
  CTA: "Get your full report — $49"
- Email 2 (Day 3 if no purchase): "Still thinking about your ADU?" — social proof from
  Oregon homeowners who bought the report. Reiterate the $49 credit toward purchase.
  CTA: same
- Email 3 (Day 7 if no purchase): "Your lot has [X] sq ft of buildable space" — use
  the homeowner's actual buildable envelope from their free check result. Specific,
  not generic. CTA: same

**Sequence 2: Manufacturer claim onboarding**
- Email 1 (Day 0 — claim verified): "Welcome to Yardstake — your activation checklist"
  Lists all remaining activation steps with direct links. Per
  `MANUFACTURER_ACTIVATION_STATES.md`.
- Email 2 (Day 3 — if Stripe not connected): "One step is blocking your leads"
- Email 3 (Day 7 — if still not match-eligible): "X homeowners checked [city] this week
  — you weren't in their results"
  Day 14 email is Victor's personal plain-text send, not automated.

**Sequence 3: Homeowner post-purchase**
- Email 1 (immediately): Report delivery confirmation + PDF download link
- Email 2 (Day 3): "Ready to talk to a manufacturer?" — direct links to inquiry flow for
  each matched manufacturer in their report
- Email 3 (Day 14 if no inquiry submitted): "Here's what other Oregon homeowners asked
  their manufacturers" — FAQ content that reduces pre-inquiry hesitation

### Priority 3: Claim Layer Sourcing

Val sources 20–30 Oregon ADU manufacturers for pre-populated unclaimed listings.
Sam imports them using the admin import tooling built in April–May.

**Sources:**
- Oregon Housing and Community Services (OHCS) contractor database
- Oregon Construction Contractors Board (CCB) license lookup — filter by "Residential
  General Contractor" with ADU or modular construction specialty
- ORCA (Oregon Residential and Commercial Contractors Association)
- Manual research: manufacturer websites for companies known to serve Oregon

**For each manufacturer, capture:**
- Company name
- Primary city (not address — city and state only for unclaimed listings)
- Website URL (used internally for context, not shown on unclaimed listing page)
- Product types (modular, prefab, site-built, conversion)
- Oregon CCB license number if publicly available

**Outreach email to unclaimed listings:**
One cold email to each manufacturer's public contact address. Plain text.
Subject: "Your company has a listing on Yardstake"
Body: Brief explanation of what Yardstake is, what their listing shows, and how to claim
it to start receiving qualified leads. Link to claim initiation flow.
No automated follow-up. Victor handles Day 14 personal outreach for any that are claimed
but not activated.

### Priority 4: Content — City Landing Pages

Publish all 5 city landing pages before Day 1. Portland and Bend should be live now.
Eugene, Hillsboro, and Salem publish before launch.

Each page structure:
- "ADU rules in [City], Oregon" — covers zone types, size limits, setback basics
- "How it works" — free check → $49 report → matched manufacturers
- CTA: "Check your [City] property" → free check entry form
- FAQ: 5–7 common homeowner questions specific to that city

These pages are the primary organic search entry point. Portland especially: "ADU
zoning Portland" and "can I build an ADU in Portland" are high-intent searches.

### Priority 5: Financing and Site GC Content Pages

**"How to Finance Your ADU in Oregon"** (`/financing-your-adu`)
Plain-language guide covering:
- HELOC — how it works, typical timeline, what equity is required
- Cash-out refinance — when it makes sense vs. a HELOC
- Oregon Housing and Community Services (OHCS) ADU loan programs
- Fannie Mae HomeStyle and FHA 203k renovation loans
- Typical financing timeline (4–8 weeks for approval) so Annie sets expectations correctly

No lender recommendations. No referral arrangements. Educational content. No RESPA exposure.

This page reduces the most common post-sale drop-off cause: homeowners who sign a contract
but then stall trying to understand financing options independently.

**"Site Preparation: What Happens After Your ADU Contract"** (`/site-preparation`)
Plain-language guide covering:
- What site prep work a modular/prefab ADU installation typically requires
- Oregon CCB license types to look for in a GC
- What to ask a site prep GC before hiring
- What crane day involves (and what to tell your neighbors)
- Typical timeline from contract signing to certificate of occupancy

This page sets Annie's expectations before she engages a manufacturer. A homeowner who
arrives at a site visit knowing what happens next is a fundamentally different conversation
than one who doesn't.

---

## Phase 1: Days 1–30 (July) — Reporting and Early Optimization

**Weekly funnel report — every Friday for Victor.**
Template from `LAUNCH_100_DAY_PLAN.md`:

```
Free checks submitted:    [N]  by city
Confidence tier split:    High [X]% / Medium [X]% / Low [X]%
Upgrade CTAs shown:       [N]
$49 reports purchased:    [N]
Conversion rate:          [X]%  (purchases / High+Medium checks)
Inquiries submitted:      [N]
Open sales pipeline:      [N]
Cumulative sales:         [N] / 20
```

**Week 2: Identify the primary drop-off point.**
Where are homeowners leaving the funnel? Options:
- Address entry (not completing the form)
- Waiting for results (job processing delay)
- Result page (not clicking upgrade CTA)
- Auth wall (dropping off at the sign-up form)
- Payment page (abandoning before completing Stripe payment)

Each drop-off point has a different fix. Val identifies the biggest one and proposes the
fix to Victor and Sam.

**Week 3: First upgrade CTA copy test.**
Current CTA: "Get Your Full Report ($49)"
Test: "See Your Buildable Envelope + Matched ADUs for Portland"
Monitor click-through rate difference over 7 days.

**Lead nurture email performance tracking.**
- Open rate target: 30%+
- Click rate target: 5%+
If open rate is below 30%, test subject line variations.
If click rate is below 5%, the email content isn't connecting — review the body copy.

**Showrooming watch: manufacturer directory page traffic.**
If the ADU home directory is launched, monitor traffic to manufacturer listing pages.
A listing page with high traffic and zero inquiry button clicks is a showrooming signal —
homeowners are finding manufacturer information and leaving the platform.
Report this to Victor weekly. The fix is ensuring manufacturer direct contact information
is hidden behind the inquiry button, not displayed on the listing page.

---

## Phase 2: Days 31–60 (August) — Analysis and Content Expansion

**Conversion rate by confidence tier analysis.**
This is the most important analytical output Val produces during the beta.

Report format:
- High confidence homeowners: [X]% convert to $49 purchase
- Medium confidence homeowners: [X]% convert to $49 purchase

If High converts at 25% and Medium at 4%, the team knows:
- Do not try to fix the payment funnel — it works for motivated buyers
- Do invest in improving confidence tier coverage in Eugene/Hillsboro/Salem so more
  homeowners get High results
- Val's growth lever is working with Zara and Sam to move more homeowners from Medium
  to High, not optimizing copy on the result page

**Financing data check.**
Review inquiry form financing readiness responses (if Sam added the question in pre-launch).
What percentage of inquiry-submitters selected "Not sure yet"? If above 40%, the financing
content page is not reaching them before they inquire — consider adding a financing
readiness prompt on the result page before the upgrade CTA.

**First manufacturer success story.**
Once the first sale closes, Val publishes it:
- Which city, which zone type, which ADU model
- How the homeowner found Yardstake
- What the site visit was like (homeowner quote)
- When the ADU will be installed

Get quotes from both the homeowner and the manufacturer. This social proof is the most
powerful trust signal for both future homeowners (credibility) and manufacturers
considering joining the platform (proof the model works).

**Publish remaining 3 city landing pages** if not done pre-launch: Eugene, Salem, Hillsboro.

**First SEO content article:**
"Can I Build an ADU on My Portland Lot?" — 800–1,200 words. Bottom-of-funnel search
intent. Explains R1–R10 zone types in plain English, links directly to the free check.
This is the highest-leverage organic content play for Phase 2.

---

## Phase 3: Days 61–100 (September–October) — Building the Series A Evidence

**Oregon Beta narrative.**
Val drafts the public-facing narrative of what Oregon Beta has produced. Numbers from the
weekly reports. Framing from Victor.

Key metrics to feature:
- "X Oregon homeowners checked their lot"
- "Y feasibility reports purchased"
- "[Accuracy rate]% of results verified accurate by our research team"
- "Z ADUs currently in progress across 5 Oregon cities"

This narrative serves three purposes: homeowner trust (if published as a landing page),
manufacturer recruitment (demonstrates platform traction), and Series A warm-up
(becomes Victor's talking points in investor conversations).

**California waitlist.**
Simple landing page at `/california` or `/coming-to-california`:
- Headline: "Yardstake is coming to California"
- 2–3 sentences on the expansion plan
- Email capture only — no promises about timeline
- Submit → confirmation email

Target: 500+ signups before the Q4 Series A pitch. Even 200 signups from California
homeowners is a demand signal that supports the West Coast expansion narrative.

**Post-purchase survey.**
Send to the first 10–20 $49 report buyers (homeowners, not manufacturers).
Two questions only:
1. "What made you decide to buy the report?" (open text)
2. "What almost stopped you from buying?" (open text)

The answers directly shape the conversion copy for California and Washington launches.
Common "almost stopped me" answers also reveal conversion levers that analytics cannot see.

**Oregon Beta summary deck for Victor.**
Not a pitch deck — a data summary. One page per criterion:
- Criterion, target, actual, trajectory
- Key data point (a specific number that makes the criterion legible to a non-technical investor)
- One honest note about what still needs to improve

Val builds the structure. Victor edits the framing. Sam supplies the data.
