# Rachel — Launch Guidance: Now Through Day 100

**Persona:** Referring Rachel — Channel Partner (Realtor / Lender / ADU Consultant)
**Period:** March 25, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 25, 2026

---

## Who Rachel Is

Rachel is not an end user. She is a professional who has ongoing relationships with
Oregon homeowners — the people who become Anxious Annie on the Yardstake platform.

She exists in one of three variants:

| Variant | Role | What she needs | Referral volume |
|---|---|---|---|
| Realtor Rachel | Oregon RE agent, 15–30 transactions/year | A tool that differentiates her in listing consultations | 5–10 Annies/year |
| Lender Rachel | ADU-focused lender (credit union, RenoFi-type) | Pre-qualified borrowers with feasibility proof | 10–20 Annies/year |
| Consultant Rachel | ADU permitting consultant / housing advocate | A free intake filter that reduces her own scoping calls | 15–30 Annies/year |

Rachel is not a validation criteria directly. She is a **multiplier on Criteria #2 and #4**:
every Annie she refers is a free-check entry at near-zero acquisition cost.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_referring_rachel.html` | Rachel's journey — created March 25, 2026 |
| `buyer/LAUNCH_GUIDANCE.md` | Annie's journey (Rachel's referrals become Annies) |
| `internal/growth_marketer/LAUNCH_GUIDANCE.md` | Val owns attribution tracking and referral link management |
| `internal/founder/LAUNCH_GUIDANCE.md` | Victor owns Rachel outreach and partner activation |

---

## Pre-Launch: Activating Rachel (Before Day 1)

Rachel is the simplest activation in the entire platform. She requires:

1. **A referral link** — `yardstake.com/check?ref=<name>` with UTM tracking. Val sets this
   up in Google Analytics. No code change required — just a URL param convention.

2. **A one-page partner brief** — PDF Rachel can attach to her email signature or print
   for client consultations. Victor drafts this. It answers: what is Yardstake, what does
   the free check do, what does the $49 report contain, and why should Rachel's clients run it.

3. **Victor's 30-minute demo** — Victor calls Rachel, runs the free check on her own address
   or a client address she names, and shows her the High/Medium/Low result. The demo IS
   the activation. Rachel is sold in the first 60 seconds when she sees her address result.

**Nothing else is required for Oregon Beta.** Rachel does not need an account, a dashboard,
a contract, or a commission agreement. She refers because it makes her look good and helps
her clients — not because Yardstake pays her to.

---

## Target Rachel Partners for Oregon Beta

Victor should activate 3–5 Rachel partners before Day 1. Priorities:

### Realtor Rachels (highest volume, easiest activation)
- Portland-area agents specializing in older neighborhoods (SE, NE, N Portland) with
  large lots — these are the highest-density Annie prospects
- RE/MAX, John L Scott, and indie brokerages in Portland Metro
- Look for agents who already mention ADU potential in their listing marketing

### Lender Rachels (highest quality leads)
- Oregon Community Credit Union — has an established ADU loan product
- Unison or RenoFi partners in Oregon — already pre-qualified for ADU financing
- Local mortgage brokers who attended Oregon ADU Collaborative events

### Consultant Rachels (highest conversion rate)
- Oregon ADU Collaborative network members
- Portland-area architects who do permit drawings (Diane persona variant)
- ADU-focused permitting consultants listed on Portland BDS resources

---

## Rachel's Activation Script (Victor's Talking Points)

> "I have a tool that tells your clients in 60 seconds whether their lot qualifies for
> an ADU, what they can build, and which Oregon manufacturers have models that fit. It's
> free for them. It takes 60 seconds. And it makes you the most informed professional
> in the room when ADU potential comes up.
>
> I'm going to give you a personal link. You send it to clients. They run the check. If
> they want the full report, they pay $49 — that's their decision, not yours. You get
> credit for the referral. We track it. When we launch our referral program formally,
> you'll be first in line.
>
> Want to run it on your own address right now?"

The last line is the close. Rachel always says yes. She sees her own result. She's activated.

---

## Rachel's Minimum Deliverables for Oregon Beta

| Deliverable | Owner | Status |
|---|---|---|
| UTM referral param convention (`?ref=name`) | Val | ⏳ needs setup |
| Partner brief PDF (1 page) | Victor | ⏳ needs drafting |
| Rachel outreach list (5 targets) | Victor | ⏳ needs building |
| Attribution visible in Val's analytics | Val | ⏳ needs UTM config |

**Estimated effort:** 4–6 hours total. No platform code changes required in Oregon Beta.

---

## How Rachel's Referrals Flow Through the Funnel

```
Rachel shares link → Annie runs free check (?ref=rachel_name)
                    → Val's analytics: "Referral channel: rachel_name"
                    → Annie converts to $49 → attributed to Rachel in UTM report
                    → Annie purchases ADU → Criteria #4 tick, attributed to Rachel channel
