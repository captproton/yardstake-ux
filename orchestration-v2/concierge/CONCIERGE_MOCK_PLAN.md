# Concierge Persona Mock Plan: "Fixer Fiona"

**Location:** `user_experience/orchestration-v2/concierge/`
**Author:** Opus (architecture) → Sonnet (implementation via `/new-pr-auto`)
**Execution:** 10 GitHub issues across 5 batches → `/new-pr-auto <issue_number>`
**Date:** April 4, 2026

---

## Context

The vendor persona ("Modular Mike") has 17 production-quality HTML mocks in `orchestration-v2/vendor/`, and the buyer persona ("Anxious Annie") has 13 mocks in `orchestration-v2/buyer/`. Both cover the full user lifecycle. The concierge persona ("Fixer Fiona") has one existing mock (`concierge_dashboard.html`) — a triage queue showing a material exception card and a payment mediation card. This plan defines the complete concierge mock suite to demonstrate Fiona's full operational role as the "wedding planner" who absorbs logistical chaos so Annie never has to.

### Source Documents

| Document | Role |
|---|---|
| `Macro PRD: Yardstake Digital Concierge` | North-star UX vision — 7 phases, "wedding planner" emotional layer, Fiona's 5-phase journey |
| `docs/plans/annie/mocks/BUYER_PHASE2_EXPERIENCE_SPEC.md` | Phase 2 buyer spec — describes Fiona's role at each buyer milestone |
| `internal/admin/blueprint/_fixer_fiona.html` | Internal persona blueprint — 5-phase journey map (trust anchoring → checkout shepherd → bureaucracy manager → enforcer → emotional handover) |
| `docs/plans/fiona/mocks/01-03` | Phase 1 mocks (superseded) — project queue, project detail, milestone approval. Useful as content reference. |
| `orchestration-v2/concierge/concierge_dashboard.html` | Existing partial mock — triage queue with 2 exception/mediation cards |
| `orchestration-v2/buyer/RATIONALE.md` | Pattern reference — how buyer mocks were documented |

### What Already Exists (Reusable)

- **`concierge_dashboard.html`** — Dark gradient nav ("Orchestration OS"), slate sidebar (Triage Queue, Dispute Mediation, Permit SLAs, Crane Day Logistics), light content area with two triage cards. Establishes the fuchsia accent color, `console-panel` card pattern, and Fiona's avatar/shift badge. **Disposition: REFACTOR in place.** Keep the nav, sidebar, and design system. Replace the two hardcoded triage cards with a proper KPI row + triage queue table + active projects list. The exception/mediation detail content moves to `concierge_triage_detail.html`.
- **`RATIONALE.md`** — 3 stub entries describing the existing dashboard. **Disposition: OVERWRITE from scratch** in the final polish batch (F-10). Follow the buyer RATIONALE.md pattern exactly.
- **Phase 1 mocks** (`docs/plans/fiona/mocks/01_project_queue.html` through `03_milestone_approval.html`) — Light-mode Tailwind, indigo accent, basic admin layout. **Superseded** by orchestration-v2 but useful as content reference for project data, stakeholder names, and milestone amounts.

---

## Design System: Concierge vs. Buyer vs. Vendor

| Property | Vendor (Mike) | Buyer (Annie) | Concierge (Fiona) |
|---|---|---|---|
| Background | Dark slate `#0F172A` | Light warm `#F8FAFC` | Light slate `#F1F5F9` (content), dark gradient nav |
| Card style | Dark glassmorphism | Light glassmorphism | White `console-panel` with colored left borders |
| Nav | Dark with emerald accents | White with blue accents | Dark gradient `#1E293B → #0F172A`, "Orchestration OS" |
| Sidebar | N/A (tab nav) | N/A (tab bar) | Dark slate `#0F172A` with fuchsia active states |
| Accent | Emerald (payouts), purple (stations) | Blue-to-cyan gradient (trust, calm) | Fuchsia `#D946EF` (primary), amber (warnings), emerald (approvals) |
| Typography | Plus Jakarta Sans | Plus Jakarta Sans | Plus Jakarta Sans |
| Icons | Lucide | Lucide | Lucide |
| Emotional register | "Cash register" — urgency, payout velocity | "Wedding planner" — reassurance, transparency | "Mission control" — triage, efficiency, empathy-aware |
| Layout | Responsive cards | Responsive cards | Fixed sidebar + scrollable main (desktop ops tool) |

