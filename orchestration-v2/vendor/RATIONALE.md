# Rationale: Vendor UX under the Orchestration Model

**Location:** `user_experience/orchestration-v2/vendor/`

This document explains the UI logic behind the Vendor (Modular Mike) experience in the Phase 2 Orchestration Model. Mike transitions from a lead-gen CRM user to a **Pure Fulfillment Partner** — he executes projects routed by Yardstake without any involvement in sales, pricing negotiation, or payment collection.

Because he no longer actively hunts for sales, the UI must provide new psychological levers to ensure **Full Activation** and sustained high-frequency engagement.

---

## Built: Engagement Levers (The "Carrots")

### 1. Platform Placement Score
- **File:** `vendor_dashboard.html` (Kanban nav bar)
- **UI:** A "Super Vendor (98/100)" badge and `Rank #1 in Portland` label, anchored to a `< 4hr avg response time` SLA.
- **Rationale:** Rewards fast vendors rather than penalizing slow ones. High scores grant premium catalog visibility to future buyers, motivating Mike to answer Concierge questions rapidly and preventing production bottlenecks.

### 2. Gamified Milestone Draw Unlock
- **File:** `vendor_sms_magic_link.html` (fully simulated with JS)
- **UI:** The $40,000 payout button is grayed-out and locked until Mike taps through 3 GPS-tagged photos. On the 3rd photo, the UI transitions to a glowing green "Transfer $40,000 to Bank" CTA. A "Processing..." spinner precedes the final "Sent via Stripe Connect" confirmation state.
- **Rationale:** Tying the app directly to liquidity trains Mike that Yardstake is his cash register. The multi-step photo sequence creates accountability without paperwork.

### 3. Preferred GC Network Bounty
- **File:** `vendor_dashboard.html` (Kanban sidebar/KPI strip)
- **UI:** A progress bar at "75% Activated" with a prominent `+$500 Bonus` label and "Invite Preferred GC" CTA.
- **Rationale:** Recruiting a vendor's local Site GC is critical for network scaling. Paying Mike a small bounty is significantly cheaper than standalone GC customer acquisition cost (CAC).

### 4. Demand Signals Widget (FOMO)
- **File:** `vendor_dashboard.html` (Kanban KPI strip)
- **UI:** A pulsating widget displaying live buyer traffic (e.g., "42 Buyers are actively visualizing your Studio XL right now").
- **Rationale:** Prevents vendor churn during quiet production periods. Proves the Magic Map is converting and incentivizes Mike to keep his 3D catalog perfectly maintained.

---

## Built: Factory Floor UX

### 5. Mobile-First Factory Kanban Board
- **File:** `vendor_dashboard.html`
- **UI:** A horizontally scrollable, snap-card Kanban board mapping 4 physical factory stations: `Queue / Pre-Prod → Framing Station → MEP Station → Ready for Freight`. On mobile, each column snaps to full-width. The active "Framing" card glows with a ring and surfaces the camera upload CTA directly on the card.
- **Rationale:** Maps the digital interface directly to Mike's physical factory workflow. Moving a card mirrors moving the physical unit in the shop.

### 6. SMS Zero-Dashboard Magic Link Flow
- **File:** `vendor_sms_magic_link.html`
- **UI:** A full-screen mobile mock (phone frame) showing what Mike sees when he taps a Yardstake SMS alert. No login required. Surfaced directly to the camera upload sequence for the active milestone.
- **Rationale:** The best interface for a factory floor worker is no interface. A single SMS tap bypasses the dashboard entirely and routes Mike straight to the one action that unlocks his payout.

---

## Built: Delegation & Team Access

### 7. Delegate Inbox (Assistant Invitation Flow)
- **File:** `delegate_inbox.html`
- **UI:** A form allowing Mike to invite his Office Manager (name, role, email, mobile number for SMS SLA alerts). Granular permission checkboxes distinguish between: Concierge comms (allowed), milestone photo upload (allowed), and Stripe payouts (Admin-only, locked). An **Owner Notifications** toggle (checked by default) lets Mike receive read-only CC'd copies of all urgent alerts without being on the hook to reply.
- **Rationale:** Enforcing a `< 4hr` SLA without a delegation path guarantees churn for factory owners. This flow allows Mike to protect his Placement Score while staying out on the floor.

---

## Built: Activation

### 8. Vendor Activation Wizard (4-Step Onboarding)
- **File:** `activation_wizard.html`
- **Steps:**
  1. **Orchestration Agreement** — Accept platform terms (5% fee, photo-verified draws).
  2. **Stripe Connect** — Mandatory KYC and bank routing setup.
  3. **Catalog Initialization** — Net-pricing entry for primary models, with a reminder that additional models can be added post-setup.
  4. **Preferred GC Handoff** — Referral entry for local site-prep partner.
