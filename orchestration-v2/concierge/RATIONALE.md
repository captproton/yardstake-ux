# Rationale: Concierge UX under the Orchestration Model

**Location:** `user_experience/orchestration-v2/concierge/`

This document outlines the UI logic for `concierge_dashboard.html`. The Concierge persona (Fixer Fiona) is the human anchor of the Phase 2 Orchestration Model. She absorbs the logistical chaos and manages exceptions so that the platform can guarantee a smooth, "white-glove" experience for the buyer.

### Key UI Features & Rationale

*   **Triage & Dispute Mediation Queue**
    *   *UI Feature:* Actionable alerts highlighting stalled projects or delayed payment approvals (e.g., Annie delaying a $25k payout to a site GC).
    *   *Rationale:* Without Fiona actively mediating, a Phase 2 custodial holding/milestone model can grind to a halt. The platform requires a human adjudicator who can override, push, or release funds if there is a dispute or delay.
    
*   **Emotional Anchoring Context Window**
    *   *UI Feature:* A persistent panel reminding Fiona of the buyer's motivations (e.g., "Housing for aging parents - use friendly, low-tech messaging").
    *   *Rationale:* Defines the "White-Glove" promise of the service. Fiona isn't just mindlessly releasing funds; she is crafting a choreographed emotional experience. Reminding her *why* the buyer is building ensures all communication is deeply empathetic.
    
*   **Track A vs. Track B Sync Warnings**
    *   *UI Feature:* A live dashboard showing if the manufacturer timeline is tracking properly against the Site GC timeline.
    *   *Rationale:* Allows Fiona to proactively spot bottlenecks (e.g., the factory is on schedule, but the foundation pour is delayed due to rain) and intervene *before* it affects delivery day. She handles the messy logistics so Annie doesn't have to.