**The concierge UI is a desktop ops console.** Fiona is a professional coordinator on a large screen during a shift — not a homeowner on a phone. The layout is a persistent sidebar + scrollable main content area, optimized for rapid context-switching between projects. The dark nav + light content split gives the "command center" feel without the eye fatigue of a fully dark UI.

### The "Emotional Anchor" Pattern

Unique to Fiona's screens. Every project-scoped screen must include a persistent **Emotional Anchor card** — a fuchsia-bordered panel showing the buyer's stated motivation and communication guidance:

```
┌─ 💜 Emotional Anchor ──────────────────────────┐
│ Priority: Housing for aging parents              │
│ Tone: High trust, low complexity. Avoid jargon.  │
│ Communication: Grandparent-friendly templates.    │
└──────────────────────────────────────────────────┘
```

This card appears on: `concierge_project_detail.html`, `concierge_milestone_review.html`, `concierge_triage_detail.html`, and `concierge_messages.html` (as a sidebar element). It does NOT appear on the dashboard (portfolio-level view) or settings.

---

## Screen Inventory (9 Screens)

Organized by Fiona's operational modes. Each entry names the file, the primary task, the key data, and the complexity.

### Core Console

#### Screen 1: `concierge_index.html`
- **Purpose:** Mock index page for reviewers — same pattern as `buyer_index.html`
- **What Fiona sees:** Card list of all 8 concierge screens with descriptions, batch badges, and complexity tags
- **Key interaction:** Click any card to open the mock
- **Complexity:** Low

#### Screen 2: `concierge_dashboard.html` (refactor of existing)
- **Purpose:** Fiona's home screen — portfolio overview + triage queue
- **What Fiona sees:**
  - **KPI row:** 4 cards — Active Projects (8), At Risk (1, red pulse), Pending Approvals (2), Permits in Review (3)
  - **Triage queue:** Table of flagged items sorted by SLA urgency. Each row: order ID, project (homeowner + address), flag type (exception / dispute / SLA breach), time remaining, severity badge. Click row → drill into `concierge_triage_detail.html`
  - **Active projects list:** Compact table of all 8 projects. Each row: project ID, homeowner name, current phase, Track A status, Track B status, next action. Click → `concierge_project_detail.html`
  - **Sidebar nav:** Triage Queue (4 badge), Active Projects, Permit SLAs, Crane Calendar, Messages, Settings
- **Key interaction:** Triage queue rows are clickable. KPI cards are summary-only. Sidebar nav links to other screens.
- **Disposition:** The existing 2 triage cards are removed — their content moves to `concierge_triage_detail.html`. The dashboard becomes a clean overview.
- **Complexity:** **High** (establishes all shared chrome — nav, sidebar, KPI pattern, table styles)

### Project Lifecycle

#### Screen 3: `concierge_project_detail.html`
- **Purpose:** Single project deep-dive — Fiona's primary working screen
- **What Fiona sees:** 5-state machine mirroring the project lifecycle:
  - **State 0 — Intake:** New buyer just deposited. Feasibility snapshot (zone, buildable area, model selected). "Set Emotional Anchor" form (dropdown: housing for aging parents / rental income / home office / guest suite + free-text notes). "Assign Concierge" button (pre-filled with Fiona). "Generate Intro Message" → pre-filled template with buyer name + model + timeline. "Activate Project →" CTA.
  - **State 1 — Permit:** Permit SLA countdown (days remaining, city queue position). BDS filing status. Fiona's proactive notification draft ("We're handling the city's questions — no action needed"). Next action: "Notify buyer when permit issues."
  - **State 2 — Active Build:** Track A/B sync dashboard — Factory Build % vs. Site Prep % with status badges (On Schedule / At Risk / Blocked). Milestone timeline (completed nodes in emerald, current in blue, upcoming in slate). Next milestone card with $ amount and trigger condition. Fiona's coordinator notes textarea.
  - **State 3 — Transit:** Crane Day logistics card (date, crane operator, camera setup status, weather check). Spectator link generation. Delivery ETA with truck GPS reference. Pre-delivery checklist (site access confirmed, crane clearance verified, utility pre-staging).
  - **State 4 — Close-out:** Final bank draw trigger (amount, lender paperwork status). Welcome basket order status (champagne + personalized mugs). Document Vault checklist (CO uploaded, warranties filed, appliance manuals attached). "Mark Project Complete" CTA.
