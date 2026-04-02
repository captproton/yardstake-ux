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
