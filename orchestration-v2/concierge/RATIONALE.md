# Rationale: Concierge UX under the Orchestration Model

**Location:** `user_experience/orchestration-v2/concierge/`
**Persona:** "Fixer Fiona" — Yardstake project coordinator, Portland region
**Suite:** 9 production-quality HTML mocks across 5 batches (F-1 through F-10, issues #37–#46)

This document records the design rationale for each screen in the concierge mock suite. It explains how each UI feature connects to the core business logic of the Yardstake Phase 2 Orchestration Model, where Fiona operates as the "wedding planner" — absorbing logistical chaos so that the buyer (Annie) experiences a seamless, white-glove service. Each entry documents key UI features and the specific product reasoning behind design choices.

**Design System Summary:**
- Background: `#F1F5F9` (light slate content area) — Fiona is a professional on a large screen during a shift
- Nav: Dark gradient `#1E293B → #0F172A` with "Orchestration OS" branding — command center feel
- Sidebar: Dark slate `#0F172A` with fuchsia active states — persistent desktop ops navigation
- Cards: White `console-panel` with colored left borders — quick visual categorization
- Accent: Fuchsia `#D946EF` (primary), amber (warnings), emerald (approvals), red (escalations)
- Typography: Plus Jakarta Sans · Icons: Lucide · Desktop-first layout

**The "Emotional Anchor" Pattern:**
Unique to Fiona's screens. Every project-scoped screen includes a persistent fuchsia-bordered card showing the buyer's stated motivation and communication tone guidance (e.g., "Priority: Housing for aging parents. Tone: Grandparent-friendly."). This ensures every action Fiona takes is filtered through empathy, not just operational efficiency.

---

## Screen 1: `concierge_index.html`

**File:** `orchestration-v2/concierge/concierge_index.html`

**UI Features:**
- Mock index page for reviewers — card list of all 8 functional concierge screens
- Cards grouped by batch (1–5) with descriptions, batch badges, and complexity tags
- Dark gradient nav with "Orchestration OS" branding + fuchsia accent
- Gradient text heading: `linear-gradient(to right, #D946EF, #A855F7)`
- Card hover: fuchsia shadow + lift animation

**Rationale:** The index exists purely as a navigation aid for stakeholders reviewing the mock suite. It mirrors the `buyer_index.html` pattern but uses the concierge color scheme to establish the visual identity from the first click. Batch grouping helps reviewers understand the build order and dependencies — which screens had to exist before others could reference them.

---

## Screen 2: `concierge_dashboard.html`

**File:** `orchestration-v2/concierge/concierge_dashboard.html`

**UI Features:**
- KPI row: 4 cards — Active Projects (8, fuchsia border), At Risk (1, red pulse), Pending Approvals (2, amber), Permits in Review (3, blue)
- Triage queue table: 4 rows sorted by SLA urgency (material exception, payment delay, SLA breach, inspection hold) — clickable to triage_detail
- Active projects table: 8 rows with Project ID, Homeowner, Phase, Track A/B status, Next Action — Annie highlighted with fuchsia accent
- Sidebar with badge counts linking to all screens
- Mobile hamburger toggle, shift timer at bottom

**Rationale:** The dashboard is Fiona's home screen — the first thing she sees when she starts a shift. The KPI row answers "What needs my attention right now?" before she reads a single table row. The triage queue is sorted by SLA urgency, not chronological order, because Fiona's job is to prevent breaches, not process tickets in FIFO order. The At Risk card with a red pulse animation is deliberately attention-grabbing — in a portfolio of 8 projects, the one going wrong needs to scream. Annie's row gets fuchsia highlighting because she's the reference project across all mocks; reviewers can follow her journey through every screen.

---

## Screen 3: `concierge_project_detail.html`

**File:** `orchestration-v2/concierge/concierge_project_detail.html`

**UI Features:**
- 5-state lifecycle: Intake → Permit → Active Build → Transit → Close-out
- State 0 (Intake): Feasibility snapshot, "Set Emotional Anchor" form, concierge assignment, intro message generator with editable template + Send button, "Activate Project" CTA
- State 1 (Permit): SLA countdown, BDS filing details, proactive buyer notification draft
- State 2 (Active Build): Track A/B sync with progress bars, milestone timeline, coordinator notes
- State 3 (Transit): Crane Day logistics, 6-item pre-delivery checklist, spectator link, delivery ETA
- State 4 (Close-out): Final bank draw, welcome basket, document vault checklist, "Mark Project Complete" CTA
- Persistent right column: Emotional Anchor card, stakeholder panel, project summary
- Quick-action buttons: "Message Buyer" (fuchsia) + "Message Vendor" (slate)
- State-switcher demo panel for reviewers

**Rationale:** This is Fiona's primary working screen — where she spends most of her shift. The 5-state lifecycle mirrors the buyer's journey but from an operational lens: Annie sees milestones and emotions, Fiona sees tasks and deadlines. The Emotional Anchor card is persistent in the right column because every action Fiona takes on this screen — approving a draw, sending a message, flagging a risk — should be informed by who Annie is and why she's building. The state-switcher demo panel exists so reviewers can experience all 5 phases without needing test data; it's a UX review tool, not a production feature.

---

## Screen 4: `concierge_milestone_review.html`

**File:** `orchestration-v2/concierge/concierge_milestone_review.html`

**UI Features:**
- Milestone header: Foundation Phase 2 Draw, $37,500, ORD-9021
- Photo grid: 4 GPS-tagged construction photos with coordinate + timestamp overlays
- Lightbox: click to enlarge, arrow keys + Escape keyboard nav, photo counter
- Verification checklist: 5 items (4/5 checked) — footing depth, rebar, concrete cure, city inspection, drainage
- Review notes textarea with pre-filled assessment
- Action buttons: "Approve & Release $37,500" (emerald), "Request Additional Photos" (amber), "Reject — Escalate" (red)
- Confirmation modal on approve: amount, payee, buyer notification, irreversibility warning
- Right column: Emotional Anchor card, milestone context, GC info

**Rationale:** The milestone review is the financial gate of the platform — Fiona is the human who decides whether real money moves. The photo grid with GPS tags and timestamps isn't a nice-to-have; it's the evidence chain that proves work was done at the right location on the right date. The 5-point verification checklist converts Fiona's judgment from "does this look right?" to a structured protocol that can be audited. The irreversibility warning in the confirmation modal is intentional friction — releasing $37,500 to a contractor should never feel like clicking "OK" on a cookie banner.

---

## Screen 5: `concierge_triage_detail.html`

**File:** `orchestration-v2/concierge/concierge_triage_detail.html`

**UI Features:**
- 2-state screen: Vendor Exception (material substitution) and Buyer Dispute (payment delay)
- State 1 (Vendor Exception): Submitter card, exception details (White Oak → Maple, 8wk backorder), drawing reference, impact-if-denied analysis, action buttons (Approve/Route to Buyer/Deny)
- State 2 (Buyer Dispute): Emotional Anchor card, Track A/B sync showing factory on-schedule but GC blocked, conflict description, financial impact grid ($25K held, 48h delay, Crane Day at risk), template selector with message preview, Force Payout button (red)
- Force Payout confirmation modal with trust score impact warning
- SLA timer in header updates per state
- State-switcher demo panel

**Rationale:** Triage is where Fiona earns her title of "Fixer." The two states represent the two hardest categories of exception: a vendor asking to change something (does Annie need to know?) and a buyer not paying (does Fiona need to push?). The Force Payout button exists because the platform holds custodial funds — if Annie won't release a draw and the GC is blocked, someone has to break the deadlock. Making that button red with a trust-score warning is deliberate: Fiona should feel the weight of overriding a buyer's decision. The Emotional Anchor card appears in the buyer dispute state specifically to remind Fiona that Annie is a person with a reason for hesitating, not just a payment bottleneck.

---

## Screen 6: `concierge_messages.html`

**File:** `orchestration-v2/concierge/concierge_messages.html`

**UI Features:**
- Thread list (left panel): 5 active threads with avatar, name, role badge (Buyer blue / Manufacturer slate / Site GC amber / Permit Runner violet), last message preview, unread count, project ID
- Active thread (right panel): Fiona's messages in fuchsia bubbles (right-aligned), other party in dark bubbles (left-aligned)
- System event pills between messages: "Permit approved · Feb 3", "Foundation verified · Mar 5"
- Emotional Anchor sidebar for buyer threads; Vendor Compliance sidebar for vendor threads
- Template selector: 5 scenarios (Milestone approaching, Permit update, Exception notification, Crane Day prep, Project complete) with merge field substitution
- Tone indicator badge: "Grandparent-friendly" (pink) for buyers, "Standard" (slate) for vendors
- Send message appends new bubble with animation

**Rationale:** Unlike Annie's single-thread messaging view, Fiona's inbox is multi-party — she talks to many Annies AND many Mikes. The role-coded badges solve the "who am I talking to?" problem instantly: blue means buyer (empathy mode), slate means vendor (professional mode). The context sidebar swaps between Emotional Anchor (buyer threads) and Vendor Compliance (vendor threads) because Fiona needs different information depending on who she's messaging. The template selector with merge fields exists because Fiona sends structurally similar messages dozens of times a week — the templates ensure consistent quality while the merge fields prevent copy-paste errors. The tone indicator badge is the bridge between the Emotional Anchor and the compose area: it reminds Fiona that this particular buyer needs "grandparent-friendly" language, not industry jargon.

---

## Screen 7: `concierge_permit_tracker.html`

**File:** `orchestration-v2/concierge/concierge_permit_tracker.html`

**UI Features:**
- 3 KPI pills: In Review (3, blue), Approaching SLA (1, amber), Overdue (0, emerald "clear")
- Permit table: 5 rows with Project ID, Homeowner, City, Application #, Filed Date, SLA Deadline, Days Remaining (color-coded: green >14d, amber 7-14d, red <7d), Status, Last City Action
- Deficiency alert card (red-bordered): ORD-9028 flagged by Portland BDS, with route-to-runner / notify buyer / escalate actions
- Expandable proactive notification draft for amber-zone permit (ORD-9041): editable textarea with pre-drafted buyer message + send button
- SLA color guide reference panel
- Permit runner contact cards with message links

**Rationale:** Permits are the single biggest timeline risk in ADU construction — a 2-week delay at BDS cascades into a missed Crane Day, a rescheduled crane operator, and a buyer who loses confidence. The SLA color-coding (green/amber/red) converts abstract dates into instant visual priority. The amber-zone proactive notification is the key innovation: instead of waiting for the buyer to ask "what's happening with my permit?", Fiona sends an update before they worry. The deficiency alert card with three action options reflects reality — some deficiencies need a permit runner to fix, some need buyer awareness, and some need escalation to management. Fiona triages based on severity, not a one-size-fits-all workflow.

---

## Screen 8: `concierge_crane_day.html`

**File:** `orchestration-v2/concierge/concierge_crane_day.html`

**UI Features:**
- 3 upcoming delivery cards: Confirmed (Annie, fuchsia border), Pending (Tom, amber), At Risk (Lisa, red)
- Annie's expanded delivery detail with 3-column layout:
  - Pre-delivery checklist: 6 toggleable items with live progress bar (site access, crane clearance, utility staging, camera shipped, spectator link, weather check)
  - Crane operator card: Rigging Northwest, 70-ton hydraulic, contact phone, confirmed 5:30 AM ETA
  - Spectator link with copy button + "Send to Annie" quick-action
  - 3-day weather forecast with Lucide icons (cloud/sun/rain/wind) and Go/No-Go wind threshold badge
  - 40-day delivery countdown
- "Confirm Set Complete" button with confirmation dialog triggering close-out workflow

**Rationale:** Crane Day is the most emotionally charged moment in the entire ADU journey — the buyer's home literally arrives on a truck. The checklist pattern converts what could be a chaotic day into a manageable protocol. The weather widget with a Go/No-Go badge exists because a 70-ton crane operation has real safety constraints — wind above 25 mph means reschedule, and that decision needs to be visible at a glance, not buried in a weather app. The spectator link is a deliberate emotional design choice: Annie watching her home being placed creates a peak memory that defines her entire Yardstake experience. The "Confirm Set Complete" button is the bridge between Transit and Close-out — it triggers the final phase of the buyer's journey.

---

## Screen 9: `concierge_settings.html`

**File:** `orchestration-v2/concierge/concierge_settings.html`

**UI Features:**
- Section nav (left sidebar) with 4 sections: Shift Management, Message Templates, Notifications, Portfolio Overview
- Shift management: On/Off toggle with status label, schedule display (Mon–Fri 8-5 PST), coverage partner card (Maria Santos) with handoff notes textarea
- Message templates: 7 templates across 4 groups (Milestone, Permit, Exceptions & Logistics, Close-out) with merge field tags and click-to-preview
- Notification preferences: 5×3 toggle matrix (events × channels: in-app, email, SMS) with fuchsia CSS toggle switches
- Portfolio overview: 8-row read-only project table with phase badges and next-action column

**Rationale:** Settings is the least glamorous screen but it solves a real operational problem: Fiona works shifts, and when she goes off-shift, someone else needs to pick up her portfolio without dropping context. The coverage partner card with handoff notes ensures continuity — Maria Santos doesn't start her shift wondering "what's happening with ORD-9021?" because Fiona left notes. The message template library centralizes quality: instead of each concierge writing their own version of "your permit is approved," the templates ensure consistent brand voice across the team. The notification matrix gives Fiona control over signal-to-noise — SMS for triage items (urgent), email for milestones (important but not urgent), in-app for everything else.

---

## Cross-Link Audit

All concierge HTML files verified on April 6, 2026:

| Source Screen | Links To | Status |
|---|---|---|
| `concierge_index.html` | All 8 functional screens | All valid |
| `concierge_dashboard.html` | triage_detail, project_detail, permit_tracker, crane_day, messages, settings | All valid |
| `concierge_project_detail.html` | dashboard, milestone_review, messages | All valid |
| `concierge_milestone_review.html` | dashboard, project_detail | All valid |
| `concierge_triage_detail.html` | dashboard | All valid |
| `concierge_messages.html` | dashboard, index, project_detail, permit_tracker, crane_day, settings | All valid |
| `concierge_permit_tracker.html` | dashboard, index, project_detail, messages, crane_day, settings | All valid |
| `concierge_crane_day.html` | dashboard, index, permit_tracker, messages, settings | All valid |
| `concierge_settings.html` | dashboard, index, permit_tracker, crane_day, messages | All valid |

**Result: Zero broken links. All sidebar nav links verified. `concierge_index.html` lists all 8 functional screens.**