- **Rationale:** Ensures every vendor is legally and financially compliant before receiving a single routed order.

---

---

## Built: Change Order & Exception Flow

### 9. Change Order / Supply Chain Exception Flow
- **Files:** `vendor_change_order.html`, `vendor_dashboard.html` (Raise Exception trigger), `concierge_dashboard.html` (exception alert)
- **UI:**
  - A "⚠ Raise Exception" link button appears on the active ORD-9021 Kanban card in the Framing Station column (`vendor_dashboard.html`), below the milestone upload CTA.
  - Tapping it opens `vendor_change_order.html` — a 3-state full-page flow:
    1. **Exception Form:** Exception type selector (Material Sub / Timeline Extension / Scope Clarification), description textarea, optional photo attach. Contextual hint text adapts per type.
    2. **Pending State:** Animated SLA countdown bar (4hr Concierge SLA), status badge, and 3 demo resolution buttons to simulate Concierge decisions.
    3. **Resolution State:** Visual confirmation card for Approved / Denied / Routed to Buyer outcomes with full decision rationale.
  - `concierge_dashboard.html` now shows a new amber-bordered triage card for the material substitution exception, with 3 Concierge action buttons (Approve / Route to Buyer / Deny).
- **Rationale:** Unauthorized material substitutions are a primary dispute surface. Formalizing the exception pathway protects Mike's Placement Score during production delays (SLA clock paused during review), gives Fiona structured options, and keeps the buyer informed — all without a single phone call.

---

## Built: Outbound Logistics

### 10. Freight Handoff & Chain-of-Custody Flow
- **Files:** `vendor_freight_handoff.html`, `vendor_dashboard.html` (Begin Handoff trigger), `orchestration-v2/buyer/buyer_dashboard.html` (In Transit banner)
- **UI:**
  - A blue "Begin Handoff" CTA button replaces the static info note on the ORD-7702 "Ready for Freight" Kanban card (`vendor_dashboard.html`).
  - Tapping it opens `vendor_freight_handoff.html` — a 2-state full-page flow:
    1. **Handoff Checklist:** Two required pre-shipment photo captures (full unit exterior + undercarriage/chassis) using the GPS-flash pattern from `vendor_sms_magic_link.html`. Bill of Lading reference field (pre-filled). Carrier name field (pre-filled by Concierge, editable). Digital acknowledgment checkbox with GPS + timestamp lock on confirm. Submit button activates only when both photos captured and acknowledgment checked.
    2. **In Transit State:** Chain-of-custody summary (BOL, carrier, photos, timestamp). ETA progress tracker bar with last-known GPS ping. Final $35,000 payout locked pending Site GC on-site delivery confirmation.
  - `buyer_dashboard.html` shows a persistent "Your ADU is on the move!" banner with live transit progress bar and ETA, inserted between the Move That Bus tracker and the Milestone Approval section.
- **Rationale:** The "Ready for Freight" column previously had no exit action — it was a dead end. The handoff flow creates a timestamped chain-of-custody record at the moment the unit leaves Mike's dock, resolving the liability ambiguity if the ADU arrives damaged. Buyers get immediate notification and a live progress bar that reduces inbound "where is my ADU?" Concierge support tickets.

---

## Built: Financial Ledger & Tax Reporting

### 11. Financial Ledger & Tax Dashboard
- **File:** `vendor_ledger.html`
- **UI:**
  - **KPI strip:** 4 summary cards — YTD Gross, YTD Fees (5%), YTD Net Received (Admin only), and In Custodial Hold (with lock icon). Net is hidden in Assistant view.
  - **Filter bar:** Dropdowns for project, date range, and status. "Export CSV" button (Admin only) with spinner → toast notification.
  - **Transaction ledger table:** 10 rows across 3 orders (ORD-9021, ORD-7702, ORD-6610) in states: Paid, Pending, Held. Columns: Date | Order | Milestone | Gross | Fee | Net | Status. Net column hidden in Assistant view.
  - **Tax section (Admin only):** 1099-K notice with auto-calculated threshold comparison, link to Stripe Express Tax Dashboard, and a projected Q2 estimated tax nudge.
  - **Access control note:** Visible to all roles — documents exactly what Admin vs. Office Assistant can and cannot see, with a link back to `delegate_inbox.html`.
  - **Role toggle (demo):** Admin / Assistant switcher in the nav bar dynamically hides net payouts, tax section, and export button when switched to Assistant view.