```

Val produces a weekly referral report during Oregon Beta. Rachel gets a monthly email
from Victor: "You've sent us X free checks this month. Y converted to reports. Here's
what that means for your clients." This is not automated — Victor sends it manually
during Beta.

---

## What Changes Post-Series A

When Yardstake raises its Series A, Rachel becomes a formal channel partner with:

- **Rachel dashboard**: referrals sent, conversions, referral credits balance
- **Embeddable widget**: Rachel puts a free-check input on her own website or Linktree
- **Formal incentive program**: credit per conversion (e.g., $10 off a report for Rachel
  herself, or 1% referral fee on ADU sales that originate from her link)
- **Co-branded PDF**: Rachel's name and headshot on the $49 report cover page
- **Rachel as a Val responsibility**: Val owns the Rachel channel at scale; Victor only
  needed to close the first 5 personally

The Phase 2 Rachel dashboard is a modest build (~8–12 hours): a public `/partners` signup
page, a referral link generator, and a simple read-only dashboard showing conversion counts.
No commission payment infrastructure needed — Rachel earns soft value, not cash, in Phase 2.

---

## Zillow Parallel

Zillow's Premier Agent program is the closest analog. Key lessons for Yardstake:

1. **The partner markets you because it closes their own deal.** Rachel doesn't refer
   Yardstake out of loyalty — she refers it because her client comes back more confident
   and more transaction-ready. Design for Rachel's self-interest, not her altruism.

2. **The free tool is the referral engine.** Zillow's Zestimate is shareable and
   embeddable. The Yardstake free check needs a shareable URL that Rachel can text to a
   client from her phone during a showing. Keep it simple: one URL, mobile-friendly,
   60-second result.

3. **Embed early, extract later.** Zillow embedded itself into agent workflows before
   adding fees. Yardstake should activate Rachel at zero cost in Beta and formalize the
   program after the model is proven. Don't charge or complicate the Rachel relationship
   before it has momentum.

---

## Gaps Affecting Rachel (Oregon Beta)

None of Rachel's Beta activation requires platform code changes. However:

- **GAP-005 (email capture)** indirectly affects Rachel: if Annie runs the free check
  through Rachel's link and Yardstake doesn't capture her email, Rachel's referral is
  a dead end. GAP-005 closure ensures Rachel's referrals are re-engageable.

- **If Oregon manufacturers are not signed** before Rachel is activated, Rachel sends
  Annie to a $49 report with zero matched manufacturers. This destroys Rachel's
  credibility with her client. Victor must close manufacturers before activating Rachel.

**The ordering matters:** Mike (manufacturers) must be activated before Rachel is activated
before Annie arrives on Day 1.

---

## Summary

Rachel is the highest-leverage, lowest-cost acquisition channel available during Oregon Beta.
Three active Rachel partners can outperform any paid advertising budget Victor has access to.
The entire activation is: a URL param, a PDF, and a 30-minute Zoom call. Do this first.
