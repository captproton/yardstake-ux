# Rationale: Buyer UX under the Orchestration Model

**Location:** `user_experience/orchestration-v2/buyer/`
**Persona:** "Anxious Annie" — Portland homeowner, 742 SE Morrison St, Zone R5
**Suite:** 13 production-quality HTML mocks across 6 batches (`buyer_dashboard.html` superseded by PR #28)

This document records the design rationale for each screen in the buyer mock suite. It explains how each UI feature connects to the core business logic of the Yardstake Phase 2 Orchestration Model, where the buyer experiences a fully managed "wedding planner" service — not a marketplace. Each entry documents key UI features and the specific product reasoning behind design choices that might otherwise appear arbitrary.

**Design System Summary:**
- Background: `#F8FAFC` (light warm) — Annie is a homeowner on a laptop, not a factory worker
- Cards: `rgba(255,255,255,0.9)` glass with blur — airy, trustworthy
- Accent: blue-to-cyan gradient (`#2563EB → #06B6D4`) — calm, forward motion
- Typography: Plus Jakarta Sans · Icons: Lucide · No dark mode

---

## Screen 1: `buyer_landing.html`

**File:** `orchestration-v2/buyer/buyer_landing.html`

**UI Features:**
- Pre-auth minimal nav (logo + "Sign in" link only — no project chrome)
- City stats bar: 847 qualifying Portland parcels, 6-month avg build, from $150K
- Address autocomplete input with "Check My Address — Free" CTA
- `runCheck()` triggers 1.5s simulated fetch → result card slides up inline (no page change)
- Confidence tier badge ("Likely Qualifies", emerald) + zone, buildable sq ft, permit type stats
- $49 report upsell card with bullet list and CTA — appears only after positive result
- "Free check — no account required" microcopy beneath input

**Rationale:** The landing page must perform a single job in under 5 seconds: turn "Can I even do this?" into "Oh wow, I might actually be able to do this." The inline result — no redirect, no form, no account — collapses the time between curiosity and confidence. The confidence tier badge uses "Likely Qualifies" rather than "Approved" because ADU eligibility is multi-factor; but "likely" rather than "possible" is intentional — Annie needs optimism, not legal hedging. The $49 upsell appears only after the validating moment, not before: it earns its place by immediately following the positive result rather than demanding money upfront.

---

## Screen 2: `buyer_report.html`

**File:** `orchestration-v2/buyer/buyer_report.html`

**UI Features:**
- Post-purchase authenticated nav (Fiona chip, bell, "A" avatar) — report implies purchase
- "Your Portland ADU Feasibility Report" hero heading with address + purchase date
- "Download PDF" button with toast confirmation
- 4-stat parcel grid (Zone, Buildable Area, Permit Type, Est. Timeline)
- Buildable envelope section with setback calculations, 800 sq ft result
- Three-bucket cost breakdown: The Box ($125K fixed), The Dirt ($35K variable allowance), The Red Tape ($12K variable)
- Portland-specific permit pathway (administrative review, no discretionary hearing required)
- Oregon financing guide (HELOC, OHCS, FHA 203k) with estimated monthly payment
- Matched model preview cards → "View Details" / "Start My Project →" dual CTAs

**Rationale:** The feasibility report is the pivot point of the funnel — Annie paid $49 and is looking for justification. The three-bucket breakdown is the central trust mechanic: separating the fixed factory cost from the variable site costs reframes the all-in number from "scary $172K" to "I know exactly what I'm signing up for." The financing section is actionable, not marketing copy — specific loan products available to a Portland homeowner in 2026. The matched model cards at the bottom are a deliberate conversion mechanism: the report ends with Annie already seeing her options, momentum intact.

---

## Screen 3: `buyer_models.html`

**File:** `orchestration-v2/buyer/buyer_models.html`

**UI Features:**
- "3 models match your lot" heading with parcel spec breadcrumb (zone, buildable sq ft, address)
- "Best Match for Your Lot" ribbon on Cascadia Studio 480 (primary model)
- Each card: hero photo, model specs (1BR/1BA/480sqft/modular), unit price in gradient text, all-in total with three-bucket sub-breakdown, verified partner badge
- Site GC assignment callout per model (Pacific Foundation Works named + rationale)
- Dual CTAs per card: "View Details" → configurator, "Start My Project →" → agreement
- "Ask Fiona" chip in page-level footer banner

**Rationale:** Three options is intentional — enough to feel like real choice, not so many that Annie spends an hour comparing. The "Best Match" ribbon eliminates the blank-slate problem by giving Annie a recommended starting point she can deviate from. The Site GC callout is a detail no competitor shows: it tells Annie that Cascadia Modular and Pacific Foundation Works have already worked together on her unit type, removing the hidden anxiety that "the site crew won't know what to do with a factory-built unit."

---

## Screen 4: `buyer_configurator.html`

**File:** `orchestration-v2/buyer/buyer_configurator.html`

**UI Features:**
- Sticky header: model name, base price, live upgrade delta, running total (gradient text)
- 5 collapsible sections: Exterior (expanded by default), Kitchen, Bathroom, Flooring & Interior, Add-ons
- Collapsed sections show "Standard included · (customize)" — no cognitive load until opened
- Pick-one categories: radio-card pattern — selecting one auto-deselects previous; selected card gets blue ring, others dim to 60%
- Add-on categories: checkbox cards — independent selection, each shows +$N delta
- Color categories: large CSS swatch cards (color IS the visual — no photo needed)
- "Included" emerald badge on default/standard options
- "Confirm Selections & Continue →" sticky footer with running total — always visible

**Rationale:** The configurator is the "I'm designing MY home" emotional transition. The single-expand-by-default design paces Annie: Exterior is where she'll spend the most time, and opening everything at once creates an overwhelming wall of options. The running total in the sticky header is continuously visible to prevent checkout sticker shock — Annie sees her $1,200 board-and-batten upgrade added immediately. The "Included" badge on defaults communicates that the base model is already high-quality, not a stripped compromise requiring upgrades to be livable.

---

## Screen 5: `buyer_project_agreement.html`

**File:** `orchestration-v2/buyer/buyer_project_agreement.html`

**UI Features:**
- Parcel owner verification strip (Regrid cross-check result displayed inline — "Regrid confirms Annie K. is the recorded owner")
- Project summary table: manufacturer, property address, Site GC, Fiona, timeline, platform fee
- Phased deposit schedule table: Permit ($5K) → Foundation ($25K) → Factory ($100K) → Delivery (remaining), each with trigger condition
- "How This Works" explainer: 4-bullet managed model overview
- Two required checkboxes (property authorization + agreement to terms); "Continue →" activates only when both checked
- Breadcrumb: Models → Customize → Agreement (current)

**Rationale:** The agreement page's job is to make Annie feel informed and protected, not pressured. The Regrid property verification strip surfaces a data cross-check Yardstake runs invisibly — telling Annie that the platform did its homework before asking for money. The phased deposit schedule is the anxiety killer: showing the full payment structure upfront with exact trigger conditions tells Annie that no money moves without something happening first. The two-checkbox gate forces Annie to read and acknowledge both authorization and terms, reducing buyer's remorse and dispute risk.

---

## Screen 6: `buyer_deposit.html`

**File:** `orchestration-v2/buyer/buyer_deposit.html`

**UI Features:**
- Two-state machine: `idle` (deposit form) and `confirmed` (success)
- Idle: order summary (report credit deducted, phase 1 deposit, due-today total), trust copy ("Funds held in Yardstake escrow — released only when permitting begins"), "Authorize Deposit →" CTA
- Processing: 1.5s spinner with "Securing your funds…" copy
- Confirmed: CSS confetti burst (40 pieces, varied colors/rotation) via `spawnConfetti()`
- Fiona introduction card: avatar + "I'm Fiona, your project coordinator" + phone/SMS note
- Next-steps timeline: 3 bullets (Fiona contacts within 24h, permit filed within 1 week, GC scheduled after permit)
- "Go to Project Hub →" primary CTA

**Rationale:** The deposit screen is the moment Annie stops researching and becomes a customer. The trust copy appears directly adjacent to the payment amount — answering the anxiety at its peak rather than burying it in terms. The 1.5s spinner is intentional: an instant transition feels fake; a brief pause signals something real is happening. The confetti + Fiona introduction is the emotional payoff — confetti says "congratulations, you did it," and Fiona immediately answers "what happens next?" The report credit deduction ($49 shown as already paid) makes Annie feel her earlier purchase was meaningful, reinforcing commitment rather than treating it as a separate transaction.

---

## Screen 7: `buyer_project_hub.html`

**File:** `orchestration-v2/buyer/buyer_project_hub.html`

**UI Features:**
- 5-state machine: `permit` → `foundation` → `factory` → `transit` → `utility`
- State switcher panel (dashed-border demo tool) with named buttons per phase
- All states share: authenticated nav, secondary tab bar (My Project active), permit number subheading
- **State 1 — Permit:** BDS filing status card, what-happens-next timeline, Fiona quote card
- **State 2 — Foundation:** $25K deposit request action card (with trigger explained), Pacific Foundation Works update photo, funds summary tiles
- **State 3 — Factory:** Dual-track "Move That Bus" progress bars (Factory Build % + Site Preparation % in parallel), milestone photo approval widget, three-bucket ledger
- **State 4 — Transit:** In-transit banner with GPS progress bar (truck marker ~72%), crane day countdown, Fiona note
- **State 5 — Utility:** Utility hookup status card, inspection scheduling, all-green summary, link to project complete
- Each state renders a different milestone stepper (1–5 of 5 nodes lit)

**Rationale:** The project hub is where Annie lives for 6–12 months — it's the screen she opens first thing in the morning when she's anxious. The 5-state architecture ensures she always sees exactly what's happening today, what triggered the current state, and what happens next. The "Move That Bus" dual-track progress in State 3 is the central tension-relief mechanism: Annie was told factory build and site prep happen in parallel, and seeing both tracks advance simultaneously proves that Yardstake is actually managing the coordination. The milestone photo approval gives Annie a moment of genuine agency — clicking "Approve & Release" on photographic evidence makes fund release feel earned rather than automatic.

---

## Screen 8: `buyer_milestone_detail.html`

**File:** `orchestration-v2/buyer/buyer_milestone_detail.html`

**UI Features:**
- GPS/timestamp overlay on each factory photo (coordinates + exact time)
- Full-screen photo lightbox with keyboard navigation (arrow keys, Escape) and prev/next buttons
- "What Was Verified" checklist with emerald check icons
- "What Happens Next" card with timeline estimate
- Funds Released strip showing amount, recipient, and confirmed send date
- Secondary tab bar ("My Project" active — this is a drill-down from the hub)

**Rationale:** The milestone detail screen is the trust engine of the entire buyer journey. Annie is spending $172K on a unit she cannot visit in the factory — the GPS-tagged photos are her proof of work. By surfacing the exact coordinates and timestamp, Yardstake signals that verification is rigorous and tamper-resistant, not just a checkbox. The lightbox interaction invites Annie to linger on the photos, transforming what could be a dry compliance step into a moment of genuine excitement ("I can SEE my ADU being built"). The funds-released strip closes the loop on the financial transaction, reinforcing that milestone draws are tied directly to verified progress — not just invoices.

---

## Screen 9: `buyer_messages.html`

**File:** `orchestration-v2/buyer/buyer_messages.html`

**UI Features:**
- Single-thread design: no inbox sidebar — Annie has exactly one contact (Fiona)
- System event pills (centered, non-interactive, `border border-slate-200 bg-slate-50 text-slate-500 text-xs rounded-full`) injected between messages as timeline anchors
- Fiona's attachment card links directly to `buyer_milestone_detail.html` (photo thumbnail + title + verified badge)
- Quick-reply chips ("When is crane day?", "Can I visit the factory?", "Who's my Site GC?") populate textarea on click
- Auto-resizing textarea (min 1 row, max ~5 rows)
- Photo attach: file input → inline thumbnail previews → previews embed in sent message bubble
- Send on button click or Enter (Shift+Enter for newline); button activates only when text or photo is present
- Full-height layout fills viewport between nav and tab bar — no page scroll, thread scrolls internally

**Rationale:** The single-thread design is a deliberate product decision, not a missing feature. In the managed marketplace model, Annie's complexity is Yardstake's problem — she should never need to decide who to contact. Fiona is the single point of contact, and the UI makes this feel like a premium concierge service rather than a limitation. The system event pills serve as an ambient project timeline: Annie can scroll up and reconstruct the entire journey from within the message thread without navigating away. The quick-reply chips lower the activation energy for common questions — reducing ghosting and improving Annie's sense of being actively engaged with her project.

---

## Screen 10: `buyer_crane_day.html`

**File:** `orchestration-v2/buyer/buyer_crane_day.html`

**UI Features (States 1 and 3 — PR #30; States 2 and 2b added in PR #31):**
- 4-state machine: `countdown` → `live` → `spectator` → `set-complete`
- Demo state-switcher panel (same dashed-border pattern as other buyer mocks)
- Nav swap: authenticated nav + tab bar hidden in spectator state (logo only)

**State 1 — Countdown:**
- Live `setInterval` countdown to April 14, 2026 8:00 AM PST with 4 gradient-text digit units
- Delivery details card (date, location, unit, crane operator, what to expect)
- Fiona note card
- Share button reveals inline card with fake spectator URL + "Copy Link" (clipboard API + toast)

**State 3 — Set Complete:**
- CSS confetti burst (same `spawnConfetti()` pattern as `buyer_deposit.html`) fires on state entry
- Animated emerald pulse ring around checkmark icon
- Hero photo: ADU on foundation (Unsplash)
- Stats row: arrival time, set time, duration, zero incidents
- Fiona wrap-up note
- "Back to My Project" + "Share Your Photo" CTAs

**State 2 — Live:**
- Full-width hero crane photo (Unsplash) with absolute-positioned overlays
- Pulsing red "● LIVE" badge (top-left) using `@keyframes pulse-dot`
- "👁 14 watching" viewer count (top-right, frosted pill)
- GPS progress bar: gradient track with truck marker at ~85% (unit confirmed on site)
- Live chat panel: messages auto-append every 3s via `setInterval`, looping 4 family messages with fade-in animation; cosmetic "Join the conversation" input
- Chat timer starts on Live/Spectator entry, clears when switching away
- "Preview shared link →" button calls `showState('spectator')`

**State 2b — Spectator:**
- Shares hero image, LIVE badge, viewer count, GPS tracker, and chat panel with State 2
- Same chat message stream (both panels receive each new message simultaneously)
- Blue-to-cyan gradient banner: "Annie's ADU — Crane Day! 🏗 · April 14, 2026"
- "Back to My View →" button calls `showState('live')`
- "Powered by Yardstake" footer
- Nav stripping handled by `showState()`: authenticated controls + tab bar hidden; logo only remains

**Rationale:** Crane Day is the emotional peak of the entire buyer journey — the "Move That Bus" moment. The countdown timer makes the event feel imminent and concrete; Annie can share it with family the way you'd share a flight tracker. The confetti + "Your ADU is home!" heading on set-complete mirrors the deposit screen's celebration, creating a bookend: Annie felt this same delight when she put down her first $5K, and she feels it again when the unit lands. The live chat simulation is deliberately looped and cosmetic — it conveys the social energy of a shared live event without requiring real infrastructure. The GPS tracker bar at ~85% positions the unit as "nearly home," building tension before the set-complete reveal. The spectator mode nav stripping is a deliberate trust signal — public viewers see the shared celebration but nothing about Annie's financials, project details, or account. The emotional energy is preserved; the privacy boundary is absolute.

---

## Screen 11: `buyer_project_complete.html`

**File:** `orchestration-v2/buyer/buyer_project_complete.html`

**UI Features:**
- "🏠 Your ADU is ready to occupy." hero heading with CO issuance subtitle
- All-green 7-node progress bar (Permit → Foundation → Framing → MEP → Delivery → Utility → CO), each with completion date; CO node has ring highlight
- Stats strip: 107 days · $172K · 7 milestones · 0 exceptions
- Document Vault: 4 download cards (CO, permit, photo archive, engineering drawings) — each shows "Preparing download…" toast on click
- Milestone financial summary table: 7 rows + total row ($172,000), "Released To" column hidden on mobile
- "Share Your ADU Story" → share modal with pre-filled testimonial text + Copy Text + Twitter/Facebook/NextDoor cosmetic buttons
- "Leave a Review for Cascadia Modular →" → toast confirmation
- Fiona farewell card (left emerald border, italic quote)
- Escape key and overlay click close share modal
- Secondary tab bar ("My Project" active)

**Rationale:** The project-complete screen closes Annie's emotional arc. The all-green progress bar is a mirror of the milestone stepper she watched advance for 107 days — seeing every node green triggers a "I actually did this" feeling that no text copy can replicate. The Document Vault answers the practical anxiety that follows the emotional high: "Where do I keep all this paperwork?" By surfacing CO, permit, photos, and drawings in one place, Yardstake signals that its value extends beyond delivery. The "Share Your ADU Story" CTA is deliberately prominent — Annie's story is a marketing asset, and the pre-filled text removes the activation energy barrier. The Fiona farewell card uses a left border instead of a card header to feel more like a personal note than a UI component, reinforcing the "wedding planner" relationship model at its conclusion.

---

## Screen 12: `buyer_notifications.html`

**File:** `orchestration-v2/buyer/buyer_notifications.html`

**UI Features:**
- Filter tabs (All · Milestones · Payments · Messages) with live unread counts per category
- 5 seeded notifications: 3 unread (foundation verified, Fiona message, upcoming payment) + 2 read (factory complete, photo share)
- Unread indicator: blue left border (`border-left: 3px solid #2563EB`) + blue dot on the right edge of each item
- Click any item to mark it read — left border transitions to transparent, dot disappears, tab badge decrements
- "Mark all read" button fires a toast confirmation and clears all indicators including the nav bell badge
- Bell badge in authenticated nav auto-hides when all notifications are read
- Empty state (bell-off icon + copy) shown when a filter category has no items

**Rationale:** The notifications screen is the ambient trust layer — Annie doesn't need to visit her project hub to know something happened, but when she does open notifications, she should feel the project is actively moving. The filter tabs solve a real pain point: "Was that a payment message or a Fiona message?" The blue left-border unread pattern is borrowed from email clients Annie already knows (Gmail, Apple Mail), reducing the learning curve. The mark-all-read interaction rewards engagement — Annie shouldn't feel chased by an ever-growing badge count. Clearing the nav bell badge when all items are read creates a satisfying "inbox zero" moment that reinforces her sense of being on top of her project.

---

## Screen 13: `buyer_settings.html`

**File:** `orchestration-v2/buyer/buyer_settings.html`

**UI Features:**
- 5-section sidebar nav (Profile, Payment Methods, Notification Preferences, Security, Documents)
- Active section highlighted with `bg-blue-50 text-blue-700` pill; content panel swaps without page reload
- Profile: editable name/email/phone fields; property address read-only with helper text pointing to support
- Payment Methods: two cards (Visa primary + Mastercard backup) with Set Primary / Remove actions; "Add payment method" button
- Notification Preferences: per-event-type rows with independent SMS and CSS toggle switches — groups for Milestones, Payments, Messages, General
- Security: password (last changed), 2FA (enabled via SMS, shown with green badge), active sessions list (current + one other device) with "Sign out all"
- Documents: 4 project documents (Agreement, Escrow Instructions, Feasibility Report, Building Permit) as download cards with file type + date; pointer to project-complete screen for CO
- Save toast fires on all interactive actions across sections

**Rationale:** Settings is intentionally simpler than the vendor equivalent — Annie is a homeowner, not a business managing a fleet of units and sub-contractors. The sidebar nav pattern scales to 5 sections cleanly on desktop without the cognitive overhead of a full-page navigation. The SMS/email toggles are CSS-only (no JavaScript library) to keep load fast and render instantly — notification preferences are a high-frequency interaction as Annie tunes her experience over the 6-month build. The read-only property address field with support copy signals that Yardstake protects data integrity (you can't accidentally move your project to the wrong lot). The Documents section in Settings is a lightweight shortcut — the canonical Document Vault lives on the project-complete screen, but surfacing project docs here means Annie can find them from anywhere without remembering to navigate to "completed" state first.
