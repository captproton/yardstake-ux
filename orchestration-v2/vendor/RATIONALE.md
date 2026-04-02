# Rationale: Vendor UX under the Orchestration Model

**Location:** `user_experience/orchestration-v2/vendor/`

This document explains the UI logic behind `vendor_dashboard.html`. In the Phase 2 Orchestration Model, the Vendor (Modular Mike) is completely removed from the sales, pitching, and payment collection process. He becomes a pure fulfillment partner who simply executes projects routed by Yardstake.

However, because he no longer actively hunts for sales, the UI must provide new psychological levers to ensure he achieves **"Full Activation"** and remains highly engaged.

### Key Engagement Levers (The "Carrots")

*   **Platform Placement Score (Search Algorithm Gamification)**
    *   *UI Feature:* A "Super Vendor (98/100)" badge in the nav bar and a prominent metric showing his rank based on an average < 4hr response time.
    *   *Rationale:* Instead of penalizing slow vendors, we reward fast ones. High platform scores grant premium catalog visibility to future buyers. This motivates Mike to answer Concierge questions rapidly, preventing production bottlenecks.

*   **Gamified Milestone Draw Unlock (The Financial Choke Point)**
    *   *UI Feature:* The Draw Request Builder displays his $40,000 payout as "grayed out" and "locked" until he uploads his proof-of-work photos. Once uploaded, the UI physically unlocks and turns green, replacing invoice sending with a dopamine-hit transaction.
    *   *Rationale:* Tying the UI directly to liquidity trains Mike that the Yardstake app is his cash register, keeping him engaged.

*   **Preferred GC Network Bounty (Activation Completion)**
    *   *UI Feature:* An activation progress bar prompting Mike to "Invite his Preferred GC" to earn a $500 bonus draw payout.
    *   *Rationale:* According to the plan, recruiting a vendor's local Site GC is crucial for scaling the network efficiently. Paying a small bounty to Mike for this referral is significantly cheaper than standalone contractor customer acquisition cost (CAC).

*   **Demand Signals Widget (FOMO)**
    *   *UI Feature:* A pulsating widget displaying live traffic (e.g., "42 Buyers are actively visualizing your Studio XL right now").
    *   *Rationale:* To prevent vendor churn while a project is quiet, this creates Fear Of Missing Out. It proves the Magical Map is driving traffic and incentivizes him to keep his 3D catalog perfectly up to date.

### Core Foundation Maintained

*   **Removal of Lead Inbox / Sales CRM Features**
    *   *Rationale:* Yardstake handles the e-commerce sale entirely. Mike logs in to execute the locked-in fulfillment specification.
