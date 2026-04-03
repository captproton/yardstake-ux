# [UX] Model Option Tree Editor — Vendor-Side Configurator Builder

**Label:** `ux-mock` `vendor` `orchestration-v2`
**Persona:** Modular Mike (Vendor Admin)
**Priority:** High
**Builds on:** Issue #1 (`vendor_catalog.html` — model card grid + base pricing)

## Problem

`vendor_catalog.html` lets Mike manage models and their base net prices, but it has no way for Mike to define **what a buyer can actually configure** for each model. Before a buyer-facing configurator can exist, Mike's team needs a UI to build and maintain the option tree:

- Which option categories exist for this model (e.g., Exterior, Kitchen, Flooring, Appliances)?
- What are the choices within each category?
- What is the price delta (upgrade cost) per choice, if any?
- Which choices are standard (included) vs. optional upgrades?
- Are any combinations mutually exclusive or conditional? (e.g., "Fiberglass enclosure only available with Bath Tub selection")

Without this admin surface, Yardstake cannot populate a buyer configurator — and Mike cannot communicate to buyers what their actual customization options are.

## Competitive Context

[thehomesdirect.com](https://www.thehomesdirect.com) ships a buyer-facing configurator with the following option categories (observed on their "Micro" 1 Bed | 1 Bath | 378 sq ft unit):

| Category | Examples |
|---|---|
| Floor Plan | Orientation (Standard / Flipped) |
| Exterior | Siding type, Exterior color, Roof material, Shingle color |
| Kitchen | Cabinet material/color/pulls, Countertop material/color, Sink, Backsplash, Island |
| Bathroom | Tub type, Wall material, Enclosure, Sink style |
| Flooring | Kitchen/bath flooring material + style, Bedroom/living carpet + color |
| Interior | Ceiling height, Lighting options, Interior finish options |
| Appliances | Package type (Standard/Upgrade), Electric-only toggle |
| Advanced Details | Structural upgrades, Insulation options, Sidewall dimensions |

Their sample unit (Micro): base $84,900 + a $300 carpet upgrade = $85,200 total. **Yardstake needs Mike to be able to define a comparable option grid for each of his models.**

## Proposed Solution

Build a `vendor_model_options.html` editor accessible from a model's card in `vendor_catalog.html` (e.g., an "Edit Options" button on the Studio XL card).

### Structure

The editor should be organized as **accordion sections**, one per option category. Within each section:

1. **Category header** — name, toggle to enable/disable the entire category for this model
2. **Option rows** — each row has:
   - Option name (text input)
   - **Thumbnail image upload zone** — small square (1:1) upload target; simulated upload swaps a placeholder into a preview swatch; this image is the visual shown to the buyer in the future buyer-facing configurator when this option is selected or hovered
   - "Standard" checkbox (included in base price, no upcharge)
   - Price delta field (e.g., `+$300`) — disabled/zeroed if Standard is checked
   - Active/inactive toggle (hide from buyer without deleting)
   - Drag handle for reordering within category
3. **Add option** button at the bottom of each category
4. **Add category** button at the bottom of the full editor

### Minimum categories to mock (matching the competitive benchmark):
- Exterior (Siding, Color, Roof, Shingles)
- Kitchen (Cabinets, Countertops, Sink, Backsplash)
- Bathroom (Tub type, Wall material, Sink)
- Flooring (Kitchen/Bath, Bedroom/Living)
- Interior (Ceiling height, Lighting)
- Appliances (Package, Electric-only flag)

### Price Summary Bar (sticky footer)
- Shows: Base Price | Total Standard Config | Max Upgrade Price | as the options are configured
- This gives Mike a real-time sanity check that his option tree won't price him out of the market

## Acceptance Criteria

- [ ] Mock built at `orchestration-v2/vendor/vendor_model_options.html`
- [ ] Accessible via "Edit Options" button on a model card in `vendor_catalog.html`
- [ ] Accordion category sections, each toggleable
- [ ] At least 3 fully populated categories (Exterior, Kitchen, Flooring) with 3–5 option rows each
- [ ] Inline price delta editing with a simulated JS total update
- [ ] "Add option" interaction simulated (appends a blank row)
- [ ] Each option row has a thumbnail upload zone; simulated upload renders a small image swatch preview inline
- [ ] Sticky footer price summary bar updates as options are toggled Standard ↔ Upgrade
- [ ] Back navigation to `vendor_catalog.html`