- **Shared across all states:**
  - Stakeholder panel: Homeowner (Annie, avatar, phone, emotional anchor), Manufacturer (Cascadia Modular, contact), Site GC (Pacific Foundation Works, contact), Permit Runner (name, status)
  - Emotional Anchor card (fuchsia border)
  - State-switcher demo panel (same dashed-border pattern as buyer mocks)
  - "Message Buyer" and "Message Vendor" quick-action buttons
- **Key interaction:** State switching via demo buttons. "Generate Intro Message" in intake. "Mark Project Complete" in close-out.
- **Complexity:** **High** (5 states, rich data in each)

### Financial Operations

#### Screen 4: `concierge_milestone_review.html`
- **Purpose:** Photo evidence review + fund release gate
- **What Fiona sees:**
  - Milestone header: "Foundation — Phase 2 Draw" + $37,500 amount + project ID
  - Photo evidence grid: 3-4 GPS-tagged photos from the Site GC (Pacific Foundation Works). Each photo shows GPS coordinates + timestamp overlay. Click to lightbox.
  - Verification checklist: 4-5 items (footing depth verified, rebar placement confirmed, concrete cure documented, city inspection passed, drainage installed). Each item has a check/flag toggle.
  - Emotional Anchor card (persistent)
  - Fiona's review notes textarea
  - Action buttons: "Approve & Release $37,500" (emerald) | "Request Additional Photos" (amber) | "Reject — Escalate to Ops Lead" (red)
  - Approval triggers a confirmation modal: "This will release $37,500 from escrow to Pacific Foundation Works. Annie will be notified." with "Confirm Release" CTA.
- **Key interaction:** Toggle checklist items. Photo lightbox. Approve/reject with confirmation modal.
- **Complexity:** Medium

#### Screen 5: `concierge_triage_detail.html`
- **Purpose:** Exception + dispute resolution — the detail view when Fiona clicks a triage queue item
- **What Fiona sees:** 2-state machine:
  - **State 1 — Vendor Exception:** Material substitution or change-order request from the manufacturer. Context pane: who submitted (Mike avatar + factory details), exception details (material X → Y, reason, drawing reference), impact-if-denied card (delay duration, buyer impact, vendor score risk). Action pane: Approve Substitution (no buyer sign-off needed) | Route to Buyer for Approval | Deny & Hold Original Spec (issue extension).
  - **State 2 — Buyer Dispute:** System-flagged buyer behavior (e.g., Annie delayed "Approve & Pay" for 48 hours). Context pane: buyer emotional anchor card, Track A/B sync status (factory on-schedule but GC blocked), conflict description (what triggered the flag, how long, $ amount held). Action pane: Draft Message to Buyer (template selector with emotional tone) | Review GC Evidentiary Photos | Adjudicate & Force Payout (red, requires confirmation modal).
- **Shared across states:** SLA timer (time remaining to resolve), project summary header, state-switcher demo panel.
- **Key interaction:** State switching. Action button selection. Confirmation modal on force-payout.
- **Complexity:** Medium (content from existing dashboard moves here)

### Communication & Tracking

#### Screen 6: `concierge_messages.html`
- **Purpose:** Fiona's multi-party communication hub
- **What Fiona sees:**
  - **Thread list (left panel):** All active message threads sorted by recency. Each thread shows: avatar, name, role badge (Buyer / Manufacturer / Site GC), last message preview, unread count, project ID. Threads are color-coded: blue for buyers, slate for vendors.
  - **Active thread (right panel):** Message bubbles (Fiona right-aligned in fuchsia, other party left-aligned). System event pills between messages (same pattern as `buyer_messages.html`): "Permit approved · Feb 3", "Foundation verified · Mar 5". Photo attachments render inline.
  - **Emotional Anchor sidebar:** Persistent card when viewing a buyer thread — shows buyer motivation + tone guidance. Hidden when viewing vendor threads (replaced with vendor compliance score).
  - **Template selector:** Dropdown above textarea with pre-written templates categorized by scenario: "Milestone approaching", "Permit update", "Exception notification", "Crane Day prep", "Project complete". Selecting a template populates the textarea with merge fields ({{buyer_name}}, {{milestone}}, {{amount}}).
  - **Tone indicator:** Small badge next to textarea showing current tone guidance: "Grandparent-friendly" (pink) or "Standard" (slate) — pulled from the buyer's emotional anchor.
