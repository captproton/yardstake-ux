# Mike's Lifecycle: Beginning to End

**Persona:** Modular Mike — Oregon ADU Manufacturer / Supplier
**Created:** March 26, 2026

---

## The Problem He Has Before Yardstake

Mike builds quality prefab/modular ADUs in Oregon. His pain isn't the product — it's wasted qualification time. He spends the first 3–5 hours of every sales conversation answering questions the homeowner should've resolved before calling: *Does my lot even work? Can I build this size? What about setbacks?* Most leads never convert because they were never qualified.

---

## Phase 0: Before Mike Knows Yardstake Exists

Val pre-populates a listing for Mike from Oregon public contractor data. It's live — indexed by search engines, "Unverified" badge — but Mike doesn't know it exists and doesn't appear in any homeowner's matched results. He gets leads the old way: word of mouth, occasional contractor referrals.

---

## Phase 1: Victor's Outreach → Verified Partner

**The hook that closes Mike in the first 60 seconds:**
Victor doesn't pitch. He pulls up Yardstake, enters Mike's own neighborhood, and shows him exactly how many Portland R5 parcels qualify for his Studio XL model. Mike has never seen his market mapped this precisely. The conversation shifts from skepticism to "how does the commission work?"

**The pitch that lands:**
- Zero cost until a sale closes
- 3% commission (drops to 2.5% at Sale #6, 2% at Sale #16)
- Leads are pre-qualified by the Digital Twin — homeowners already know their lot works

**The four steps to `match_eligible?`:**
1. Service areas set to Oregon cities (not California seed data)
2. Commission agreement accepted
3. Stripe Express connected
4. 2+ active Home listings with real photos, Oregon pricing, accurate sq footage

Until all four are done, Mike sees a blurred lead inbox: *"These are the leads you'd receive as a Verified Partner."* That parcel counter — *"847 Portland R5 parcels qualify — you're not in their reports yet"* — is the primary conversion pressure.

**The ordering constraint that governs everything:**
Mike must reach Verified Partner status **before Rachel is activated**, which must happen **before Annie arrives on Day 1.** If Rachel sends Annie to a $49 report with zero matched manufacturers, Rachel's credibility is destroyed. The entire launch sequence depends on Mike being ready first.

---

## Phase 2: Days 1–30 — First Leads Arrive

Victor calls every Verified Partner before the platform opens. Mike understands: respond to every inquiry within 48 hours, the commission agreement covers Yardstake-originated sales even if the homeowner contacts him directly.

**What Mike's lead notification contains:**
- Homeowner's address + Oregon city
- Confidence tier (High/Medium/Low)
- Buildable envelope (sq footage)
- Which of Mike's models was matched
- LeadScore: Hot (75–100), Warm (50–74), Cool (<50)
- Financing readiness indicator

**Mike meets Annie here.** She comes in as a Hot lead — High confidence parcel, already purchased the $49 report, knows her lot qualifies, knows which Mike model fits. She isn't researching. She's buying. The platform already answered every question she used to ask contractors. Mike calls within the hour. It's the easiest conversation he's had in 15 years.

---

## Phase 3: Days 31–60 — First Sale, First Review

Victor's 30-day review with Mike surfaces blockers:
- Homeowner financing not in place → surface Val's financing content
- Site prep confusion → Mike leads with his preferred GC partner
- Price hesitation → smaller model or phased scope

First sale closes: `SaleTransaction` → `completed` → `CommissionCalculationService` → `CreatePaymentIntentService` → Stripe Connect transfer. Sam monitors the first transfer in real time.

Val interviews Mike for the Oregon Beta success narrative. A manufacturer who can describe pre-qualified Digital Twin leads is the most powerful recruitment tool for the next manufacturer cohort.

---

## Phase 4: Days 61–100 — The Target

**The math:** 20 sales across 5 manufacturers over 100 days = 4 per manufacturer = roughly one sale every 25 days. A Phase 1 inquiry that progressed to a site visit in Week 2–3 should be approaching contract territory here.

Victor monitors each pipeline. A manufacturer at 1 sale by Day 80 gets a direct diagnosis call: lead quality problem? Price point? Site prep? Each has a different fix.

**What success proves beyond the revenue:**
- Commission tier progression (Mike approaching Sale #6) validates volume, not one-off transactions
- If Mike self-activated from an unclaimed listing without Victor calling, that's the Series A data point: the claim-and-activate model scales to California without Victor making 500 calls

---

## Mike ↔ Annie: The Core Transaction Loop

```
Annie runs free check → High confidence result
Annie buys $49 report → matched Mike models appear
Annie submits inquiry → Mike's dashboard: Hot lead, LeadScore 87
Mike calls Annie within the hour
Annie is pre-answered — no lot qualification conversation needed
Site visit → contract → sale closes
Stripe transfer: commission deducted, remainder to Mike
```

The key insight: **Yardstake doesn't sell to Mike.** It sells *for* Mike. Annie arrives already convinced her lot works and already knowing which model fits. Mike's job is to close, not to educate. That's the moat.

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_modular_mike.html` | Mike's journey visualization |
| `LAUNCH_GUIDANCE.md` | Full pre-launch and Day 1–100 operational guide |
| `Builder Dashboard02.html` | Mike's manufacturer dashboard mockup |
| `demand_signals.html` | Demand signal and LeadScore UI |
| `builder_onboarding.html` | 5-step onboarding wizard |
| `factory_floor_iPad_checklist.html` | Factory floor checklist UI |
| `viral_embed.html` | Embeddable widget (Phase 2) |
