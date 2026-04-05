# Rationale: Buyer UX under the Orchestration Model

**Location:** `user_experience/orchestration-v2/buyer/`

This document correlates the UI features seen in the `buyer_dashboard.html` mock to the core business logic of the Yardstake Phase 2 Orchestration Model. Under this newer model, the buyer (Annie) is no longer purchasing lead information—she is experiencing a seamless, frictionless e-commerce project run entirely by Yardstake as a "wedding planner."

### Key UI Features & Rationale

*   **The "Three-Bucket" Ledger**
    *   *UI Feature:* Separate, transparent cost breakdowns for "The Box" (Fixed Cost), "The Dirt" (Variable Allowance), and "The Red Tape" (Variable Allowance).
    *   *Rationale:* A key reason ADU buyers abandon deals is sticker shock and contractor miscommunication. By splitting the fixed factory cost from the variable site-prep costs, Annie knows exactly what is guaranteed. This aligns with the Orchestration model's need to capture a single $150K+ project funding pool using clean, transparent accounting.
    
*   **The "Move That Bus" Project Tracker**
    *   *UI Feature:* Two parallel visual progress bars for "Track A: Factory Build" and "Track B: Site Preparation".
    *   *Rationale:* This solves the primary anxiety of ADU builds: coordinating the factory timeline with the groundwork timeline. Yardstake actually manages this complex coordination behind the scenes, but by visualizing it beautifully, the user feels actively informed and in control without lifting a finger.
    
*   **Milestone Photo Approvals**
    *   *UI Feature:* Actionable widget requiring Annie to review GPS/Timestamped photos of site progress to click "Approve & Release Funds."
    *   *Rationale:* Replaces messy email invoicing and contractor chasing. This creates absolute transparency and gives the buyer a feeling of ultimate agency, all while efficiently maintaining the tight milestone-draw schedule required by lenders and our Stripe platform accounts.

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
