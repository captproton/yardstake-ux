---
name: new-pr-auto
description: Start a new PR from a single GitHub issue in the yardstake-ux UX mocks repo. Checks out main, creates a feature branch, builds the HTML mock, commits, and opens a PR on captproton/yardstake-ux.
---

# Start New PR from Issue (yardstake-ux)

You are working on the **yardstake-ux** repository — a collection of HTML/CSS/JS UX mocks for the Yardstake Phase 2 Orchestration Model. There is no Rails stack, no tests, and no build step. The workflow is: branch → build mock → commit → PR.

## 1. Preparation

```bash
git checkout main
git pull origin main
```

## 2. Find Issue to Work On

```bash
gh issue list --repo captproton/yardstake-ux
```

- Ask the user which issue number to work on if not specified.
- Read the full issue: `gh issue view <NUMBER> --repo captproton/yardstake-ux`

## 3. Create Feature Branch

**Naming convention:** `feature/issue_<ISSUE_NUM>_<short-slug>`

- Example: `feature/issue_1_vendor_catalog`
- To check existing PRs: `gh pr list --repo captproton/yardstake-ux --state all | head -10`

```bash
git checkout -b feature/issue_<NUM>_<short-slug>
```

## 4. Understand Requirements

Read the issue thoroughly:
- What HTML mock file(s) need to be created or modified?
- Which persona directory does it belong to? (`orchestration-v2/vendor/`, `orchestration-v2/buyer/`, etc.)
- What acceptance criteria must be satisfied?
- What interaction simulation (JS) is required?

## 5. Build the Mock

### File Conventions
- All new vendor mocks go in: `orchestration-v2/vendor/`
- All new buyer mocks go in: `orchestration-v2/buyer/`
- Concierge mocks go in: `orchestration-v2/concierge/`
- File names are lowercase with underscores: `vendor_catalog.html`

### Tech Stack
- **HTML5** with semantic structure
- **Tailwind CSS** via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- **Lucide Icons** via CDN: `<script src="https://unpkg.com/lucide@latest"></script>` + `lucide.createIcons()`
- **Google Fonts** (Plus Jakarta Sans): `https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap`
- **Vanilla JS** for interaction simulation (no frameworks)

### Design System
- Background: `bg-slate-900` (`#0F172A`)
- Cards: `glass-card` pattern — `background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(51, 65, 85, 0.8);`
- Accent: Blue (`blue-500`/`blue-600`) for primary actions
- Success/Unlock states: Emerald (`emerald-500`)
- Urgency/SLA alerts: Amber (`amber-400`/`amber-500`)
- Typography: `font-family: 'Plus Jakarta Sans', sans-serif`

### Mobile-First Rules
- All layouts default to single-column stacked on mobile
- Use `lg:grid` or `lg:flex` to expand on desktop
- For factory floor features: use `flex-col-reverse` so the primary action (camera/draw) is at the TOP on mobile
- Horizontal Kanban: use `snap-x snap-mandatory` with `min-w-[85vw]` columns for mobile swipe

### Interaction Simulation Guidelines
- **Photo upload flows**: flash effect on click → progress bars fill per photo → icon swaps to checkmark → payout button unlocks (see `vendor_sms_magic_link.html` for reference pattern)
- **Locked→Unlocked states**: start `opacity-50 cursor-not-allowed scale-95` → transition to `opacity-100 cursor-pointer scale-100`
- **Processing states**: swap button text to spinner icon + "Processing..." → then final confirmation state
- Always use `lucide.createIcons()` after dynamically changing `data-lucide` attributes

### Navigation
- Every page must have a "Back to Dashboard" link: `<a href="vendor_dashboard.html">← Back</a>`
- The Kanban nav bar is the persistent header for all vendor pages

## 6. Acceptance Criteria Checklist

Before committing, verify against the issue's acceptance criteria:
- [ ] Mock file exists at the correct path
- [ ] Mobile layout works (single-column, correct stacking order)
- [ ] All JS interactions are simulated
- [ ] Design matches the established glass-card dark system
- [ ] Navigation links work (back to dashboard, related pages)
- [ ] `lucide.createIcons()` called on load and after dynamic icon swaps
- [ ] No placeholder images — generate with `generate_image` tool if needed

## 7. Commit

Use conventional commit format referencing the issue:

```
feat(vendor): add catalog & net-pricing management mock

- Build vendor_catalog.html with model card grid
- Global price adjustment interaction (JS simulated)
- Edit model drawer with trim package pricing
- Active/inactive toggle per model
- Links to/from vendor_dashboard.html Kanban nav

Closes #1
```

```bash
git add .
git commit -m "feat(vendor): ..."
git push -u origin feature/issue_<NUM>_<slug>
```

## 8. Create Pull Request

```bash
gh pr create \
  --repo captproton/yardstake-ux \
  --title "PR: [UX] <Issue Title>" \
  --body "..."
```

### PR Body Template

```markdown
## Summary
Brief description of what mock was built and why.

## Closes
Closes #<ISSUE_NUM>

## Persona
**Modular Mike** — Vendor / Manufacturer

## Files Added / Modified
- `orchestration-v2/vendor/<filename>.html` — main mock
- `orchestration-v2/vendor/RATIONALE.md` — updated with new feature entry

## Key UX Decisions
- Decision 1 and rationale
- Decision 2 and rationale

## Mobile Considerations
- How the layout adapts for factory floor / phone use

## Interactions Simulated
- JS interaction 1
- JS interaction 2

## Checklist
- [x] Mock built at correct path
- [x] Mobile-first layout
- [x] JS interactions simulated
- [x] Design matches dark glass-card system
- [x] Navigation links working
- [x] RATIONALE.md updated
- [x] Closes issue referenced in commit
```

## 9. Monitor PR

```bash
gh pr list --repo captproton/yardstake-ux
gh pr view <PR_NUM> --repo captproton/yardstake-ux
```

Since there is no CI in this repo, PRs can be merged immediately once reviewed.

## Quick Reference

```bash
# Start new PR
git checkout main && git pull
git checkout -b feature/issue_<NUM>_<slug>

# Build mock, then commit
git add orchestration-v2/vendor/<file>.html
git commit -m "feat(vendor): <description> -- Closes #<NUM>"
git push -u origin feature/issue_<NUM>_<slug>

# Open PR
gh pr create --repo captproton/yardstake-ux --title "PR: [UX] ..."

# Check status
gh pr list --repo captproton/yardstake-ux
```

## Success Criteria
- ✅ Mock file exists and is visually consistent with the design system
- ✅ Mobile layout verified (primary action at top on small screens)
- ✅ All acceptance criteria from issue are checked off
- ✅ RATIONALE.md updated
- ✅ PR description is complete
- ✅ Issue linked via `Closes #N` in commit and PR body
