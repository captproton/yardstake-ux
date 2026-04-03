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

## Built: Buyer Configurator Foundation

### 12. Model Option Tree Editor
- **Files:** `vendor_model_options.html`, `vendor_catalog.html` (Edit Options entry point added to Studio XL card)
- **UI:**
  - **Entry point:** "Edit Options" button at the bottom of the Studio XL card in `vendor_catalog.html` links directly to the option tree editor. Click stops propagation so it doesn't trigger the Edit Model drawer.
  - **Stats strip:** 4 live-updating KPI tiles — Categories, Total Options, Active Upgrades, and Max Uplift — give Mike an instant sanity check at page top.
  - **Column legend:** Single-row header labels (Swatch / Option Name / Std / Price Delta / Live) align with each option row for scanability.
  - **Accordion categories:** 6 sections matching the competitive benchmark — Exterior, Kitchen, Bathroom, Flooring, Interior, Appliances. Exterior, Kitchen, and Flooring open by default; the rest collapsed. Each category has a category-level enable/disable toggle.
  - **Option rows:** Each row contains: drag handle (cursor:grab) · thumbnail upload zone (48×48, click triggers file input; simulated upload flashes zone then renders inline preview) · name input · Standard checkbox (disables price delta and turns label emerald when checked) · price delta number field · per-option active toggle (hides from buyer without deleting) · remove button.
  - **Add option:** Appends a blank row to the active category accordion, auto-expands the body, and focuses the name input.
  - **Add category:** Appends a full new accordion card with editable name input and its own Add option button.
  - **Sticky footer price bar:** Base Net Price | Standard Config | Max Upgrade (base + sum of all active, non-standard deltas). Updates live on any toggle or price field change.
  - **Save toast:** "Options saved to Studio XL" confirmation appears 2.5 s after Save button click.
- **Rationale:** `vendor_catalog.html` (issue #1) gave Mike base pricing control but no way to define buyer choices. Without this editor, Yardstake cannot populate a buyer-facing configurator. The option tree is the prerequisite data layer: Mike defines categories, options, standard inclusion, price deltas, and visual swatches — all of which will drive the buyer-side selection UI in a future issue. The sticky footer max-upgrade sanity check ensures Mike doesn't accidentally publish an option grid that prices his unit out of the market.

---

## Planned (GitHub Issues)

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
