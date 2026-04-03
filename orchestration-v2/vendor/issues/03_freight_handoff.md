# [UX] Outbound Logistics & Freight Handoff

**Label:** `ux-mock` `vendor` `orchestration-v2`
<br>**Persona:** Modular Mike
**Priority:** Medium

## Problem

The Kanban board has a "Ready for Freight" column but no UI for the actual handoff event. Once Mike's ADU rolls off the factory floor and is strapped to a third-party carrier coordinated by Yardstake, there is currently:
- No digital Bill of Lading upload UI
- No formal "I confirm this unit has left my facility" acknowledgment
- No chain-of-custody record if the unit arrives damaged

This creates liability ambiguity: if the ADU arrives on-site cracked or scratched, there is no timestamped record of the unit's condition at the moment it left Mike's dock.

## Proposed Solution

Build a `vendor_freight_handoff.html` (or modal within the Kanban) triggered when an order is dragged/moved to "Ready for Freight":

**Handoff Checklist UI:**
- [ ] Upload pre-shipment photo (minimum 2: full unit exterior, undercarriage/chassis)
- [ ] Upload or confirm Bill of Lading reference number
- [ ] Confirm carrier name (pre-filled by Yardstake Concierge but editable)
- [ ] Digital "thumb-sign" acknowledgment: *"I confirm this unit left my facility in the condition shown in the photos above."*
- Timestamp and GPS coords locked at submission

**Post-Submission State:**
- Kanban card moves to "In Transit" with a tracker showing estimated site-delivery ETA
- Buyer's dashboard updates: *"Your ADU is on the move!"*
- Final payout milestone unlocked only after Site GC confirms on-site delivery

## Acceptance Criteria

- [ ] Handoff flow mock built at `orchestration-v2/vendor/vendor_freight_handoff.html`
- [ ] Includes photo upload simulation (reuse pattern from `vendor_sms_magic_link.html`)
- [ ] Post-submit "In Transit" state shown with simulated ETA
- [ ] Buyer dashboard (`buyer_dashboard.html`) shows corresponding status update when handoff is submitted
