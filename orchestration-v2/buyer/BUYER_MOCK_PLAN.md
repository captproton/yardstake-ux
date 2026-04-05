# Buyer Persona Mock Plan: "Anxious Annie"

**Location:** `user_experience/orchestration-v2/buyer/`
**Author:** Opus (architecture) → Sonnet (implementation via `/new-pr-auto`)
**Execution:** 10 GitHub issues across 6 batches → `/new-pr-auto <issue_number>`
**Date:** April 4, 2026

---

## Context

The vendor persona ("Modular Mike") has 19 production-quality HTML mocks in `orchestration-v2/vendor/`, covering the full lifecycle from application through delivery. The buyer persona ("Anxious Annie") has one partial mock (`buyer_dashboard.html`) — a project hub showing the "Move That Bus" tracker, milestone approval, in-transit banner, and three-bucket ledger. This plan defines the complete buyer mock suite to match the vendor coverage.

### Source Documents

| Document | Role |
|---|---|
| `Macro PRD: Yardstake Digital Concierge` | North-star UX vision — 7 phases, "wedding planner" emotional layer |
| `docs/plans/annie/mocks/BUYER_PHASE2_EXPERIENCE_SPEC.md` | Phase 2 orchestration buyer spec — screen-by-screen wireframes |
| `docs/plans/annie/mocks/BUYER_EXPERIENCE_SPEC.md` | Phase 1 reference (superseded but useful for existing screen inventory) |
| `orchestration-v2/buyer/buyer_dashboard.html` | Existing partial mock — project hub mid-build state |
| `orchestration-v2/vendor/RATIONALE.md` | Pattern reference — how vendor mocks were documented |

### What Already Exists (Reusable)

- **`buyer_dashboard.html`** — "Move That Bus" dual-track progress, milestone photo approval widget, three-bucket ledger, in-transit banner. Light theme (white glass cards on `#F8FAFC`). This is the **mid-project active state**. **Disposition: DELETE when `buyer_project_hub.html` is built.** Its content is absorbed as State C of the project hub. The original widgets (dual-track bar, milestone approval, three-bucket ledger, in-transit banner) should be replicated inside that state — there's no reason to preserve the standalone file.
- **`docs/plans/annie/mocks/01_dashboard.html` through `04_inquiry.html`** — Phase 1 mocks (light Tailwind, no glassmorphism). These are **superseded** by orchestration-v2 but useful as content reference for the pre-project screens.
- **`RATIONALE.md`** — Current file has 3 stub entries describing `buyer_dashboard.html`. **Disposition: OVERWRITE from scratch** when the first screen is built. Start numbering from #1. Follow the vendor RATIONALE.md pattern exactly (section header → file → UI bullets → rationale paragraph).

---

## Design System: Buyer vs. Vendor

| Property | Vendor (Mike) | Buyer (Annie) |
|---|---|---|
| Background | Dark slate `#0F172A` | Light warm `#F8FAFC` |
| Card style | Dark glassmorphism (`rgba(30,41,59,0.7)`, blur) | Light glassmorphism (`rgba(255,255,255,0.9)`, blur) |
| Accent | Emerald (payouts), purple (stations) | Blue-to-cyan gradient (trust, calm) |
| Typography | Plus Jakarta Sans | Plus Jakarta Sans |
| Icons | Lucide | Lucide |
| Emotional register | "Cash register" — urgency, payout velocity | "Wedding planner" — reassurance, transparency, celebration |
| Mobile pattern | Factory-floor snap-scroll, SMS magic links | Responsive desktop-first, SMS notifications |

**The buyer UI is NOT dark mode.** Annie is a homeowner on her laptop or phone, not a factory worker. The existing `buyer_dashboard.html` already establishes the correct light, airy tone. All new mocks inherit this.

---

## Screen Inventory (14 Screens)

Organized by the buyer journey phases from the Macro PRD and Phase 2 spec. Each entry names the file, the journey phase, the primary user action, and the key emotional beat.

### Phase 0–1: Discovery & Free Feasibility

#### Screen 1: `buyer_landing.html`
- **PRD Phase:** 1 — The Magic Portal
- **What Annie sees:** City landing page for Portland. Address autocomplete input. "Can I build an ADU?" headline. Quick stats (847 qualifying parcels in Portland, avg build 6 months, from $150K). Above-the-fold CTA: "Check My Address — Free."
- **Key interaction:** Address entry → instant confidence tier result (High/Medium/Low) rendered inline below the input (no page change). "Get My Full Report — $49" upsell card with bullet list of what's included.
- **Emotional beat:** Instant gratification. Annie gets an answer in seconds, not weeks.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §0A–1A