- **Key interaction:** Click thread to load conversation. Select template to populate message. Send message. Attach photo.
- **Complexity:** **High** (multi-thread inbox + template engine + emotional context switching)

#### Screen 7: `concierge_permit_tracker.html`
- **Purpose:** Portfolio-wide permit SLA dashboard
- **What Fiona sees:**
  - **Summary bar:** 3 KPI pills — In Review (3), Approaching SLA (1, amber), Overdue (0, emerald "clear")
  - **Permit table:** All active permits across Fiona's portfolio. Columns: Project ID, Homeowner, City, Application #, Filed Date, SLA Deadline, Days Remaining (color-coded: green >14d, amber 7-14d, red <7d), Status (In Review / Deficiency / Approved), Last City Action.
  - **Proactive notification drafts:** When a permit hits the amber zone (7-14 days remaining), an expandable card appears below the row with a pre-drafted buyer notification: "Hi {{name}}, your permit is in city review and on track. Our permit runner checked in today — no deficiencies flagged. We'll notify you the moment it's approved." Fiona can edit and send.
  - **Deficiency alert card:** If a city reviewer flags a deficiency, a red-bordered card surfaces with: deficiency description, Fiona's action options (respond via permit runner / notify buyer / escalate).
- **Key interaction:** Sort/filter table. Expand notification drafts. Edit and send proactive messages.
- **Complexity:** Medium

#### Screen 8: `concierge_crane_day.html`
- **Purpose:** Crane Day operations command center
- **What Fiona sees:**
  - **Upcoming deliveries list:** Cards for each delivery in the next 30 days. Each card: project ID, homeowner, address, delivery date, crane operator assigned, status (Confirmed / Pending / At Risk).
  - **Active delivery detail** (expanded card for the next delivery):
    - Pre-delivery checklist: 6 items (site access confirmed, crane clearance verified, utility pre-staging complete, camera shipped to buyer, spectator link generated, weather check — clear/rain/wind with go/no-go badge)
    - Crane operator card: name, company, phone, crane type, confirmed ETA
    - Spectator link section: generated URL, copy button, "Send to buyer" quick-action
    - Weather widget: 3-day forecast for delivery address, wind speed threshold indicator
  - **Post-delivery section:** "Set Complete" confirmation → triggers buyer notification + confetti on Annie's screen + close-out sequence initiation
- **Key interaction:** Toggle checklist items. Copy spectator link. Send to buyer. Confirm set-complete.
- **Complexity:** Medium

### Peripheral

#### Screen 9: `concierge_settings.html`
- **Purpose:** Fiona's account and operational preferences
- **What Fiona sees:**
  - **Shift management:** Current shift status (On Shift / Off Shift toggle), shift schedule display, coverage partner (backup concierge name + handoff notes)
  - **Message templates:** Library of all message templates, grouped by scenario. Click to preview. "Edit" opens inline editor. "New Template" button. Each template shows merge fields used.
  - **Notification preferences:** Toggle matrix — which events trigger Fiona's alerts (new triage item, SLA approaching, buyer message, milestone submitted, permit update). Channel options: in-app, email, SMS.
  - **Portfolio overview:** Read-only list of all assigned projects with current phase — a lightweight version of the dashboard's active projects table.
- **Key interaction:** Toggle shift status. Edit/preview message templates. Toggle notification channels.
- **Complexity:** Low

---

## Design System Elements

### Shared Chrome (established by `concierge_dashboard.html` refactor)

