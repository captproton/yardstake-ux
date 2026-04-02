# Annie — Launch Guidance: Now Through Day 100

**Persona:** Anxious Annie — Oregon Homeowner / Buyer
**Period:** March 7, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 7, 2026

---

## Who Annie Is

Portland-area homeowner. 5,000+ sq ft lot, owned 5+ years. Has been researching ADUs for
months without a confident answer. She is not sure if her lot qualifies. She has looked at
contractor websites, read articles, and gotten conflicting information from neighbors. She
is ready to trust a platform that gives her a definitive, data-backed answer.

Annie is the reason the platform exists. Every technical decision — the Digital Twin, the
confidence scoring, the matched manufacturer results — exists to serve her specific problem.

Annie does not exist as a real user yet. Her experience begins on Day 1. Everything between
now and then determines the quality of that first impression.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_anxous_annie.html` | Annie's journey — updated March 7, 2026 |
| `dashboard-phase0.html` | Annie's dashboard — updated March 7, 2026 |
| `marketplace_platform/docs/analyses/ANALYSIS-001-conversion-funnel.md` | Current funnel state and conversion levers |
| `marketplace_platform/docs/analyses/ANALYSIS-003-launch-readiness-scorecard.md` | Launch readiness against criteria Annie drives |
| `marketplace_platform/docs/MANUFACTURER_ACTIVATION_STATES.md` | What Annie sees for each manufacturer listing state |

---

## Pre-Launch: What Must Be True Before Annie Arrives (Day 1)

Annie's first experience depends entirely on the gaps being closed before launch. Each gap
maps to a specific moment in her journey.

| If this gap is not closed | Annie's experience breaks here |
|---|---|
| GAP-010 (Postmark) | She receives no email — ever |
| GAP-011 (Stripe live keys) | Her $49 payment appears to succeed but no money moves; report may not generate |
| GAP-005 (email capture) | She gets a High confidence result, leaves, and is never re-engaged |
| GAP-006 (EUG/HIL/SAL parcels) | Eugene/Hillsboro/Salem homeowners get Low confidence results regardless of actual eligibility |
| GAP-009 (auth redirect) | She clicks "Buy Report," hits a sign-up form, registers, and lands on a generic dashboard — her report is gone |
| GAP-003 ($49 credit) | She pays $49 with no signal that it applies toward her eventual purchase |
| Oregon manufacturers signed | She buys a $49 report and sees zero matched manufacturers — the core promise is broken |

The hard gate is the Oregon manufacturers. If Victor does not have at least 3
manufacturers with Oregon service areas, active listings, and Stripe Connect before Day 1,
Annie should not be admitted to the platform. A homeowner who pays $49 and gets an empty
"Matched Manufacturers" section will not trust the platform again.

---

## Annie's Journey — What It Should Look Like at Launch

### Step 1: Discovery

Annie finds Yardstake through:
- **Organic search**: Val's city landing page for Portland answers "ADU zoning Portland Oregon"
- **Referral**: A manufacturer Victor is talking to mentions the platform to a homeowner
  they're already in conversation with
- **Content**: Val's "Can I Build an ADU on My Portland Lot?" article

She arrives at the free check entry form without knowing what to expect.

### Step 2: Free Feasibility Check

Annie enters her Portland address. The platform geocodes it, matches it to a parcel in the
Digital Twin, runs `PortlandOregonStrategy`, and returns a High or Medium confidence result
with her zone, estimated setbacks, and buildable envelope.

For Portland and Bend: this result is high-quality and trustworthy.
For Eugene, Hillsboro, and Salem: this result is useful at launch but has lower confidence
until Zara's strategy class reviews are incorporated.

What Annie sees:
- Confidence tier (High / Medium / Low) with a plain-English explanation
- Her zone (e.g., "R5 — Low-Density Residential")
- Estimated buildable envelope (e.g., "After setbacks: approximately 320 sq ft")
- Upgrade CTA (shown only if she qualifies — `qualified: true`)

What Annie does not see: her specific parcel dimensions, matched manufacturer models, full
setback calculations, or permit type. Those require the $49 report.

### Step 3: Lead Nurture Email (First Time This Has Ever Worked)

Within 1 hour of her free check, Annie receives an email (Val's Sequence 1). This is the
first time in the platform's history that any homeowner has received a follow-up email —
GAP-005 (nil recipient) has prevented every previous email from firing.

The email explains what her result means and CTAs to the $49 report.

If she doesn't buy on Day 1, she receives two more emails over the following week.

### Step 4: $49 Premium Report

Annie clicks the upgrade CTA. She is not yet authenticated.

`FeasibilityReportPaymentsController` requires `authenticate_user!`. She hits the sign-up
form. If GAP-009 was verified pre-launch, Devise redirects her back to the payment page
after registration. She completes the $49 Stripe payment without re-entering her address.

She receives:
- A PDF report with her parcel's full setback calculations, buildable envelope, and permit type
- "How to Finance Your ADU in Oregon" section — HELOC, cash-out refi, OHCS programs
- "Site Preparation — What Happens After Contract Signing" section
- 3 matched Oregon manufacturer models with photos, square footage, and Oregon pricing
- Names of manufacturers with their preferred site prep GC partners (if available)
- The $49 credit applied toward her eventual ADU purchase (GAP-003)

### Step 5: The Financing Gap (Addressed Without a Lender Partnership)

Annie sees a $145K–$200K ADU that fits her lot. Her first question is: "How do I pay for this?"

Without intervention, she leaves the platform to call her bank, waits 4–8 weeks for a HELOC
approval, and loses momentum. This is the most common silent drop-off point — invisible
in the platform's analytics.

The $49 report's financing section tells her:
- What a cash-out refinance involves (most common for homeowners with 20%+ equity)
- What a HELOC involves (lower closing costs, revolving credit)
- That OHCS has Oregon-specific ADU loan programs she may qualify for
- That Fannie Mae HomeStyle and FHA 203k can roll construction costs into a mortgage
- The typical timeline (4–8 weeks for approval) so she plans accordingly

Val's `/financing-your-adu` page provides deeper detail. The inquiry form asks her about
financing readiness before she contacts a manufacturer — so the manufacturer knows whether
she is financing-ready before the site visit.

### Step 6: Manufacturer Inquiry

Annie submits an inquiry through the platform. The inquiry automatically includes:
- Her property address
- Her confidence tier and buildable envelope from the $49 report
- Her LeadScore (calculated by `LeadScoringService` from feasibility data + intent signals)
- Her financing readiness response (if she selected it in the form)

The manufacturer receives a structured lead notification — not a cold email, but a data
package that makes the site visit conversation immediately substantive.

### Step 7: Site Visit

Annie meets the manufacturer (or their site rep) at her property. Because the $49 report
included the site preparation section, Annie already knows:
- Site prep work is required before the ADU can be delivered
- The manufacturer likely has a preferred GC for this work
- The timeline from contract to certificate of occupancy is typically 6–12 months

The site visit confirms the report's findings. The manufacturer can verify the buildable
envelope, review the setback requirements, and assess site prep needs.

### Step 8: The Site GC Gap (Addressed Without GC Onboarding)

After the site visit, Annie needs a GC to handle foundation, utility stubs, and crane
coordination. Without Yardstake's help, she independently finds a random GC who may have
never done a modular ADU installation — and creates problems for the manufacturer.

With the manufacturer's preferred GC surfaced in the $49 report, Annie has a starting
point. The manufacturer has already vetted this GC. The homeowner-manufacturer-GC
coordination is familiar and practiced. Crane day is managed by people who have done it before.

Val's `/site-preparation` page supplements this with plain-English guidance on what to
expect and what to ask a GC before hiring.

### Step 9: Contract and Sale

Annie signs a contract with the manufacturer. The `SaleTransaction` is created. Yardstake
earns its 3% commission on the contract value. The $49 Annie paid for her report credits
toward the purchase (GAP-003).

---

## Annie's Experience in the ADU Home Directory

If the ADU home directory is built (a future feature), Annie can browse ADU models from
all manufacturers — including unclaimed and partially-activated listings.

She must never see an unclaimed or pending manufacturer in her matched results inside the
$49 report. Only `match_eligible?` manufacturers appear there.

In the directory, the visual distinction is:

| Listing state | Badge | Inquiry button | What Annie can do |
|---|---|---|---|
| Unclaimed | "Unverified" (grey) | Hidden | Read about the manufacturer; no contact |
| Claimed — Incomplete | "Activation Pending" (yellow) | Hidden | Same |
| Verified Partner | "Verified Partner" (green) | Visible | Submit inquiry through Yardstake |

If Annie clicks into a non-verified profile:
> "This manufacturer hasn't joined the Yardstake network yet. To get matched to Verified
> Partners who serve your lot, run a free feasibility check."

This turns a dead end into a funnel entry. Non-verified directory traffic benefits Annie
(she discovers more options) and the platform (she re-enters the free check flow).

**Showrooming awareness:** Annie can discover a manufacturer's name through the directory
and contact them directly (bypassing Yardstake). The platform's defense is not hiding
information — it is making the Yardstake inquiry channel better than a cold call. The
inquiry automatically delivers her parcel data to the manufacturer. A homeowner who arrived
via direct contact does not come with that data package.

---

## Phase by Phase: Annie's Experience

### Phase 1: Days 1–30 (July)
Annie's first cohort enters the platform. Primary entry is Portland and Bend. Eugene,
Hillsboro, and Salem are live but with lower initial confidence until Zara's strategy
reviews land.

The lead nurture email fires for the first time. Val monitors open and click rates.
Val's CTA test runs. The auth wall UX is confirmed or flagged.

### Phase 2: Days 31–60 (August)
Phase 1 Annie who made an inquiry in Week 1–2 is now in a site visit or early negotiation.
ADU sales have 60–120 day timelines — Phase 1 inquiries closing in Phase 2 are on track.

New Phase 2 Annie arrives to improved social proof: Val's first manufacturer success story
is published. Eugene, Hillsboro, and Salem confidence tiers improve as Zara's strategy
reviews land. Val's conversion tier analysis reveals which confidence tier to focus on.

### Phase 3: Days 61–100 (September–October)
Phase 1 Annie may be approaching contract signing. Val's post-purchase survey targets the
first 10–20 buyers — their answers reveal what worked and what almost stopped them.

Oregon Beta social proof grows: "X homeowners checked their lot, Y reports purchased, Z
ADUs in progress." Annie in Phase 3 arrives to a platform with evidence of real outcomes,
not just a promise.

---

## Annie's Most Important Moments — Where the Platform Must Not Fail Her

| Moment | Risk | Defense |
|---|---|---|
| Free check result — sees her buildable envelope | Low confidence result in EUG/HIL/SAL due to missing parcel data | GAP-006 closed before launch |
| Lead nurture email — re-engagement after result | Never receives email | GAP-005 closed before launch |
| Payment page — auth wall | Loses her place after sign-up | GAP-009 verified before launch |
| $49 report — sees matched manufacturers | Empty manufacturer list | Oregon manufacturers signed before launch |
| Post-sale — "How do I finance this?" | Leaves platform, loses momentum | Financing section in report + Val's content page |
| Post-sale — "Who does my site prep?" | Independently finds unqualified GC | Site prep section in report + manufacturer's preferred GC |
