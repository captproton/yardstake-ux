# [UX] Change Order & Supply Chain Exception Flow

**Label:** `ux-mock` `vendor` `orchestration-v2` `concierge`
**Persona:** Modular Mike + Fiona (Concierge)
**Priority:** High

## Problem

The current Kanban board assumes a perfect, linear build. Real factory production does not work this way. Suppliers run out of specified materials mid-build (e.g., specified White Oak flooring is backordered 6 weeks). Mike currently has no structured way to:
- Notify Yardstake of a material substitution needed
- Get approval from the Concierge and ultimately the Buyer before proceeding
- Document the change for liability and payout calculation purposes

Without this flow, Mike either delays the build (hurting his Placement Score) or makes unauthorized substitutions (creating a dispute).

## Proposed Solution

Build a `change_order_modal.html` or integrate a "Raise Exception" interaction into the Kanban card (`vendor_dashboard.html`):

**Trigger:** A "⚠ Raise Exception" button visible on an active Kanban order card.

**Exception Flow (3 steps):**
1. **Mike's Form:** Dropdown for exception type (Material Sub, Timeline Extension, Scope Clarification), a free-text field to describe the issue, and an optional photo attach.
2. **Concierge Review State:** Fiona's dashboard (`concierge_dashboard.html`) receives a flagged ticket. She mediates and routes to Buyer if needed.
3. **Resolution State:** Mike's Kanban card updates with one of: ✅ Approved / ❌ Denied / 🔄 Pending Buyer Reply — with a countdown timer showing remaining SLA window.

## Acceptance Criteria

- [ ] "Raise Exception" button added to active Kanban order card in `vendor_dashboard.html`
- [ ] Modal or inline form captures exception type, description, and optional photo
- [ ] Simulated JS state shows card updating from "Active" → "Exception Pending"
- [ ] Corresponding flag appears in `concierge_dashboard.html` as a new system alert