```
┌─────────────────────────────────────────────────────────────────┐
│ [layers icon] ORCHESTRATION OS          Active Shift: Fixer Fiona [avatar] │  ← Dark gradient nav
├──────────┬──────────────────────────────────────────────────────┤
│          │                                                      │
│ Triage   │  KPI Cards / Main Content Area                       │
│ Queue (4)│                                                      │
│          │  Background: #F1F5F9                                  │
│ Active   │  Cards: white, rounded-2xl, colored left-border      │
│ Projects │                                                      │
│          │                                                      │
│ Permit   │                                                      │
│ SLAs     │                                                      │
│          │                                                      │
│ Crane    │                                                      │
│ Calendar │                                                      │
│          │                                                      │
│ Messages │                                                      │
│          │                                                      │
│ Settings │                                                      │
├──────────┴──────────────────────────────────────────────────────┤
│ (no footer — full-height app layout)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Color-Coded Left Borders (triage severity)

| Color | Meaning | CSS |
|---|---|---|
| Fuchsia `#D946EF` | Active/primary | `border-l-4 border-l-fuchsia-500` |
| Amber `#F59E0B` | Warning / approaching SLA | `border-l-4 border-l-amber-500` |
| Orange `#F97316` | Mediation required | `border-l-4 border-l-orange-500` |
| Red `#EF4444` | Critical / overdue | `border-l-4 border-l-red-500` |
| Emerald `#10B981` | Approved / on-track | `border-l-4 border-l-emerald-500` |

### Standard Data — Annie's Project (used across all screens)

| Field | Value |
|---|---|
| Project ID | ORD-9021 |
| Homeowner | Annie Morrison |
| Address | 742 SE Morrison St, Portland OR 97214 |
| Zone | R5 |
| Model | Cascadia Studio 480 (Cascadia Modular, Hillsboro OR) |
| All-in total | $172,000 |
| Site GC | Pacific Foundation Works (Portland/HIL) |
| Permit | #2026-04-1822 (Portland BDS) |
| Emotional anchor | Housing for aging parents · Grandparent-friendly tone |
| Concierge | Fixer Fiona |
| Crane operator | Rigging Northwest (Portland) |

---

## GitHub Issues & Execution Model

Each issue is executed via `/new-pr-auto`. Issues are grouped into 5 batches. **Execute batches in order** — later screens cross-link to earlier ones and inherit the shared chrome established in Batch 1.

### Batch 1: Core Console