#### Screen 2: `buyer_report.html`
- **PRD Phase:** 2 — Financial Engine + Phase 3 — Catalog
- **What Annie sees:** Full feasibility report (post-$49 purchase). Confidence tier, exact setback calculations, buildable envelope with parcel outline diagram, permit pathway, Oregon financing guide (HELOC, OHCS, FHA 203k). **Phase 2 additions:** Full project cost estimate (three-bucket breakdown), escrow/custodial funds explainer, matched models preview with "Start My Project" CTA.
- **Key interaction:** PDF download button. "View Matched Models →" and "Start My Project →" CTAs.
- **Emotional beat:** "I'm not guessing anymore — I know exactly what this costs." Removes sticker shock by showing all-in pricing upfront.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §3B

### Phase 3: Catalog & Configuration

#### Screen 3: `buyer_models.html`
- **PRD Phase:** 3 — Prefab Catalog
- **What Annie sees:** 3 matched manufacturer models (cards). Each card: hero photo, model name + specs (1BR/1BA/480sqft), unit price, all-in estimated total, verified partner badge, preferred Site GC name + note, "View Details" and "Start My Project →" CTAs.
- **Key interaction:** Click "View Details" → opens `buyer_configurator.html`. Click "Start My Project" → opens `buyer_project_agreement.html`.
- **Emotional beat:** "These actually fit MY lot." Confidence that matching was done for her.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §3C

#### Screen 4: `buyer_configurator.html`
- **PRD Phase:** 3 — Customization Studio
- **What Annie sees:** Visual option selection for the chosen model. Image cards per option (the buyer side of what Mike configured in `vendor_model_options.html`). Grouped by 5 section dividers: Exterior, Kitchen, Bathroom, Flooring & Interior, Add-ons. **Only Exterior expanded by default** — all other sections show a collapsed summary: "Standard included · (customize)". Pick-one categories show radio-card pattern (select one, others dim). Add-on categories show checkbox cards. Color categories show large swatches. Running total at bottom updates live, starting at $0 uplift.
- **Key interactions:** Click section to expand → reveal image cards. Select option → card highlights with blue ring, price delta animates into running total. Selecting a non-standard option in a pick-one category auto-deselects the previous choice. "Confirm Selections & Continue →" locks options and routes to project agreement.
- **Emotional beat:** "I'm designing MY home, not choosing from a spreadsheet." This is the "Customization Studio" from the Macro PRD — the moment Annie goes from browser to buyer.
- **Content source:** Macro PRD §4 (Dynamic Pricing Calculator), vendor_model_options.html (data structure)
- **Data connection:** The categories, options, images, price deltas, and selection types all come from what Mike configured in the vendor option tree editor. Annie sees the buyer-facing presentation of Mike's data.

### Phase 4: Project Initiation

