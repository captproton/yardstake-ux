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

## Planned (GitHub Issues)

| # | Feature | Issue |
|---|---------|-------|
| 1 | Catalog & Net-Pricing Management | [#1](https://github.com/captproton/yardstake-ux/issues/1) — ✅ Done |
| 2 | Change Order & Supply Chain Exception Flow | [#2](https://github.com/captproton/yardstake-ux/issues/2) — ✅ Done |
| 3 | Outbound Logistics & Freight Handoff | [#3](https://github.com/captproton/yardstake-ux/issues/3) |
| 4 | Financial Ledger & Tax Reporting Dashboard | [#4](https://github.com/captproton/yardstake-ux/issues/4) |

---

## Core Foundation

- **Removal of Lead Inbox / Sales CRM:** Yardstake handles the e-commerce sale entirely. Mike logs in purely to execute the locked-in fulfillment specification.
- **Terminology:** All references to "Escrow" have been replaced with **"Project Funds"** and **"Custodial Holding"** to align with the Stripe Destination Charge architecture and avoid regulatory misinterpretation.