Establishes the shared nav, sidebar, KPI pattern, and table styles. All subsequent screens inherit this chrome.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| F-1 (#37) | Concierge mock index | `concierge_index.html` | Low | Card list of all 8 screens with descriptions and batch badges. Same pattern as `buyer_index.html`. **✅ DONE — PR #47 merged 2026-04-04** |
| F-2 (#38) | Concierge dashboard (refactor) | `concierge_dashboard.html` | **High** | Refactor existing file. KPI row (4 cards), triage queue table, active projects table, sidebar nav with badge counts. Removes existing inline triage cards (content moves to F-5). **✅ DONE — PR #48 merged 2026-04-04** |

### Batch 2: Project Lifecycle

The two screens Fiona lives in daily — project detail and milestone review.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| F-3 (#39) | Project detail (5-state lifecycle) | `concierge_project_detail.html` | **High** | 5 states: Intake → Permit → Active Build → Transit → Close-out. Stakeholder panel, Track A/B sync, emotional anchor card, coordinator notes. State-switcher demo panel. **✅ DONE — PR #49 merged 2026-04-05** |
| F-4 (#40) | Milestone review + fund release | `concierge_milestone_review.html` | Medium | Photo evidence grid (GPS-tagged), verification checklist, approve/reject/escalate with confirmation modal. Emotional anchor card. **✅ DONE — PR #50 merged 2026-04-05** |

### Batch 3: Exception Handling

Single screen absorbing both vendor exceptions and buyer disputes from the existing dashboard.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| F-5 (#41) | Triage detail (exception + dispute) | `concierge_triage_detail.html` | Medium | 2-state: vendor exception (material sub) + buyer dispute (payment delay). Context pane → action pane layout. SLA timer. Confirmation modal on force-payout. **✅ DONE — PR #51 merged 2026-04-05** |

### Batch 4: Communication & Tracking

Fiona's information and coordination screens.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| F-6 (#42) | Messages (multi-thread inbox) | `concierge_messages.html` | **High** | Thread list (left) + conversation (right) + emotional anchor sidebar. Template selector with merge fields. Tone indicator badge. System event pills. **✅ DONE — PR #52 merged 2026-04-05** |
| F-7 (#43) | Permit SLA tracker | `concierge_permit_tracker.html` | Medium | Portfolio-wide permit table with SLA color-coding. Proactive notification drafts. Deficiency alert cards. |
| F-8 (#44) | Crane Day operations | `concierge_crane_day.html` | Medium | Upcoming deliveries list. Pre-delivery checklist. Crane operator assignment. Weather widget. Spectator link generation. |

### Batch 5: Peripheral + Polish

Settings screen and documentation audit.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| F-9 (#45) | Concierge settings | `concierge_settings.html` | Low | Shift management, message template library, notification preferences, portfolio overview. |
| F-10 (#46) | RATIONALE.md + cross-link audit | None (documentation) | Low | Overwrite RATIONALE.md with all 9 screen entries. Verify cross-links. Update `concierge_index.html` if filenames changed. |

**Total: 10 issues across 5 batches. 9 screens.**

---

### Parallel Execution Rules

Issues **within** the same batch create different files and use separate worktrees/branches — they are safe to run simultaneously with `/new-pr-auto`.

Issues **across** batches have dependency on the shared chrome established in Batch 1. Merge each batch before starting the next.

```
# Batch 1 — Core Console (must merge before Batch 2)
/new-pr-auto 37   # F-1: concierge_index
/new-pr-auto 38   # F-2: concierge_dashboard (refactor)

# Batch 2 — Project Lifecycle
/new-pr-auto 39   # F-3: concierge_project_detail (5-state)
/new-pr-auto 40   # F-4: concierge_milestone_review

# Batch 3 — Exception Handling
/new-pr-auto 41   # F-5: concierge_triage_detail (2-state)

# Batch 4 — Communication & Tracking
/new-pr-auto 42   # F-6: concierge_messages
/new-pr-auto 43   # F-7: concierge_permit_tracker
/new-pr-auto 44   # F-8: concierge_crane_day

# Batch 5 — Peripheral + Polish
/new-pr-auto 45   # F-9: concierge_settings
/new-pr-auto 46   # F-10: RATIONALE.md + cross-link audit
```

### RATIONALE.md Strategy

Same approach as the buyer suite: **defer all RATIONALE.md entries to F-10.** Individual issues skip RATIONALE work — F-10 writes all 9 entries from scratch and audits cross-links.

---

## Image Strategy

The concierge console is a data-heavy ops tool — fewer hero images than the buyer suite, more structured data displays.

| Category | Image Source | Rationale |
|---|---|---|
| Fiona's avatar | pravatar `?img=32` | Same avatar used across all three persona suites |
| Milestone evidence photos | Unsplash (construction, foundation, framing) | Same photos Annie sees — Fiona reviews what GCs upload |
| Stakeholder avatars | pravatar (varied `?img=` values) | Quick differentiation of Annie, Mike, GC contacts |
| Weather widget | Static text/icons (no API) | Simulated 3-day forecast — Lucide cloud/sun/wind icons |
| Crane operator | No photo needed | Name + company + phone is sufficient for ops context |

---

## Relationship to Other Persona Suites

Fiona's screens are the **operational backend** of what Annie and Mike see on the frontend:

| Annie sees... | Mike sees... | Fiona manages... |
|---|---|---|
| "Permit filed, Fiona is tracking" | (nothing — not his project) | Permit SLA countdown, proactive notifications |
| Milestone photo gallery | Photo upload confirmation | GPS verification, checklist review, fund release |
| "Fiona: Your foundation is verified!" | "$37,500 draw released" | Triage → review → approve flow |
| Crane Day countdown + live stream | Delivery dispatch confirmation | Crane operator assignment, weather check, camera setup |
| "I'm Fiona, your project coordinator" | (never sees this) | Intake form, emotional anchor setup, intro message generation |
| Share modal + spectator link | (nothing) | Spectator link generation, delivery confirmation |

This three-persona model — buyer sees trust, vendor sees cash, concierge sees operations — is the complete Yardstake UX story.
