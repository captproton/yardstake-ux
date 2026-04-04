Yardstake Digital Concierge: Technical Blueprint & User Journey

1. Executive Vision: The White-Glove Digital Concierge

The Yardstake mission is to redefine the backyard home-building process by transitioning it from a chaotic construction project into a high-end managed service. Architecturally, the platform is built on Rails 8 and Jumpstart Pro, leveraging the full Hotwire (Turbo and Stimulus) stack to create a seamless, Single-Page App (SPA) experience that avoids traditional page reloads.

The experience is designed to mirror working with a high-end wedding planner rather than a traditional contractor. By utilizing a "Managed Marketplace" model and a sophisticated digital interface, we shield the user from the "chaotic wiring" of construction. This "Extreme Makeover" emotional layer ensures the journey is a choreographed, relentlessly positive experience, transforming a complex build into a white-glove concierge service.

2. Phase 1: The Magic Portal (Onboarding & Feasibility)

This phase facilitates the transition from a casual browser to a serious buyer through immediate gratification and visualization.

* The Address Hook: The entry point is a landing page featuring the Address Autocomplete Input component. This is powered by the Google Maps API and integrated via a Stimulus controller to provide instant, responsive address suggestions without a page refresh.
* Feasibility Visualization: Upon selection, the Interactive Lot Map component pulls public GIS data to highlight property lines and overlays a 3D building envelope on a satellite view. This instantly shows the user exactly where an ADU can legally fit on their specific lot.
* The "Why" Questionnaire: To establish the project's emotional tone, users interact with Gamified Selection Cards.
  * Example Drivers: "Housing for aging parents," "Rental Income," "Home Office," or "Guest Suite."
  * Selecting "Housing for aging parents" triggers a customized UX track that prioritizes accessibility options and specific "Grandparent-friendly" language throughout the journey.
* The Concierge Introduction: Using a Turbo Frame, the interface dynamically loads the dedicated human support team. This view features bios and photos of the real-world Concierge, Site Manager, and Permit Runner assigned to the project.

3. Phase 2: The Financial Engine (Estimates & Funding)

This phase focuses on building trust through financial transparency and integrated fintech tools, presented in a non-reloading, interactive dashboard.

* The "No Surprises" Estimate: A Three-Bucket Table provides a clear breakdown of costs, categorizing them by certainty and predictability.

Category	Description	Status / Certainty	Cost Type
The Box	Prefab unit and manufacturing.	Green Light: Exact Quote	Fixed
The Dirt	Foundation, trenching, and site prep.	Yellow Light: Allowance	Variable
The Red Tape	Permits, city impact, and fees.	Yellow Light: Allowance	Variable

* Educational Tooltips: The Cost Tooltips component provides context to prevent sticker shock. For example, hovering over "Crane Rental" displays: "Required to lift the prefab unit over your main house; price estimated based on typical reach requirements for your street."
* The Funding Hub:
  * Plaid Link Modal: A Stimulus-powered modal allows users to securely log into their bank via Plaid to verify existing HELOC (Home Equity Line of Credit) balances.
  * Embedded Lending Widget: For users requiring new financing, we integrate Acorn/Hearth directly within the dashboard for instant loan approvals.
* Success State: Upon verification (e.g., "HELOC Balance: $185,000 Verified"), a Turbo Stream triggers a Javascript confetti animation, marking the transition from "planning" to "funded."

4. Phase 3: The Prefab Catalog & Customization Studio

The platform shifts into an e-commerce experience, leveraging prefab efficiency to simplify complex design decisions.

* Model Browsing: Users explore the Model Browser, which utilizes a 3D Unit Viewer and high-resolution Photo Gallery to showcase pre-approved models that fit the user's specific lot envelope.
* The Customization Studio: The Dynamic Pricing Calculator component allows for real-time personalization. As the user selects upgrades—such as "Coastal White" siding or "Accessible Bathrooms" for aging parents—the total price updates instantly via Turbo Streams.
* Phase 1 Checkout: To initiate engineering and "lock in" the project, the platform uses the Rails Pay gem to process the initial deposit (typically 5k–10k) and facilitate digital contract signing.

5. Phase 4: The Project Hub (Homeowner Command Center)

Once active, the Master Dashboard becomes the central source of truth, utilizing Turbo Frames to stay updated without manual refreshes.

* "Move That Bus" Timeline: A dual-track progress bar visualizes parallel workstreams: Factory Progress (Track A) and Site GC Progress (Track B).
* Team Interaction: A "Meet Your Dream Team" Carousel allows the user to cycle through profiles of their Site Manager, Factory Rep, and Permit Runner within a dedicated Turbo Frame.
* Permitting Transparency: The Permit SLA Countdown Clock acts as a "Domino's Tracker for Bureaucracy." This is driven by a backend state machine logic; when city reviewers request clarifications, the state changes, triggering a proactive push notification: "The city reviewer asked for a fire sprinkler clarification; our engineers are responding today—no action required from you."

6. Phase 5: Milestone Payments & Proof of Work

Financial draws are tied to physical progress, using secure multi-party routing to ensure accountability.

* The Approval Flow:
  1. The Site GC completes a milestone (e.g., Foundation).
  2. The GC uploads photos to the Proof of Work Gallery.
  3. The homeowner receives a notification to review the cured concrete photos.
* Component Requirements:
  * Approve & Pay Button: A secure trigger integrated with Stripe Connect Destination Charges.
  * Logic: When the homeowner clicks "Approve," the system draws funds from the verified HELOC and routes them directly to the contractor’s account.
* Action/Reaction: Successful payment triggers a UI-wide celebration (confetti) and updates the "Move That Bus" timeline instantly.

7. Phase 6: The Vendor Portals (Managed Marketplace Logic)

Vendors interact with a specialized version of the platform designed for high-volume document and invoice management.

* Role-Based Access: Vendors access a Vendor Dashboard scoped strictly by the ProjectVendor role, ensuring data privacy across the marketplace.
* The Document Upload Center: A structured portal for critical project documentation.

Vendor Type	Required Documents
Manufacturer	State Insignia, Structural Plans, Production Schedule
Site GC	Site Plan, Topography Reports, Local Permits

* Invoicing: Vendors utilize the Draw Request Builder. To trigger the homeowner's approval flow, the vendor must submit a specific invoice (e.g., $25,000 for foundation) and attach mandatory proof-of-work photos.

8. Phase 7: The "Live Drop" & Digital Handover

The project culminates in a high-impact delivery and a transition to long-term digital management.

* Delivery Day Command Center: A week before delivery, the user receives a physical Wi-Fi camera to set up in their backyard. On "Crane Day," the dashboard enters "Live Drop" mode, featuring an ActionCable Live Video Player and a Shareable Public Link for friends and family to watch the unit being lifted into place.
* Post-Completion Experience: The Digital Welcome Mat provides the user with long-term resources:
  * The Document Vault: A secure repository for the Certificate of Occupancy, warranties, and appliance manuals.
  * The Final Bank Draw: The platform automates the "Final Bank Draw" by handling the complex paperwork submission to the lender required for the final manufacturer payment.
  * The "Welcome Home" Video Player: A personalized video message from the Yardstake founders.
* The Real-World Touch: To bridge the digital-physical gap, a high-end welcome basket is delivered to the door, containing champagne and the specific "Grandma" and "Grandpa" mugs—a final nod to the project's original emotional driver.
