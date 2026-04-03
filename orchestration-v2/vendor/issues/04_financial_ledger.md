# [UX] Financial Ledger & Tax Reporting Dashboard

**Label:** `ux-mock` `vendor` `orchestration-v2` `stripe`
**Persona:** Modular Mike (and his Accountant/Admin)
**Priority:** Medium

## Problem

Mike gets a satisfying dopamine hit every time a $40k draw unlocks on the SMS Magic Link. But his accountant (or his office admin acting with financial-adjacent permissions) needs an aggregate picture. Currently there is no UI for:
- Viewing total payouts received YTD across all projects
- Seeing funds currently held in the Yardstake Custodial Account (pending milestone unlock)
- Exporting data for 1099-K tax filing (Stripe issues these above $600 thresholds)
- Viewing the Yardstake platform fee deductions (5%) per transaction

Without this screen, Mike's tax preparation becomes manual reconciliation from Stripe emails — a major pain point that could drive churn at the end of the fiscal year.

## Proposed Solution

Build a `vendor_ledger.html` mock inside `orchestration-v2/vendor/` structured as a clean, print-friendly financial report:

**Summary Header:**
- YTD Gross Payouts (total before Yardstake fee)
- YTD Yardstake Fees Deducted (5%)
- YTD Net Received (lands in Stripe Connect account)
- Currently in Custodial Hold (pending milestone unlock, shown as locked amount)

**Transaction Ledger Table:**
- Columns: Date | Order ID | Milestone | Gross | Fee (5%) | Net | Status
- Filterable by date range and project
- "Export CSV" button (simulated)

**Tax Section:**
- Projected 1099-K notice (auto-calculated if YTD > $600)
- Link to Stripe Express Tax Dashboard (external)

**Access Control Note:**
- Full ledger visible to Mike (Admin)
- Office Assistant can see In-Progress project holds but NOT historical net payouts (per delegate_inbox.html permissions)

## Acceptance Criteria

- [ ] Mock built at `orchestration-v2/vendor/vendor_ledger.html`
- [ ] Includes at least 5 sample transaction rows in varied states (paid, pending, held)
- [ ] Export CSV button simulated with a JS download or toast notification
- [ ] 1099-K projection section included
- [ ] Access-level note visible in the UI distinguishing Admin vs. Assistant view