- **Rationale:** Without this screen, Mike's annual tax prep is manual reconciliation from Stripe emails — a major churn risk at fiscal year-end. The dual-view access model directly mirrors the permissions set in `delegate_inbox.html`, making it safe to share dashboard access with an office admin without exposing sensitive payout history.

---

---

## Built: Vendor Acquisition

### 13. Builder Application & Vetting Flow
- **File:** `vendor_apply.html`
- **UI:**
  - A 3-state flow: Value Pitch + Application Form → Under Review → Outcome (Approved / Waitlist / Declined).
  - **State 1 — Value pitch & form:** Hero section with "Stop chasing leads. Start building." headline targeting factory owners tired of sales overhead. Stats strip (847 qualifying parcels, 5% flat fee, <4hr payout speed, 0 sales calls). 3-step "How It Works" explainer (Apply → Activate → Build). Full application form with 4 sections: Company Information (name, contact, email, phone), Production Details (factory location, construction type selector, monthly capacity, unit types), Service Coverage (delivery radius, metro area checkboxes for Portland/Eugene/Bend/Salem/Corvallis/Medford), and Optional Partnerships (preferred GC, portfolio link, freeform notes).
  - **State 2 — Under Review:** Submission confirmation with animated status badge ("Under Review"), submitted summary card, and 3-step "What Happens Next" timeline (Team Review → Intro Call → Activation Wizard). Demo buttons simulate the 3 possible vetting outcomes.
  - **State 3 — Outcome:** Configurable resolution card for Approved (green, links to `activation_wizard.html`), Waitlisted (amber, explains market expansion timeline), or Declined (red, explains common rejection reasons and 90-day reapply window). Each outcome has appropriate icon, color scheme, rationale message, and CTA.
  - **Nav integration:** Top nav links to public site and includes "Already approved? Sign in" shortcut to `activation_wizard.html`.
- **Rationale:** The public `index.html` persona card previously linked directly to `vendor_dashboard.html`, skipping vendor acquisition entirely. This flow creates the prerequisite gate before activation. It also serves as a demand-qualification tool — Yardstake can gauge builder interest per metro area before committing to market expansion. The waitlist outcome is strategically important: it captures supply-side interest in markets not yet open (Eugene, Bend) without rejecting willing partners.

---

## Built: Buyer Configurator Foundation

### 12. Model Option Tree Editor — Redesign (Selection Types + Sectioned Categories)
- **Files:** `vendor_model_options.html` (complete rewrite), `vendor_catalog.html` (Edit Options entry point)
- **Context for the redesign:** Two problems emerged from the original flat accordion: (1) buyers need to see images of options before choosing, and (2) categories can have multiple mutually exclusive choices (oval vs. square sink, stainless vs. white appliances). The original checkbox-per-row model didn't distinguish between "pick exactly one" and "add independently" selection modes, and had no first-class color picker type. The rewrite addresses both.
- **UI:**
  - **Entry point:** "Edit Options" button on the Studio XL card in `vendor_catalog.html` links directly to the editor. Click stops propagation to avoid triggering the Edit Model drawer.
  - **Stats strip:** 4 live-updating KPI tiles — Categories (13) · Total Options (47) · Active Upgrades (34) · Max Uplift ($25,100). Updates on any toggle or price change.
  - **Section dividers:** Categories are grouped under 5 logical sections — EXTERIOR · KITCHEN · BATHROOM · FLOORING & INTERIOR · ADD-ONS — with a flush divider line and section label. Groups mirror the rooms/zones a buyer thinks about when configuring their unit.
  - **Selection type badge (per category):** Every category header carries a clickable pill badge that cycles through three types:
    - **⊙ Pick one** (purple) — radio-button exclusivity. Selecting any option as default deselects all others in the category. Price delta for the default option is locked at $0; all alternates are editable. Used for Siding, Roofing, Shingle Style, Appliances, Countertops, Cabinets, Sink Style, Shower Tile, Flooring.
    - **☑ Add-on** (emerald) — independent checkboxes. Options stack. No mutual exclusivity. Used for Outdoor Upgrades (deck, patio cover, irrigation) and Utility & Tech (EV charger, solar-ready, smart thermostat).
    - **⬤ Color** (amber) — color swatch rows instead of image zones. A 52×48 swatch rendered from a hex value; clicking it opens the browser's native color picker via an overlaid `<input type="color" opacity:0>`. Used for Exterior Color and Interior Paint.
  - **Pre-populated categories (13 total):**
    - EXTERIOR: Siding (pick-one, open) · Exterior Color (color-pick, open) · Roofing (pick-one, collapsed) · Shingle Style (pick-one, collapsed — with amber conditional note: "Applies when Architectural Shingles is the selected Roofing option")
    - KITCHEN: Appliances (pick-one) · Countertops (pick-one) · Cabinets (pick-one)
    - BATHROOM: Sink Style (pick-one) · Shower Tile (pick-one)
    - FLOORING & INTERIOR: Flooring (pick-one) · Interior Paint (color-pick)
    - ADD-ONS: Outdoor Upgrades (add-on) · Utility & Tech (add-on)
  - **Option rows (type-aware):** Each row has: image thumbnail zone (52×48, simulated upload) · option name input · default selector (radio-sel for pick-one, standard checkbox for add-on, n/a for color-pick) · price delta (disabled and $0 for the default option in pick-one categories; enabled for all others) · per-option active toggle · delete button. Column widths are consistent across all three types — only the control inside each zone changes.
  - **Radio exclusivity JS (`selectDefault()`):** When a row is marked default, the function deselects all other `.radio-sel` in the same `[data-category]` container and simultaneously updates `price-delta disabled` state for every row in the category.
  - **Color swatch JS (`updateSwatch()`):** `onchange` handler updates `.color-swatch` background to the picker's current hex value, giving instant visual feedback.
  - **Type-aware `addOption()`:** Reads the category's type badge class to generate the correct row HTML — radio selector for pick-one, checkbox for add-on, color-swatch zone for color-pick.
  - **`addColorOption()`:** Dedicated helper for color-pick categories; generates a swatch + radio row pre-seeded with the current color value.
  - **Sticky footer price bar:** Base Net Price · Standard Config · Max Upgrade (base + sum of all active non-default deltas). Updates live on any interaction.
  - **Save toast:** "Options saved to Studio XL" confirmation, 2.5s delay.
