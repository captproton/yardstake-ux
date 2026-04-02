# Zara — Launch Guidance: Now Through Day 100

**Persona:** Zoning Zara — Research Lead
**Period:** March 7, 2026 → October 9, 2026 (Day 100)
**Last updated:** March 7, 2026

---

## Who Zara Is in This Window

Zara is the human engine behind Criteria #1 — the 90%+ Digital Twin accuracy target that
makes the platform's results trustworthy and the Series A pitch credible. Every other
criterion depends on accuracy: a homeowner who can't trust her result won't buy the $49
report (Criteria #2), won't connect with a manufacturer (Criteria #3 and #4), and won't
generate revenue (Criteria #5).

If Zara has not been hired yet, that is the first action. She must be operational before
the parcel data verification work begins in March.

Her work in this window runs in parallel across two tracks:
1. **Research** — reviewing strategy classes against current ordinances and verifying
   parcel data currency before import
2. **Auditing** — systematic spot-check audits using `AccuracyAuditRecord` to build the
   formal evidence trail that answers an investor's "how do you know your data is 90%
   accurate?" with data instead of conviction

---

## Reference Documents

| Document | Purpose |
|---|---|
| `_zoning_zara.html` | Zara's persona journey |
| `ROLE_REFERENCE.md` | Zara's operating guide — research methodology, audit cadence, escalation |
| `dashboard.html` | Zara's admin dashboard prototype |
| `jurisdiction_intake.html` | Jurisdiction intake tool prototype |
| `ordinance_editor.html` | Ordinance editor tool prototype |
| `parcel_review.html` | Parcel review tool prototype |
| `marketplace_platform/docs/pre_launch_gaps/GAP-002-zoning-researcher-admin-tooling.md` | Full spec for AccuracyAuditRecord and Admin::ZoningResearch |
| `marketplace_platform/docs/analyses/ANALYSIS-004-data-quality-baseline.md` | City-by-city accuracy baseline — what's confirmed, what's unknown |
| `marketplace_platform/docs/analyses/ANALYSIS-003-launch-readiness-scorecard.md` | Current state vs. 5 criteria — Criteria #1 section |
| `marketplace_platform/CLAUDE_SUPPORT_ZONING_RESEARCHER.md` | Claude usage guide for ordinance research |

---

## Now → June 30: Pre-Launch

### Critical Context: GAP-002 Is Not Built Yet

`AccuracyAuditRecord` and `Admin::ZoningResearch` do not exist in the codebase. Sam
builds them in April (the largest pre-launch engineering item). Until then, Zara's audit
work happens in a spreadsheet — columns for parcel address, jurisdiction, zone, confidence
tier returned by the platform, expected result from manual review, and notes.

Sam delivers GAP-002 by approximately April 20. Zara transfers any pre-built spreadsheet
audit records into `AccuracyAuditRecord` at that point.

The strategy class reviews below are independent of the tooling — they require ordinance
research, not platform access.

### March: Strategy Class Reviews

These three reviews are Zara's highest-value pre-launch work. The Eugene, Hillsboro, and
Salem strategy classes have never been validated against real parcels. From
`ANALYSIS-004-data-quality-baseline.md`:

| City | Status | Key risks |
|---|---|---|
| Portland | High confidence — accuracy-corrected Sprint 1.5b | Historic overlay zones (H, HC) not encoded |
| Bend | Medium-High — corrected, not field-validated | Rural residential (RL) setbacks may be incomplete |
| Eugene | Unknown — strategy never tested against real parcels | R-1 local overlay restrictions; LTD EmX parking waivers missing |
| Hillsboro | Unknown — strategy never tested | Washington County UDC differs from Multnomah County; MAX Blue Line waivers missing |
| Salem | Unknown — strategy never tested | Marion County boundary issue; Salem Revised Code local amendments |

**Eugene review:** `EugeneOregonStrategy` against current Eugene Municipal Code. Focus on:
R-1 zone overlay restrictions by neighborhood, ADU size limits under HB 2001 with local
amendments, and parking waiver eligibility along LTD EmX BRT corridors.

**Hillsboro review:** `HillsboroOregonStrategy` against Washington County UDC.
Washington County has its own Urban Development Code with specific ADU provisions that
may differ from state minimums and from Multnomah County (Portland) rules. The MAX Blue
Line terminates in Hillsboro — significant transit-adjacent residential density that should
qualify for parking waivers.

**Salem review:** `SalemOregonStrategy` against Salem Revised Code.
Confirm HB 2001 and SB 1045 local amendments are encoded. Identify the Marion County /
City of Salem boundary — parcels in the county fringe may be incorrectly processed.
Note any active historic districts (Mission Mill area, etc.) with overlay restrictions.

**Default height flag:** Per `ANALYSIS-004`: Eugene, Hillsboro, Bend, and Salem use
`DEFAULT_MAX_HEIGHT_FT = 15.0`. Oregon HB 2001 allows up to 20ft in many configurations.
The 15ft default may produce incorrect "does not fit" results. Verify each city's actual
maximum height against current ordinances and flag any corrections to Sam.

### March–April: Parcel Data Verification

Before Sam runs the imports for Eugene, Hillsboro, and Salem, Zara verifies:

| City | Source | Check |
|---|---|---|
| Eugene (EUG) | ODF MapServer | Confirm dataset vintage and coverage boundary |
| Hillsboro (HIL) | RLIS Washington County filter | Confirm this is Washington County data, not Multnomah County |
| Salem (SAL) | City of Salem dataset | Confirm city boundary vs. Marion County boundary — parcels outside city limits should not be imported |

A stale or wrong-boundary dataset produces confident-looking results that are silently wrong.
Verify before import, not after.

### April–May: First Portland Accuracy Audits

Once GAP-002 is delivered (approximately April 20), begin systematic auditing immediately.
The first 10-parcel Portland spot-check establishes the pre-launch baseline for Criteria #1.

**Audit methodology:**
1. Select a parcel from the platform with a High confidence result
2. Identify the parcel's zone, lot size, and dimensions from the Portland BDS records
3. Manually apply Portland ADU rules (per the Portland Zoning Code, not the platform)
4. Compare the manual result to the platform's result: does the confidence tier match?
   Do the setback numbers match? Does the buildable envelope calculation match?
5. Record in `AccuracyAuditRecord`

Select parcels that test different zones (R1, R2.5, R5, R7, R10) and different scenarios
(transit-adjacent, corner lots, flag lots).

### May–June: Transit Stop Seeding

Work with Sam on transit stop coordinates for Eugene, Hillsboro, and Salem. Verify all
stop coordinates against official GTFS data — do not seed approximate locations.

| City | System | Priority |
|---|---|---|
| Eugene | LTD EmX BRT — major corridor stops | High — BRT stops have highest ridership |
| Hillsboro | MAX Blue Line — western terminus stops | High — transit-rich area |
| Salem | Cherriots — key downtown and corridor stops | Low — minimal ADU parking waiver impact |

3–5 stops per city is sufficient to unblock parking waiver accuracy for launch. A full GTFS
import is the long-term solution but is not required for Oregon Beta.

---

## Phase 1: Days 1–30 (July) — Establishing the Audit Cadence

**Week 1: 5-parcel Portland spot-check**
Select 5 High confidence Portland results across different zones. Manually verify each
against Portland BDS records. Record all 5 in `AccuracyAuditRecord`. Report the accuracy
rate to Victor for the first weekly narrative update.

This is the first formal evidence for Criteria #1. Even a single week of data — if the
accuracy rate is 90%+ — is the beginning of the formal audit trail.

**Week 2: 5-parcel Bend spot-check**
Bend's strategy class was accuracy-corrected in Sprint 1.5b but has never been validated
against real parcels. Select 5 High confidence Bend results across RS, RL, RM, and SR zones.

**Flag immediately.** Any result that appears inaccurate goes to Sam within 24 hours.
In Phase 1 these are cheap to fix. In Phase 3 they become investor risks.

**Monitor confidence tier distribution for EUG, HIL, SAL.**
What percentage of submitted addresses in these cities are returning Low confidence?
A rate above 60% signals a data or strategy issue, not a user issue. Investigate with Sam.

If the platform is returning mostly Low confidence for Eugene because the strategy class
has a known issue, it is better to surface this in Phase 1 and fix it than to report 60%
Low confidence to investors as "expected."

---

## Phase 2: Days 31–60 (August) — Expanding the Audit Coverage

**5-parcel-per-week cadence across all 5 Oregon cities.**
Weight toward High confidence tier results — that's the 90% accuracy target.
Mix cities so no single jurisdiction dominates the audit record.

By end of Phase 2: 50+ parcels audited across all 5 cities.

**Full EUG/HIL/SAL strategy class reviews — with real parcel data.**
Now that real homeowner results are coming in from these cities, Zara reviews each strategy
class against actual ordinances with live examples from the audit. Any inaccuracy discovered
here is corrected by Sam before Phase 3.

**Portland historic overlay investigation.**
Per `ANALYSIS-004`: "Historic overlay zones (H, HC) — strategy does not encode historic
district restrictions." Check whether Portland parcels in historic districts (Irvington,
Ladd's Addition, etc.) are getting High confidence results that should be restricted.
If yes, flag to Sam for a strategy class correction.

**Oregon TAM data pull.**
Work with Sam to produce a qualifying parcel count by city: how many Portland parcels
return High confidence? Medium? This data feeds Victor's Oregon TAM analysis for the
Series A narrative.

---

## Phase 3: Days 61–100 (September–October) — The Formal Audit Summary

**50-parcel formal accuracy audit.**
This is the primary Series A deliverable from Zara. Select parcels systematically across:
- All 5 Oregon cities
- Multiple zones per city
- High confidence tier (primary target) and Medium (secondary)
- Mix of parcel characteristics (corner lots, flag lots, transit-adjacent, historic areas)

Document every audit entry in `AccuracyAuditRecord`. The output is a summary report:

```
YARDSTAKE DIGITAL TWIN ACCURACY AUDIT — OREGON BETA
Audit period: [Date range]
Total parcels audited: [N]
High confidence parcels audited: [N]
High confidence accuracy rate: [X]%

By city:
  Portland:  [N] parcels, [X]% accurate
  Bend:      [N] parcels, [X]% accurate
  Eugene:    [N] parcels, [X]% accurate
  Hillsboro: [N] parcels, [X]% accurate
  Salem:     [N] parcels, [X]% accurate

Method: Manual review of platform results against [source] municipal records.
Auditor: [Zara's name], [date range]
```

This document goes directly into the Series A data room. It is the answer to
"how do you know your data is 90% accurate?"

**Portland middle housing amendment watch.**
Portland's ongoing middle housing amendments may have introduced new zone-specific rules
not yet in the strategy class. One mid-beta ordinance change could invalidate existing
High confidence results for affected zones. Monitor the Portland Bureau of Planning and
Sustainability for any amendments effective during the beta window.

**California jurisdiction research — begins Phase 3.**
Per `LAUNCH_100_DAY_PLAN.md`: California has a 6–12 month data lead time. If the Series A
targets West Coast expansion, California research must start now — not after funding closes.

Start with:
1. Los Angeles ADU ordinance (LA has the most active ADU market in California)
2. San Francisco ADU ordinance (high-value market, complex historic overlay environment)

Research questions for each:
- What zones allow ADUs by right under state law (AB 68, SB 9, AB 2221)?
- What local amendments exist beyond state minimums?
- What are the size, height, and setback rules?
- What transit systems exist that create parking waiver eligibility under AB 2097?
- What parcel data sources are available (county assessor, city GIS portal)?

The California strategy class architecture will follow the same OregonBaseStrategy
pattern — a CaliforniaBaseStrategy with city-specific subclasses. Document the ordinance
research in the same format as `docs/ADU_regs/city_opinions/OR-Portland.md`.
