# How Claude Supports the Zoning Researcher Role

This document covers where Claude AI provides meaningful leverage for the Zoning Researcher (Research Lead) role at Yardstake, organized by the five stages of Zara's workflow. It also notes clearly where Claude cannot help.

This is the first in a planned series. The same analysis will eventually be written for each internal persona (Founder, Growth Marketer, Lead Developer, Accountant, Logistics Lead).

See `zoning_researcher/ROLE_REFERENCE.md` for the full role definition.

---

## Stage 1: PDF Purgatory

**Where Claude is most valuable.** This is the least-tooled, most time-consuming stage. A 200-page ordinance PDF with contradictory values across sections is exactly the kind of document Claude handles well.

**Concrete tasks:**

- **Extract authoritative rule values**: "Here is Section 9.410 of Eugene's ADU ordinance. What is the maximum lot coverage for a detached ADU in an R-1 zone? Does it count the primary dwelling or only the ADU footprint?"
- **Surface conflicts**: "These three sections seem to contradict each other on setbacks. Identify the conflict and tell me which section controls under Oregon statutory interpretation norms."
- **Identify amendment residue**: Old PDFs often contain struck-through text, "effective as of" dates, or references to resolutions that superseded them. Claude can flag these.
- **Cross-reference state law**: Oregon HB 2001 and SB 1051 create statewide ADU minimums. Claude can identify whether a local ordinance provision is likely preempted by state law — a common error in jurisdiction research.
- **Translate planner jargon**: Terms like "ministerial approval," "Type I review," "nonconforming structure," and "accessory structure envelope" have specific meanings. Claude can define them in the context of the jurisdiction's code.

**Limitation**: Claude cannot call the city planner. The irreducibly human part of Stage 1 — getting confirmation from the actual authority when sources conflict — stays with Zara.

---

## Stage 2: Jurisdiction Intake

**Narrower utility.** The GeometryValidator runs automated checks. Zara's judgment calls are:
- Is this self-intersection a data error or a real parcel boundary quirk?
- Does the SRID mismatch mean the whole shapefile is wrong, or just a subset?

Claude can explain what a specific geometry error means and what the repair options are — essentially as a PostGIS/GIS reference. It can also help Zara write field mapping notes that document why certain fields were excluded or renamed during intake, which matters for the audit trail.

---

## Stage 3: The Rulebook (Strategy Pattern Coding)

**High value, specific to Yardstake's architecture.** The translation from ordinance text to Ruby strategy code is a structured, rule-following task Claude handles well. Given the strategy pattern Yardstake uses, Claude can:

- **Draft the strategy class** from a provided ordinance excerpt. Example prompt: "Eugene's ADU ordinance says parking is waived within 0.5 miles of a frequent service transit stop, defined as buses running every 15 minutes or better. Write the `parking_required?()` method stub for `EugeneOregonStrategy`."
- **Write integration tests first** (TDD). Given the rule values, Claude writes the spec before the implementation.
- **Flag edge cases the ordinance doesn't address**: "The ordinance specifies setbacks for detached ADUs. It's silent on JADUs. How should the strategy handle that?" Claude identifies the gap and suggests a defensive approach.
- **Maintain consistency across strategies**: If Portland's strategy uses a particular pattern for `near_major_transit?()`, Claude ensures Eugene's follows the same interface.
- **Document RULES_BASE deviations**: When a jurisdiction's rulebook diverges from baseline (e.g., Bend missing `permit_type()` and `near_major_transit?()`), Claude writes the explanation comment and the issue ticket.

---

## Stage 4: Confidence Calibration

**Pattern recognition at the margin.** Threshold decisions — where exactly to draw the line between High and Medium — require judgment informed by data. Claude can help think through:

- **Distribution analysis**: "I have 200 parcels currently classified Medium. Here are the field characteristics of those that went through successfully vs. those that required variance. What pattern distinguishes them?"
- **Threshold sensitivity**: "If I move the Medium/Low boundary from 50% to 60%, how many current Medium parcels in Eugene drop to Low? Is there a cleaner natural break?"
- **Overlay zone taxonomy**: Different HPZ designations, flood zone classifications (AE vs. X), and riparian buffer rules have different risk profiles. Claude can help build a lookup table of overlay type → confidence tier impact.

Over time, the parcel_review.html resolution decisions accumulate into a dataset. That dataset becomes Claude's input for suggesting pre-classifications before parcels even reach the review queue.

---

## Stage 5: The Feedback Loop (Accuracy Audit)

**Root cause analysis.** When a prediction misses — like project #123 in Eugene — the question is: why, and how do we prevent the same category of miss in other jurisdictions?

Claude can:

- **Draft the post-mortem**: Given the miss details (HPZ buffer rule in a memo never reflected in the official ordinance), Claude writes the structured incident analysis: root cause, data gap, rule change required, similar-risk jurisdictions to audit proactively.
- **Scan other jurisdictions for the same gap**: "Eugene had an HPZ buffer rule in a 2018 city memo that never made it into the PDF. Here are the other four active jurisdiction ordinances. Do any of them have language suggesting a similar informal amendment process?"
- **Write threshold adjustment rationale**: When Zara narrows a threshold based on a miss, Claude drafts the documentation explaining why, so the decision is auditable later.

---

## Cross-Cutting: The Data Queue

When a new jurisdiction request comes in (e.g., "Grants Pass, ordinance last updated 2022"), Claude can front-load the research sprint:

- Summarize what's publicly known about that jurisdiction's ADU regulations before Zara even requests the Shapefile
- Estimate effort based on the jurisdiction's size and the age/completeness of public data
- Draft the intake checklist specific to that jurisdiction's known quirks
- Flag whether Oregon state ADU preemption law would override any restrictive local provisions

---

## The Meta-Level: Claude as Institutional Memory

As Yardstake scales from 5 to 15 to 30 Oregon jurisdictions, the research patterns Zara discovers recur. Certain Oregon county Assessor offices always export in SRID 2152. Certain city planners respond to records requests; others don't. Certain overlay zone types are systematically under-documented in digital form.

Claude can serve as the place where those patterns live — a queryable, updatable research guide that Zara builds over time, so the second jurisdiction in a new county takes 30 hours instead of 60, because the county-level GIS quirks are already documented.

---

## What Claude Cannot Do

To be precise about limits:

| Task | Why Claude can't do it |
|---|---|
| Call planners or request GIS exports | The human-government interface stays human |
| Validate geometry | PostGIS runs the GeometryValidator; Claude can explain results but not compute them |
| Be the source of truth on ordinances | Training data has a cutoff and ordinances change; Zara's primary source is always the official document |
| Replace the accuracy audit | Only closed transactions reveal whether predictions were right; Claude can analyze results but cannot generate ground truth |

---

## The Right Framing

Claude compresses Zara's research and coding time on every task that is **reading, translating, and reasoning about text or code** — which is most of what Stage 1 and Stage 3 require. The irreplaceable parts — authoritative source verification, geometric calculation, and real-world outcome tracking — remain Zara's domain.

The goal is not to automate Zara's role. It is to ensure that the 40–80 hours each jurisdiction currently requires trends toward 25–40 hours as the research playbook matures and Claude handles more of the pattern-matching work within each stage.