- **Rationale:** The flat accordion treated every choice as independent, which is wrong for "pick exactly one finish" decisions. A buyer choosing Exterior Siding should see 4 options and select one — the interface must enforce that exactly, or Mike's pricing math breaks (double-counting deltas). The three-type model maps cleanly to how modular builders actually think about their product: exclusive swaps (siding, sink style), additive upgrades (EV charger, deck), and colorways (paint, stain). Section dividers reduce cognitive load for Mike during data entry — he thinks room by room, not feature by feature. The conditional note on Shingle Style surfaces a dependency that would otherwise be invisible in a flat list, preventing a buyer from selecting a shingle color without first understanding it only applies to one roofing choice.

---

## Built: Order Intake

### 14. New Order SMS Alert & Spec Review
- **Files:** `vendor_order_received.html` (SMS magic link), `vendor_order_detail.html` (desktop spec page)
- **UI:**
  - **SMS magic link (`vendor_order_received.html`):** Reuses the phone-frame mock pattern from `vendor_sms_magic_link.html`. 3-state flow:
    1. **Alert state:** Pulsing blue "New Order Routed" badge with glow animation. Order summary card showing model, location, zoning, buyer deposit ($14,500 secured), and a 4-tile milestone draw schedule (Framing $40k · MEP $30k · Finishes $25k · Delivery $35k) with total project value ($144,500 net). Two CTAs: "Review Full Spec" (opens scrollable spec within phone) and "Accept & Add to Queue" (fast-accept shortcut).
    2. **Spec preview state:** Scrollable within-phone detail view with sticky back-nav header. Sections: Project Overview (model, sqft, bed/bath, foundation type), Buyer Option Selections (6 line items showing STD vs. upgrade deltas totaling +$7,500), Delivery & Site (address, distance, target date, Site GC contact, crane coordination), Drawings & Docs (4 downloadable PDFs), and Concierge Note (contextual message from Fiona with buyer priorities). Sticky footer "Accept Order & Add to Queue" CTA.
    3. **Accepted state:** Emerald checkmark confirmation with order summary (station: Queue / Pre-Prod, first draw: $40,000). "Open Kanban" link to `vendor_dashboard.html`. Notification copy: "Buyer and Site GC have been notified."
    4. **Decline reason state:** Structured reason selector (At capacity / Distance too far / Timeline doesn't work / Other). Requires reason selection before confirming. Explicit "No impact to your Placement Score" messaging to prevent decline anxiety.
    5. **Declined confirmation state:** Neutral confirmation (not punitive). Order returned to Concierge for re-routing. Score impact: None.
  - **Desktop spec page (`vendor_order_detail.html`):** Full-width 3-column layout accessible from Kanban Queue cards. Left column (2/3): Project Specifications (6-tile grid), Buyer Option Selections (full table with STD/upgrade delta column and footer total), Drawings & Documents (4 file rows with size and download icons). Right sidebar (1/3): Accept/Decline Action Card (border-highlighted with emerald Accept CTA; expandable "Can't take this order?" toggle reveals decline reason selector and confirm button), Milestone Draw Schedule (4-step numbered list with $144,500 total), Delivery & Site details (address, distance, target date, GC contact with phone number), and Concierge Note with "Reply to Concierge" link to `vendor_messages.html`. 3-state flow: Detail → Accepted confirmation or Declined confirmation.
  - **Nav integration:** Both screens link back to `vendor_dashboard.html`. The desktop version includes the standard nav pattern (back arrow + page title + order number).
- **Rationale:** Orders previously appeared in the Kanban Queue column with minimal context (buyer name, model name, deposit amount). Mike had no way to review the locked-in specification, no buyer option selections, no drawings, no Site GC contact, and no explicit acceptance handshake. The SMS variant ensures Mike can review and accept from the factory floor via a single tap — the same zero-friction pattern that makes milestone draws successful. The desktop variant provides the full-density reference view for pre-production planning. The acceptance step creates a clear commitment point: before accepting, Mike is browsing; after accepting, he's committed to a production timeline. The decline flow is equally important: forcing acceptance without an exit creates resentment. By collecting structured decline reasons (capacity, distance, timeline) and explicitly protecting the Placement Score, Yardstake gets routing intelligence data while Mike feels empowered rather than trapped. The Concierge can use decline patterns to adjust order routing heuristics over time.

---

## Built: Concierge Communication

### 15. Concierge Message Thread
- **File:** `vendor_messages.html`
- **UI:**
  - Full-height two-pane layout (sidebar + thread) that fills the viewport below the nav bar. Mobile-responsive: sidebar and thread swap on small screens with a back button.
  - **Sidebar:** Conversation list per order, each showing order number, model name, last message preview, and timestamp. Unread conversations show a colored badge (red for SLA-active, blue for standard unread). SLA-urgent conversations show a mini progress bar and countdown directly in the list item. Search bar at top.
  - **Thread header:** Concierge avatar, order title, sub-label (order number + "Fiona (Concierge)"). "View Order Spec" link routes to `vendor_order_detail.html`. Unread count badge in nav bar updates live.
  - **SLA banner:** Sticky red banner below thread header when the active conversation has an unanswered Concierge message. Shows countdown timer (ticking live via JS) and a progress bar. Dismisses automatically when Mike sends a reply.
  - **Messages:** Concierge messages left-aligned (fuchsia headphones avatar), Mike's replies right-aligned (blue bubbles). Unread Concierge messages have a red dot indicator and red border. System events (order routed, exception resolved) shown as centered pills. Read receipts ("Read by Fiona" with double-check icon) appear beneath Mike's replies.
  - **4 demo conversations:** ORD-9021 (active, SLA urgent — bolt pattern question), ORD-7702 (unread — freight pickup confirmation), ORD-8814 (read — framing schedule check-in), ORD-6610 (resolved exception — material sub approved).
  - **Reply bar:** Photo attachment button (simulates file attach, shows preview strip with remove option), auto-resizing textarea (Enter to send, Shift+Enter for newline), send button activates only when text or photo present. Sent messages append to thread with "Sent" → "Read by Fiona" read receipt progression. Sending a reply clears the SLA banner and unread indicator for that conversation.
- **Rationale:** The Placement Score rewards `< 4hr avg response time`, the delegate inbox grants "Manage Concierge Communications" permission, and the change order flow routes to Concierge — but no screen previously existed where Mike could read or reply to messages. The SLA mechanic was undeliverable without a reply surface. The live countdown timer creates urgency without being punitive — it disappears the moment Mike replies. Photo attachment enables Mike to answer specification questions directly from the factory floor without switching apps. The per-conversation structure (rather than a single inbox) keeps threads tied to their order context, so Mike never has to remember which project a message belongs to.

---

---

## Built: Inter-Station Kanban Progression

### 16. Inter-Station Progression & Multi-Milestone Draws
- **File:** `vendor_dashboard.html` (updated)
- **UI:**
  - **Draw schedule strip:** Every card now shows a 4-pip progress bar at the top — one pip per milestone (Deposit, Framing, MEP, Freight). Pips are green for completed draws, blue for the active milestone, and dark for upcoming ones. Below the strip, a 4-column label row shows the dollar amount and status for each milestone at a glance.
  - **Queue card ("Begin Production" CTA):** ORD-8814 now has a green "Begin Production" button. Tapping it opens the inline photo upload modal pre-configured for the Framing draw transition.
  - **Framing card ("Complete Station" CTA):** ORD-9021's camera upload zone replaced with a full-width "Complete Station · Unlock $40k" CTA button, consistent with the new pattern.
  - **Photo upload modal (inline):** A dark glassmorphism modal overlays the Kanban. Title and draw label are dynamically set per station. Three GPS-tagged photo slots — tapping each triggers the camera-flash simulation and a slot-level upload progress bar. On all 3 slots filled, the "Submit & Unlock Draw" button activates. A GPS verification strip ("Location verified") anchors the authenticity UI.
  - **Processing state:** Animated spinner + progress bar that fills over ~1.5s simulating photo verification and Stripe payout initiation.
  - **Success state:** Celebration ring animation, draw amount in large emerald type, ETA `<4 hours` note, and an "Advance to [Next Station]" button that actually moves the card.
  - **Card advancement:** On clicking "Advance", the source card is removed from its column (count decremented), a new card is injected into the destination column (count incremented, pop-in animation), and the destination column header activates (color and pulse dot update live). The MEP column transitions from slate/empty to purple/active when a card arrives.
  - **MEP active card:** When ORD-9021 advances to MEP, it renders with a purple ring, a "Complete Station · Unlock $30k" CTA, and the same Raise Exception link.
  - **Freight card:** When a card advances to Ready for Freight, it renders with a blue border, all-green draw strip, and "Begin Handoff · Unlock $35k" linking to `vendor_freight_handoff.html`.
- **Rationale:** The Kanban previously showed 4 columns but had no inter-station triggers — it was a status display, not a workflow tool. Cards could not advance without Mike manually navigating elsewhere. This update closes the full production loop: every station transition requires GPS-verified evidence and immediately initiates the corresponding draw, making the Kanban the literal mechanism through which Mike gets paid. The pop-in animation and column header activation give Mike immediate confirmation that the system processed his work — no ambiguous "did that go through?" moment.

---

---

## Built: Post-Delivery Completion & Project Archive

### 17. Delivery Confirmation & Project Wrap-Up
- **Files:** `vendor_order_complete.html` (new), `vendor_dashboard.html` (5th column added), `vendor_freight_handoff.html` (demo trigger added to In Transit state)
- **UI:**
  - **`vendor_order_complete.html` — SMS magic link (2 states):**
    - **State 1 — Delivery Alert:** Full-screen phone frame. Celebration header with pulsing emerald checkmark ring (pop + payPulse CSS animations). "Project Complete" badge. Site GC confirmation card ("Backyard Bill tapped 'Confirm Delivery'" with GPS coordinates and timestamp). Payout card showing $35,000 in large emerald type with Stripe Connect routing note and `<same business day` ETA. All-4 draw strip (all pips green) with dollar amounts. "View Project Summary →" CTA and "Back to Kanban" text link.
    - **State 2 — Project Summary:** Back nav + "Project Complete" badge. Project financials block: Total Gross Draws $117,000 / Yardstake Fee −$5,850 / Net Paid to You $111,150 (emerald, large). Stats grid: 72 days · 4/4 milestones · 10 photos. Milestone timeline (4 rows with dates and amounts: Jan 22 $12k / Feb 10 $40k / Mar 3 $30k / Apr 4 $35k). Placement Score impact callout (+3 pts, on-time delivery, no exceptions). "View in Ledger" → `vendor_ledger.html` and "Back to Kanban" CTAs.
  - **`vendor_dashboard.html` — 5th column "Delivered · Archive":**
    - Muted emerald column header (not active-pulsing — production has closed).
    - Compact archived card for ORD-6610 (Eugene Backyard, Studio S · Natural Wood, delivered Mar 12 2026, $94,050 net paid). Card is intentionally de-emphasized (opacity-80, no CTAs, no ring). All-green draw strip, order number, model, completion date, net paid, and "Summary →" link to `vendor_order_complete.html`.
    - Text separator: "Completed orders archive here" guides Mike's mental model.
  - **`vendor_freight_handoff.html` — demo trigger:**
    - Below the "Final Draw Pending" note in the In Transit state, a dashed emerald border panel shows "Demo: Simulate Site GC Event" with a link: "GC confirms delivery → Mike gets $35k SMS" routing to `vendor_order_complete.html`. Allows reviewers to traverse the full delivery flow without waiting for the live GC action.
- **Rationale:** The freight handoff previously ended at "In Transit" with a passive note about a pending draw. Mike had no screen showing delivery confirmation, no payout celebration, and no archive for completed projects — the story stopped three chapters before the ending. The completion notification closes the "cash register" loop: Mike sees the final transfer the instant the crane crew sets the unit on the foundation, reinforcing that Yardstake is the fastest-paying middleman he's ever worked with. The Project Summary gives him a shareable record without any manual reconciliation. The 5th Kanban column keeps the active board clean (only in-flight work) while preserving a permanent history — important for multi-order vendors tracking which GCs performed well on which sites.

---

---

## Built: Notification Center

### 18. Notification Center / Activity Feed
- **Files:** `vendor_notifications.html` (new), `vendor_dashboard.html` (bell icon added to nav)
- **UI:**
  - **`vendor_dashboard.html` nav:** Bell icon button added between "Route Inbox" and the avatar. Badge shows unread count (2). Links to `vendor_notifications.html`.
  - **`vendor_notifications.html` — full-page activity feed:**
    - **Sticky nav:** Back-to-Kanban link, "Notifications" title, "Mark all read" action (desktop); mobile version pinned to bottom bar.
    - **Filter tab bar (sticky):** Five tabs — All (11) · Payouts (3) · Messages (2, badged blue for unread) · Orders (3) · Exceptions (2). Active tab has blue bottom border. Tabs filter notification rows with JS; date group headers auto-hide when all their rows are filtered out. Empty state ("No notifications in this category") shown when a filter yields nothing.
    - **Notification rows:** Grouped under date headers (Today · Apr 4 / Yesterday · Apr 3 / Mar 31 / Mar 22). Each row: type icon in colored rounded square (emerald for payouts/delivery, blue for messages/orders, red for SLA, amber for exceptions/score) · bold title + description + timestamp · chevron or unread dot. Unread rows have `unread` class with blue-tinted background. Read rows have `read-fade` opacity on title. Clicking an unread row marks it read (removes dot + bg tint).
    - **11 demo notifications covering every type:**
      - Payouts: $35k final draw (ORD-7702), $30k MEP draw (ORD-9021), $40k Framing draw (ORD-9021) → all link to ledger or completion screen
      - Messages (2 unread): Fiona MEP schedule check (ORD-9021), Fiona freight BOL confirmation (ORD-7702) → link to `vendor_messages.html`
      - Orders: ORD-7702 delivered, ORD-7702 carrier pickup, ORD-8814 new order routed → link to relevant order screens
      - Exceptions: SLA alert ORD-9021 (resolved), exception resolved ORD-6610 → link to `vendor_messages.html` and `vendor_change_order.html`
      - System: Placement Score updated 98/100 (+2 pts)
    - **Mark all read:** Strips unread class + dot from all rows, fades titles, hides the button.
- **Rationale:** Every other screen in the vendor UX is triggered by a specific action (SMS tap, Kanban CTA, order accept). There was no "ambient catch-up" view for Mike to see what happened across all orders while he was on the factory floor. This screen is the daily opener: Mike scans payouts landed, messages waiting, and exceptions resolved — all in one scroll — then deep-links directly into the right screen. The filter tabs are particularly important for multi-order vendors who want to see "all pending payouts" without wading through message threads.

---

---

## Built: Profile, Settings & Account Management

### 19. Vendor Settings
- **File:** `vendor_settings.html` (new)
- **UI:**
  - **Two-column desktop layout:** Left sidebar (200px, sticky) with icon + label nav items (Company Profile · Stripe & Payouts · Service Areas · Notifications · Security · Activation Recap). Active item highlighted blue. Bottom of sidebar shows account name + email. Right side: scrollable content area, max-width 2xl.
  - **Mobile:** Horizontally scrollable tab bar (sticky below nav) replaces the sidebar. Same 6 sections.
  - **Section 1 — Company Profile:** Logo upload zone (80×80, simulates upload with flash → checkmark → initials restore). Company name, tagline (buyer-facing catalog copy), city/state, contact phone (used for SLA SMS), email, website. Save button triggers emerald toast.
  - **Section 2 — Stripe & Payouts:** KYC Verified status card (green badge, verified date). Bank account row (Chase ••••4821) with "Update →" link simulating Stripe Express redirect. Instant Payouts toggle (on by default). 1099-K notice with YTD amount, threshold note, and "View Tax Dashboard →" link.
  - **Section 3 — Service Areas:** Card grid per metro. Portland (Active, green border, toggle on, delivery radius range slider 75 miles). Bend and Eugene (Waitlisted, amber border, toggle disabled with toast explaining market queue). Salem and Medford (Coming soon, dimmed, no toggle). Market expansion nudge: "Refer a builder to move up the waitlist" with link to `delegate_inbox.html`.
  - **Section 4 — Notifications:** Toggle rows per event type (New Order / Payout / Concierge Message / Exception). SMS for Concierge messages locked with "Required for SLA" label. Quiet Hours card (on/off toggle + from/until time selectors). SLA bypass note in amber.
  - **Section 5 — Security:** Password change form (3 fields + Update button). Two-factor authentication card — initially shows "Not enabled" + "Enable 2FA" button. Tapping shows QR code (hand-drawn SVG pattern + manual key string) and 6-digit verification input. Entering any 6 digits triggers success state ("2FA Enabled"). Active sessions list (iPhone current + MacBook) with individual sign-out buttons.
  - **Section 6 — Activation Recap:** Read-only checklist of all 4 activation wizard steps with completion dates (Jan 20–21 2026). Each row links to the relevant management screen: Agreement → PDF, Stripe → section 2, Catalog → `vendor_catalog.html`, GC referral → update toast. Bottom note links to `delegate_inbox.html` for team management.
  - **"M" avatar** in nav links to `vendor_settings.html` (updated in `vendor_dashboard.html` as well).
- **Rationale:** Mike had no way to update his bank account, service area, notification preferences, or review his platform agreement. This creates both operational risk (wrong bank = delayed payouts) and churn risk (can't silence 3 AM notifications = Mike deletes his app). The sidebar layout mirrors what Mike already knows from Stripe, Gusto, and similar SaaS dashboards — no learning curve. The activation recap is specifically valuable for vendors who completed onboarding months ago and want to confirm what they signed up for or update their GC referral after a relationship change.

---

## Built: Multi-Unit Scaling View

### 20. List View & Batch Milestone Upload
- **File:** `vendor_dashboard.html` (updated)
- **UI:**
  - **Stats strip (persistent above board):** Shows station counts for the current floor state: "1 Queue · 1 Framing · 0 MEP · 1 Freight · 1 Delivered" — each segment colored to match its column. Updates dynamically as cards advance. Visible in both Kanban and List views.
  - **View toggle:** Kanban / List button pair in the toolbar right. Active view highlighted with blue tint + border. Icons: `layout-dashboard` for Kanban, `list` for List view.
  - **List view (table):** Full-width density table with columns: checkbox · Order/Model · Station · Days in Station · Next Draw · SLA/Status. Replaces the horizontal Kanban scroll. Each row is clickable and deep-links to the relevant order screen (order detail, freight handoff, completion). Station column shows colored dot + label matching Kanban column colors. ORD-9021 row has red "SLA" badge. ORD-6610 (archived) is dimmed, checkbox disabled, row links to completion screen.
  - **Batch selection:** Checkboxes on each active row. Checking any row triggers a fixed bottom "batch bar" that slides up (cubic-bezier pop-in animation): camera icon · "N orders selected · Batch milestone upload" · "Upload Photos" button (opens existing photo modal) · dismiss ✕. Batch bar hides when selection is cleared. Row clicks that are not on the checkbox navigate to the order screen.
  - **"M" avatar** now links to `vendor_settings.html`.
- **Rationale:** The snap-scroll Kanban is optimal for 3–5 concurrent orders — each card is a rich touchpoint. At 15+ orders (the Oregon Beta growth target), horizontal scrolling becomes unusable. The list view solves density: Mike can see all orders, their stations, days in station (flags stuck cards), next draw amounts, and SLA status in one scroll. The batch upload is the key efficiency gain — instead of opening each order card individually to upload framing photos, Mike selects all 8 orders currently in Framing, uploads once, and unlocks $320k in draws simultaneously.

---

## Shipped (GitHub Issues)

| # | Feature | Issue |
|---|---------|-------|
| 1 | Catalog & Net-Pricing Management | [#1](https://github.com/captproton/yardstake-ux/issues/1) — ✅ Done |
| 2 | Change Order & Supply Chain Exception Flow | [#2](https://github.com/captproton/yardstake-ux/issues/2) — ✅ Done |
| 3 | Outbound Logistics & Freight Handoff | [#3](https://github.com/captproton/yardstake-ux/issues/3) — ✅ Done |
| 4 | Financial Ledger & Tax Reporting Dashboard | [#4](https://github.com/captproton/yardstake-ux/issues/4) — ✅ Done |
| 9 | Model Option Tree Editor (Buyer Configurator Foundation) | [#9](https://github.com/captproton/yardstake-ux/issues/9) — ✅ Done |

---

## Core Foundation

- **Removal of Lead Inbox / Sales CRM:** Yardstake handles the e-commerce sale entirely. Mike logs in purely to execute the locked-in fulfillment specification.
- **Terminology:** All references to "Escrow" have been replaced with **"Project Funds"** and **"Custodial Holding"** to align with the Stripe Destination Charge architecture and avoid regulatory misinterpretation.
