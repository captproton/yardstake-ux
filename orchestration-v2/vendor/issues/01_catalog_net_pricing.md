# [UX] Vendor Catalog & Net-Pricing Management

**Label:** `ux-mock` `vendor` `orchestration-v2`
**Persona:** Modular Mike
**Priority:** High

## Problem

In the Activation Wizard (Step 3), we intentionally kept onboarding light — capturing only the base model and a starting net price to get Mike over the finish line quickly. We told him he could "add more catalog items later." That "later" screen does not exist yet.

Without a Catalog Management UI, Mike has no way to:
- Add new model variants (e.g., Studio L, Studio XL, Family Loft)
- Define trim packages and their respective net price adders (e.g., "Coastal White" +$3,200)
- Adjust base pricing globally when input costs change (e.g., lumber surge requires a $2,000 base increase across all models)

## Proposed Solution

Build a `vendor_catalog.html` mock inside `orchestration-v2/vendor/` that includes:

- **Model List View:** Card-based grid of all listed models with thumbnail, base net price, and an active/inactive toggle.
- **Edit Model Drawer/Modal:** On click, expands a side panel with fields for:
  - Base net price
  - Lead time (weeks)
  - Available trim packages (name + net adder price)
  - Primary photo
- **"Apply Global Price Adjustment" Banner:** A top-of-page CTA allowing Mike (or his assistant) to increase/decrease all base prices by a flat $ amount or % — surfaced prominently when lumber/CPI index changes.
- **"Add Model" CTA** linking back to the Activation Wizard Step 3 flow for new model entry.

## Acceptance Criteria

- [ ] Mock built at `orchestration-v2/vendor/vendor_catalog.html`
- [ ] Includes at least 3 sample models in varied states (active, inactive, pending review)
- [ ] Global price adjustment interaction is simulated with JS
- [ ] Links back from the Vendor Dashboard Kanban nav