#### Screen 5: `buyer_project_agreement.html`
- **PRD Phase:** 4 — Project Hub setup
- **What Annie sees:** Project agreement page. Model + property summary at top. "How This Works" explainer (4 points: Yardstake manages, phased deposits, milestone verification, Fiona assigned). Phased deposit schedule table (Permit $5K → Foundation $25K → Factory $100K → Delivery remaining). Project summary (manufacturer, GC, permitting — all named). Property authorization checkbox (owner name from Regrid cross-check). Agreement checkbox + PDF link. "Continue →" proceeds to initial deposit.
- **Key interaction:** Check both boxes → "Continue" activates. Property name mismatch → amber warning with explanation (doesn't block, flags for Fiona).
- **Emotional beat:** "I understand what I'm signing. I'm not depositing everything upfront." Phased deposits are the anxiety killer.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §4A

#### Screen 6: `buyer_deposit.html`
- **PRD Phase:** 4 — Initial deposit
- **What Annie sees:** Clean summary card (model, address, deposit amount). Trust messaging: "Funds held by Yardstake — not released until permit approved and verified." Single "Deposit $5,000 →" CTA button (no fake Stripe card form — the button is the interaction). Two states:
  - **State 1 — Deposit:** Summary + trust copy + CTA.
  - **State 2 — Confirmed:** 1.5s processing spinner → confetti burst → confirmation card with Fiona's intro ("I'm Fiona, your project coordinator. I'll text you at every milestone."), project next-steps, and "Go to Project Hub →" link.
- **Key interaction:** Click deposit → processing animation → confetti → Fiona intro confirmation.
- **Emotional beat:** Confetti + Fiona intro = "this is real, and someone has my back."
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §4B, Macro PRD §2 (confetti on funding verified)

### Phase 5: Project Hub (Active Build)

#### Screen 7: `buyer_project_hub.html` (refactor of existing `buyer_dashboard.html`)
- **PRD Phase:** 5 — Homeowner Command Center
- **What Annie sees:** The primary long-duration screen (Annie visits this for 6–12 months). Multi-state:
  - **State A — Permit phase:** Progress bar (1 of 7 lit). Current phase card: "Permit filed with Portland — est. 3–6 weeks." Fiona note card. Funds summary (3 tiles: deposited, requested, remaining).
  - **State B — Foundation phase:** Progress bar (2 of 7). Action card: "Foundation deposit requested — $25,000." Photo update from Pacific FW.
  - **State C — Factory build (active):** This is roughly the current `buyer_dashboard.html` state. "Move That Bus" dual-track bar. Milestone photo approval widget. Three-bucket ledger.
  - **State D — In transit:** In-transit banner with GPS progress (already exists in current mock). Crane day countdown.
  - **State E — Utility hookup / final:** Progress bar (6 of 7). Utility work status. Fiona scheduling inspection.
- **Key interactions:** State-switching demo buttons (like vendor mocks). Approve & Release Funds button on milestone cards. Message Fiona CTA.
- **Emotional beat:** "I always know where my ADU is." The "wedding planner app" — checking on progress is exciting, not stressful.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §5A, existing buyer_dashboard.html, Macro PRD §5

#### Screen 8: `buyer_milestone_detail.html`
- **PRD Phase:** 5 — Milestone Payments & Proof of Work
- **What Annie sees:** Full-screen milestone detail. Milestone name + date + verified badge. 3 GPS-tagged photo gallery (from factory floor — same photos Mike uploaded via vendor dashboard). "What Was Verified" checklist. "What Happens Next" note. Funds released amount + status. Back to project hub.
- **Key interaction:** Photo lightbox (click to expand). Photos are view-only — Annie doesn't upload, she reviews.
- **Emotional beat:** "I can SEE my ADU being built, photo by photo." This is the trust engine.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §5B

### Phase 6: Communication

#### Screen 9: `buyer_messages.html`
- **PRD Phase:** 5 — Fiona interaction
- **What Annie sees:** Single message thread with Fiona (concierge). NOT a multi-conversation inbox — Annie talks to one person. Fiona's avatar + "Project Coordinator" title in thread header. Message bubbles (Fiona left-aligned with headphones avatar, Annie right-aligned in blue). **System event pills** injected between messages as centered, muted-style badges: `Permit approved · Feb 3` / `Foundation verified · Mar 5` / `Factory framing photos uploaded · Mar 25` (same visual pattern as `vendor_messages.html` system pills). Photo sharing (Annie can send photos of her backyard to Fiona). Quick-reply suggestion chips below the input ("When is crane day?", "Can I visit the factory?", "Who's my Site GC?").
- **Key interaction:** Send message, attach photo, tap quick-reply chip. System pills are non-interactive — they're context anchors in the timeline.
- **Emotional beat:** "I have a real person I can reach any time." Fiona is the safety net.
- **Content source:** Macro PRD §5 (Team Interaction), BUYER_PHASE2_EXPERIENCE_SPEC.md §4C (Fiona introduction)

### Phase 7: Delivery & Completion

#### Screen 10: `buyer_crane_day.html`
- **PRD Phase:** 7 — The "Live Drop"
- **What Annie sees:** "Crane Day" countdown / live-drop experience. Three states:
  - **State 1 — Countdown (T-48hrs):** Large countdown timer. Delivery details (date, time, what to expect). "Share with family" link (generates a public spectator URL). Fiona's note about the day.
  - **State 2 — Live (Crane Day):** Static hero image of crane setting a modular unit, overlaid with pulsing red "● LIVE" dot and viewer count ("14 watching"). GPS tracker showing truck's final approach. Chat sidebar with family reactions (simulated messages).
  - **State 2b — Spectator Mode:** What friends/family see via the shared link. Same hero image + LIVE badge, but stripped nav (Yardstake logo only, no account controls). "Annie's ADU — Crane Day!" banner. Chat sidebar. No project details or financials exposed.
  - **State 3 — Set complete:** Celebration screen — confetti, "Your ADU is home!" Large hero photo of set unit. "Next: Utility hookup begins this week" note.
- **Key interaction:** Share link (generates spectator URL), toggle chat, view live feed.
- **Emotional beat:** The peak emotional moment of the entire journey. "EXTREME MAKEOVER" energy — "Move that bus!" This is what Annie shows her friends.
- **Content source:** Macro PRD §7 (Live Drop, ActionCable Live Video Player, Shareable Public Link)

#### Screen 11: `buyer_project_complete.html`
- **PRD Phase:** 7 — Digital Handover
- **What Annie sees:** Project completion screen. All-green progress bar (7/7). CO download + permit download + full photo archive link. Project summary stats (87 days, $218,500 total, 7 milestones verified). "Share Your ADU Story →" CTA (feeds Val's content pipeline). "Leave a Review for Cascadia Modular →" (feeds public builder directory). Document vault section (CO, warranties, appliance manuals, engineering drawings).
- **Key interaction:** Download documents, leave review, share story.
- **Emotional beat:** "I did it." Pride, accomplishment, and a clean handoff to the "homeowner" phase.
- **Content source:** BUYER_PHASE2_EXPERIENCE_SPEC.md §6C, Macro PRD §7 (Digital Welcome Mat, Document Vault)

### Peripheral Screens

#### Screen 12: `buyer_notifications.html`
- **What Annie sees:** Activity feed (same pattern as `vendor_notifications.html`). Filter tabs: All · Milestones · Payments · Messages. Notifications for: deposit requested, milestone verified, photo update, Fiona message, permit approved, crane day reminder, CO issued.
- **Key interaction:** Filter by type, mark read, deep-link to relevant screen.
- **Content source:** Pattern from vendor_notifications.html

#### Screen 13: `buyer_settings.html`
- **What Annie sees:** Account settings. Simpler than vendor — Annie is a homeowner, not a business. Sections: Profile (name, email, phone), Payment Methods (Stripe/HELOC link), Notification Preferences (SMS/email toggles per event type), Security (password, 2FA), Documents (links to all project docs).
- **Content source:** Pattern from vendor_settings.html (simplified)

#### Screen 14: `buyer_index.html`
- **What Annie sees:** Index page listing all buyer screens with descriptions and links. Same pattern as `docs/plans/annie/mocks/00_index.html` but for the orchestration-v2 suite.
- **Purpose:** Navigation aid for reviewers walking the full journey.

---

## Image Strategy

Buyer mocks need product images (siding textures, kitchen finishes, roofing materials) for the configurator and model cards. Use a **mixed approach:**

| Category | Image Source | Rationale |
|---|---|---|
| Model hero photos | Unsplash (search: "modern ADU", "prefab home", "modular house backyard") | High visual impact, sets the tone |
| Siding, roofing, countertops, cabinets, flooring, shower tile | Unsplash (search: material name + "texture") | Annie needs to see the actual material |
| Exterior paint, interior paint | **CSS color swatches** (solid hex fills) | Color IS the visual — no photo needed |
| Appliances (stainless vs. white) | Unsplash (search: "modern kitchen appliances") | One hero shot per option |
| Add-ons (deck, EV charger, solar) | Unsplash (search: item name) | Lifestyle context |
| Sink style (oval vs. square) | Unsplash (search: "bathroom sink oval/square") | Shape is the differentiator |
| Factory floor milestone photos | Unsplash (search: "construction framing", "house foundation") | Already used in `buyer_dashboard.html` |
| Crane day hero | Unsplash (search: "crane modular home") | The money shot |

**Unsplash URL pattern:** `https://images.unsplash.com/photo-XXXXX?auto=format&fit=crop&w=400&q=80`

Use `w=400` for card thumbnails, `w=800` for hero images. If a specific Unsplash photo ID breaks in the future, the mock degrades gracefully to a blank rectangle — acceptable for stakeholder review mocks.

**For the configurator specifically:** Each option card should be ~160×120px image area with the option name and price delta below. Pick-one cards get a blue ring on selection. Standard/default card gets a small emerald "Included" badge.

---

## GitHub Issues & Execution Model

Each issue is executed via `/new-pr-auto`. Issues are grouped into 5 batches by journey phase. **Execute batches in order** — later screens cross-link to earlier ones. Within a batch, issues are independent and can run in parallel.

### Batch 1: Discovery & Pre-Purchase (Screens 1–4)

These screens are pre-authentication — Annie is browsing, not yet a customer. No secondary tab bar. Minimal nav on landing page.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| B-1 ✅ | Buyer index + landing page | `buyer_index.html`, `buyer_landing.html` | Medium | **Shipped — PR #21 merged 2026-04-04.** |
| B-2 ✅ | Buyer feasibility report | `buyer_report.html` | Medium | **Shipped — PR #22 merged 2026-04-04.** |
| B-3a (#23) ✅ | Matched models page | `buyer_models.html` | Low | **Shipped — PR #25 merged 2026-04-05.** |
| B-3b (#24) ✅ | Buyer configurator | `buyer_configurator.html` | **High** | **Shipped — PR #26 merged 2026-04-05.** |

### Batch 2: Project Initiation (Screens 5–6)

Annie commits. Phased deposits, Fiona introduction, confetti.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| B-4 ✅ | Project agreement + initial deposit | `buyer_project_agreement.html`, `buyer_deposit.html` | Medium | **Shipped — PR #27 merged 2026-04-05.** |

### Batch 3: Active Project (Screens 7–9)

The core long-duration experience. This is where Annie lives for 6–12 months.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| B-5 ✅ | Project hub (5-state command center) | `buyer_project_hub.html` | **High** | **Shipped — PR #28 merged 2026-04-04.** `buyer_dashboard.html` deleted. |
| B-6 ✅ | Milestone detail + messages | `buyer_milestone_detail.html`, `buyer_messages.html` | Medium | **Shipped — PR #29 merged 2026-04-04.** |

### Batch 4: Delivery & Completion (Screens 10–11)

The emotional peak and project wrap-up.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| B-7a ✅ | Crane day — scaffold + countdown + set complete | `buyer_crane_day.html` | Low | **Shipped — PR #32 merged 2026-04-04.** Countdown timer, share link, confetti, nav-swap wired. |
| B-7b | Crane day — live + spectator states | `buyer_crane_day.html` | **High** | PR #31 (STANDARD). Pulsing LIVE badge, GPS tracker, auto-chat simulation, spectator content. Depends on B-7a. |
| B-8 | Project complete + document vault | `buyer_project_complete.html` | Medium | All-green progress bar, CO download, photo archive, review CTA, share story CTA. |

### Batch 5: Peripheral Screens (Screens 12–14)

Supporting screens that follow established patterns from the vendor mocks.

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| B-9 | Notifications + settings | `buyer_notifications.html`, `buyer_settings.html` | Low-Medium | Notifications: vendor pattern adapted (filter tabs: All/Milestones/Payments/Messages). Settings: simplified vendor pattern (Profile, Payment, Notifications, Security, Documents). |

### Batch 6: Final Polish

| Issue | Title | Screens | Complexity | Notes |
|---|---|---|---|---|
| B-10 | RATIONALE.md + cross-link audit | None (documentation) | Low | Overwrite buyer RATIONALE.md with all 14 screen entries. Verify all cross-links between screens work. Update `buyer_index.html` if any filenames changed. |

**Total: 11 issues across 6 batches. 14 screens.** _(#13 split into #23 + #24)_

---

### Parallel Execution Rules

Issues **within** the same batch create different files and use separate worktrees/branches — they are safe to run simultaneously with `/new-pr-auto`.

Issues **across** batches have cross-link dependencies (later screens reference filenames from earlier screens). Merge each batch before starting the next.

```
# Batch 1 — ✅ B-1 merged (PR #21). B-2 open (PR #22).
# /new-pr-auto 11   ✅ DONE — PR #21 merged 2026-04-04
# /new-pr-auto 12   ✅ DONE — PR #22 merged 2026-04-04
# /new-pr-auto 23   ✅ DONE — PR #25 merged 2026-04-05
# /new-pr-auto 24   ✅ DONE — PR #26 merged 2026-04-05

# Batch 2 — ✅ DONE — PR #27 merged 2026-04-05
# /new-pr-auto 14   ✅ DONE — buyer_project_agreement + buyer_deposit

# Batch 3 — Batch 2 complete, ready to run
# /new-pr-auto 15   ✅ DONE — PR #28 merged 2026-04-04 — buyer_project_hub (5-state), buyer_dashboard deleted
# /new-pr-auto 16   ✅ DONE — PR #29 merged 2026-04-04 — buyer_milestone_detail + buyer_messages

# Batch 4 — run both in parallel, after Batch 3 merges
# /new-pr-auto 17   → SPLIT into #30 (B-7a) and #31 (B-7b)
# /new-pr-auto 30   ✅ DONE — PR #32 merged 2026-04-04 — scaffold + countdown + set-complete
/new-pr-auto 31   # buyer_crane_day live + spectator (STANDARD) — depends on #30/#32
/new-pr-auto 18   # buyer_project_complete

# Batch 5 — single issue, after Batch 4 merges
/new-pr-auto 19   # buyer_notifications + buyer_settings

# Batch 6 — after everything merges
/new-pr-auto 20   # RATIONALE.md + cross-link audit
```

### RATIONALE.md Conflict Avoidance

Each issue's acceptance checklist includes an "Add RATIONALE.md entry" item. If multiple issues in the same batch both write to `RATIONALE.md`, a merge conflict will result (it's the only shared file across issues in a batch).

**Resolution: defer all `RATIONALE.md` work to B-10.** Issue #20 is purpose-built to write all 14 entries from scratch and audit the result. Individual issues within a batch should skip the RATIONALE.md step — B-10 covers it comprehensively at the end.

### Issue Template

Each GitHub issue body should follow this structure so `/new-pr-auto` has full context:

```markdown
## Context
Build buyer UX mock(s) for Yardstake orchestration-v2.
- **Plan doc:** `user_experience/orchestration-v2/buyer/BUYER_MOCK_PLAN.md`
- **Batch:** N of 6
- **Screen spec:** See "Screen Inventory → Screen N" in the plan doc

## Requirements
- [ ] Read BUYER_MOCK_PLAN.md before starting (design tokens, nav pattern, data block, image strategy)
- [ ] Build screen(s): `filename.html`
- [ ] Follow buyer light theme (NOT dark mode)
- [ ] Use standard nav pattern (primary + secondary tab bar where specified)
- [ ] Use consistent Annie project data from plan doc
- [ ] Cross-link to adjacent screens per plan doc linking convention
- [ ] Add RATIONALE.md entry for each screen built (or defer to B-10 for batch update)
- [ ] All files go in: `user_experience/orchestration-v2/buyer/`

## Acceptance
- HTML file(s) open in browser with no build step
- Lucide icons render
- State machine works (for multi-state screens)
- Responsive at 390px and 1280px
- Links to adjacent screens are correct relative paths
```

---

## Sonnet Implementation Instructions

### Technical Stack (Identical to Vendor Mocks)

```html
<!-- Required in every file <head> -->
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest"></script>
```

- **No build step.** Tailwind via CDN, Lucide via unpkg.
- **Call `lucide.createIcons()` after any DOM injection** (state switches, modal opens, etc.).
- **All interactivity is vanilla JS** — no frameworks. State management via `.state { display: none; } .state.active { display: block; }` with `showState(id)` functions.
- **All data is hardcoded.** These are visual mocks, not connected to an API.

### Design Tokens (Buyer Light Theme)

```css
body {
  font-family: 'Plus Jakarta Sans', sans-serif;
  background-color: #F8FAFC;
  color: #0F172A;
}
.glass-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(226, 232, 240, 0.8);
}
.gradient-text {
  background: linear-gradient(to right, #2563EB, #06B6D4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

- **Primary accent:** Blue-600 `#2563EB` (actions, progress, trust)
- **Secondary accent:** Cyan-500 `#06B6D4` (site-prep track, secondary elements)
- **Success/celebration:** Emerald-500 `#10B981` (completed milestones, verified badges)
- **Warning/action-required:** Orange-500 `#F97316` (pending approvals, deposit requests)
- **Borders:** Slate-200 `#E2E8F0`
- **Card radius:** `rounded-[2rem]` for major sections, `rounded-xl` for inner cards
- **Content max-width:** `max-w-7xl mx-auto`

### Nav Pattern (Consistent Across All Buyer Screens)

**Primary nav (all screens):**

```html
<nav class="bg-white border-b border-slate-200 sticky top-0 z-50">
  <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
    <div class="flex items-center space-x-2">
      <i data-lucide="home" class="text-blue-600"></i>
      <span class="text-xl font-bold tracking-tight">Yard<span class="text-cyan-500">stake</span></span>
    </div>
    <div class="flex items-center space-x-6">
      <!-- Fiona quick-message chip -->
      <a href="buyer_messages.html" class="flex items-center space-x-2 bg-blue-50 px-3 py-1.5 rounded-full border border-blue-100 cursor-pointer hover:bg-blue-100 transition-colors">
        <img src="https://i.pravatar.cc/100?img=32" alt="Concierge" class="w-6 h-6 rounded-full">
        <span class="text-xs font-bold text-blue-700">Message Fiona</span>
      </a>
      <!-- Notification bell -->
      <a href="buyer_notifications.html" class="relative cursor-pointer">
        <i data-lucide="bell" class="w-5 h-5 text-slate-500"></i>
        <span class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-orange-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">3</span>
      </a>
      <!-- Avatar -->
      <a href="buyer_settings.html" class="w-8 h-8 bg-slate-900 text-white rounded-full flex items-center justify-center font-bold text-sm">A</a>
    </div>
  </div>
</nav>
```

**Secondary tab bar (screens 7–13 only — post-purchase screens where Annie has an active project):**

```html
<div class="bg-white border-b border-slate-200">
  <div class="max-w-7xl mx-auto px-6 flex space-x-8">
    <a href="buyer_project_hub.html" class="py-3 text-sm font-semibold border-b-2 border-blue-600 text-blue-700">My Project</a>
    <a href="buyer_report.html" class="py-3 text-sm font-semibold border-b-2 border-transparent text-slate-500 hover:text-slate-700">My Report</a>
    <a href="buyer_messages.html" class="py-3 text-sm font-semibold border-b-2 border-transparent text-slate-500 hover:text-slate-700">Messages</a>
  </div>
</div>
```

The active tab gets `border-blue-600 text-blue-700`. Inactive tabs get `border-transparent text-slate-500`. Pre-purchase screens (1–6) do NOT show the secondary bar — Annie doesn't have a project yet.

**Exception — `buyer_landing.html`:** Uses a minimal nav variant (Yardstake logo + "Already have an account? Sign in" link). No Fiona chip, no bell, no avatar. Annie isn't authenticated at this point.

**Exception — `buyer_crane_day.html` State 2b (Spectator Mode):** Stripped nav — Yardstake logo only. No account controls, no tabs. Public viewers see nothing about Annie's account.

### State Machine Pattern

For multi-state screens (project hub, crane day, deposit), use this pattern:

```html
<div id="state-permit" class="state active"> ... </div>
<div id="state-foundation" class="state"> ... </div>
<div id="state-factory" class="state"> ... </div>

<!-- Demo state switcher (bottom of page, dashed border) -->
<div class="max-w-7xl mx-auto px-6 py-4 mt-8 border-2 border-dashed border-slate-300 rounded-2xl">
  <p class="text-xs font-bold text-slate-400 uppercase mb-3">Demo: Switch State</p>
  <div class="flex flex-wrap gap-2">
    <button onclick="showState('state-permit')" class="text-xs px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 font-semibold">Permit Phase</button>
    <!-- ... more states -->
  </div>
</div>
```

```css
.state { display: none; }
.state.active { display: block; }
```

```js
function showState(id) {
  document.querySelectorAll('.state').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  lucide.createIcons();
}
```

### Annie's Project Data (Use Consistently)

```
Homeowner:     Annie K.
Property:      742 SE Morrison St, Portland, OR 97214
Zone:          R5 — Low-Density Residential
Lot:           6,200 sq ft
Model:         Cascadia Studio 480 (Cascadia Modular, Hillsboro OR)
Specs:         1BR / 1BA / 480 sq ft · Modular
Unit price:    $125,000 (fixed — "The Box")
Site prep:     $35,000 (allowance — "The Dirt")
Permits/fees:  $12,000 (allowance — "The Red Tape")
Total:         $172,000
Platform fee:  5% of GTV (included in above)

Concierge:     Fiona (concierge@yardstake.com, 503-555-0142)
Manufacturer:  Cascadia Modular (Modular Mike)
Site GC:       Pacific Foundation Works ("Backyard Bill")
Permit #:      Portland ADU #2026-04-1822

Deposit schedule:
  Phase 1 (Permit):      $5,000
  Phase 2 (Foundation):  $25,000
  Phase 3 (Factory):     $100,000
  Phase 4 (Delivery):    $42,000 (remaining balance)

Key dates (for milestone mocks):
  Jan 15  Report purchased
  Jan 20  Project agreement signed, $5K deposited
  Feb 03  Permit approved
  Feb 10  Foundation deposit, site prep begins
  Mar 05  Foundation complete
  Mar 10  Factory build deposit, production begins
  Mar 25  Factory framing complete
  Apr 10  Factory MEP complete
  Apr 12  Unit ships
  Apr 14  Crane day — unit set on foundation
  Apr 28  Utility hookup complete
  May 05  CO issued — project complete

Total duration: ~107 days (Jan 20 → May 5)
```

### Cross-Linking Convention

Every screen should link to adjacent journey screens. Use relative paths (all files in the same directory):

```
buyer_landing.html → buyer_report.html → buyer_models.html
  → buyer_configurator.html → buyer_project_agreement.html
  → buyer_deposit.html → buyer_project_hub.html
  → buyer_milestone_detail.html
  → buyer_crane_day.html → buyer_project_complete.html

Peripheral (accessible from nav on any screen):
  buyer_messages.html
  buyer_notifications.html
  buyer_settings.html
  buyer_index.html (home)
```

### RATIONALE.md Updates

After each screen is built, add a numbered entry to `orchestration-v2/buyer/RATIONALE.md` following the vendor pattern:

```markdown
### N. Screen Title
- **File:** `filename.html`
- **UI:** Bullet-point description of what's on screen.
- **Rationale:** Why this screen exists — what anxiety it resolves, what business goal it serves, how it connects to the orchestration model.
```

---

## Quality Checklist (Per Screen)

Before marking a screen complete:

- [ ] Plus Jakarta Sans font loaded
- [ ] Lucide icons render (call `lucide.createIcons()` after DOM injection)
- [ ] Responsive: looks reasonable at 390px (phone) and 1280px (desktop)
- [ ] Nav bar matches the standard pattern above
- [ ] All links to other buyer screens use correct filenames
- [ ] Consistent data: Annie's name, address, model, prices match the data block above
- [ ] State switcher works (for multi-state screens)
- [ ] No dead-end screens — every screen has a "next" CTA or back link
- [ ] RATIONALE.md entry written

---

## Gap Analysis: What `buyer_dashboard.html` Contributes to `buyer_project_hub.html`

The existing file is a strong mid-project snapshot. Its widgets are absorbed into State C (Factory Build) of the new 5-state project hub. **Delete `buyer_dashboard.html` after `buyer_project_hub.html` is built (issue B-5).**

| Widget in `buyer_dashboard.html` | Destination in `buyer_project_hub.html` |
|---|---|
| "Move That Bus" dual-track progress bar | State C — factory build active state. Also add a 7-node linear progress bar (permit → CO) to ALL states as a persistent header. |
| Milestone approval widget (foundation photo review) | State C — but parameterized per milestone (foundation, framing, MEP). Different photos and draw amounts per state. |
| Three-bucket ledger (Box / Dirt / Red Tape) | Persistent across all states as the "Project Ledger" section. Values don't change — it's a reference. |
| In-transit banner (GPS progress, ETA) | State D — transit state only. |
| Fiona chip in nav | Carried forward to all states via standard nav pattern. |
| N/A (not in current file) | 7-node progress bar, funds summary strip (deposited/requested/remaining), Fiona note card per state, secondary tab bar, demo state-switcher, links to milestone detail / messages / settings. |

---

## Design Decisions (Resolved)

### 1. Configurator depth → All 13 categories, collapsed-by-default with "Standard included" pre-selected

Show all 13 categories grouped under the 5 section dividers (Exterior / Kitchen / Bathroom / Flooring & Interior / Add-ons). **Only the Exterior section is expanded by default.** Every category shows a collapsed summary line: "Standard included · (customize)" — clicking expands to reveal image cards. The running total starts at $0 uplift. Annie who wants vanilla scrolls past. Annie who wants Coastal White siding opens the Exterior section and picks it. This mirrors Tesla's configurator: everything has a default, you only touch what you care about. The full 13-category set ensures Mike's option tree isn't artificially truncated on the buyer side.

### 2. Live video on crane day → Static image + pulsing "LIVE" badge, no hosted video

A static hero image of a crane setting a modular unit, overlaid with a pulsing red "● LIVE" dot, a viewer count ("14 watching"), and a simulated chat sidebar. These are stakeholder-review mocks — a looping video adds hosting complexity without improving the UX narrative. The static approach sells the concept.

### 3. Spectator link → Yes, include a minimal spectator view as a sub-state of `buyer_crane_day.html`

The shareable public link is one of the Macro PRD's strongest viral hooks ("friends and family watch the unit being lifted"). Add a **State 2b — Spectator Mode** inside the crane day state machine: same hero image + LIVE badge, but stripped nav (Yardstake logo only, no account controls), a "Annie's ADU — Crane Day! 🏗" banner, and the chat sidebar. This is what the shared URL renders. ~20 extra lines of HTML inside the existing states — minimal cost, strong demo value.

### 4. Payment UX → Single "Deposit $X" button + processing spinner + confetti confirmation. No fake Stripe form.

Fake card number fields train nobody and look uncanny valley. Instead: a clean summary card (model, address, deposit amount), trust messaging ("Funds held by Yardstake — not released until milestone verified"), a single "Deposit $5,000 →" CTA button, then a 1.5s processing spinner → confetti burst → confirmation card with Fiona's intro ("I'm Fiona, your project coordinator. I'll reach out within 24 hours."). This matches the vendor SMS payout pattern — the button IS the interaction.

### 5. Fiona messages → Single thread. Vendor updates arrive as system event pills, not Fiona messages.

Annie talks to **one person: Fiona.** She never sees "Modular Mike" or "Backyard Bill" directly — that's the entire value proposition of the managed marketplace. Fiona's thread includes auto-generated **system event pills** injected between messages: `Permit approved · Feb 3` / `Foundation verified · Mar 5` / `Factory framing photos uploaded · Mar 25`. These are visually distinct from Fiona's conversational messages (centered pills with muted styling, same pattern as `vendor_messages.html`). Fiona's own messages are proactive updates and responses to Annie's questions. The thread becomes Annie's single source of truth — every project event and every human interaction in one scroll.
