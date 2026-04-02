# Partner Brief — Usage Guide

**File:** `rachel_partner_brief.html`
**Purpose:** One-page PDF Victor sends to each Rachel partner after the demo call.
**Owner:** Victor (personalizes and sends). Val (tracks referral link attribution).

---

## Step 1 — Personalize the Link

Open `rachel_partner_brief.html` in any text editor and find line:

```
yardstake.com/check?ref=<span class="text-white">[YOUR NAME]</span>
```

Replace `[YOUR NAME]` with Rachel's slug. Use lowercase, no spaces:

| Rachel | Slug | Full link |
|---|---|---|
| Rachel Kim (RE/MAX Portland) | `rachel_kim` | `yardstake.com/check?ref=rachel_kim` |
| Portland Housing Center | `phc` | `yardstake.com/check?ref=phc` |
| Oregon Community CU | `occu` | `yardstake.com/check?ref=occu` |

Save the file with a new name so you keep the master blank:

```
rachel_partner_brief_rachel_kim.html
rachel_partner_brief_occu.html
```

---

## Step 2 — Tell Val the Slug

Email Val the slug before you send the brief. Val adds it to Google Analytics as a
tracked UTM source so Rachel's referrals are attributed correctly in the weekly funnel
report.

Val needs: the slug, Rachel's full name, and her variant (Realtor / Lender / Consultant).

---

## Step 3 — Export to PDF

1. Open the personalized HTML file in Chrome or Safari
2. Click the **Export as PDF** button at the top of the page
3. In the print dialog: **Destination → Save as PDF**, margins → None, background graphics → ON
4. Save as `Yardstake_Partner_Brief_[Rachel Name].pdf`

**Chrome gives the cleanest output.** Safari works. Firefox sometimes clips the footer.

---

## Step 4 — Send to Rachel

Send within 24 hours of the demo call while the Yardstake result is still fresh in her mind.

**Suggested email:**

> Subject: Your Yardstake referral link + one-pager
>
> Hi [Rachel],
>
> Great talking today. Attached is a one-pager you can share with clients or drop in
> your email signature. Your personal link is already on it —
> every check that comes through it gets tracked back to you.
>
> I'll send you a monthly note with your referral counts. Any questions, reply here.
>
> — Victor

---

## Step 5 — Monthly Referral Update

On the first Monday of each month, Victor sends each active Rachel partner a short email:

> Hi [Rachel],
>
> Your Yardstake referrals this month:
> - Free checks run: X
> - Reports purchased: X
> - ADU inquiries initiated: X
>
> [Optional: one interesting result — e.g. "A SE Portland client on your link qualified
> for 900 sq ft — one of the largest buildable envelopes we've seen this month."]
>
> — Victor

Val pulls these numbers from the GA referral report filtered by Rachel's slug.
During Oregon Beta, Victor sends this manually. It takes 5 minutes per partner.

---

## Master File Management

Keep one blank master (`rachel_partner_brief.html`) with `[YOUR NAME]` intact.
Never overwrite the master — always save a new named copy per partner.

```
partner/
  rachel_partner_brief.html                        ← master blank (never edit)
  rachel_partner_brief_rachel_kim.html             ← personalized copies
  rachel_partner_brief_occu.html
  Yardstake_Partner_Brief_Rachel_Kim.pdf           ← exported PDFs (optional, keep for records)
```

---

## When to Update the Brief

The brief content should be updated if:

- The free check result format changes significantly
- The $49 report contents change (new data fields, new manufacturer matches)
- Oregon Beta expands to new cities (update the footer city list)
- Victor's contact email changes

**Who updates it:** Sam edits the HTML. Victor approves. Val is notified if the referral
link format changes.

---

## Variants (Future)

If a Rachel partner has a specific use case, the brief can be lightly customized:

| Variant | What to change |
|---|---|
| Lender Rachel | Swap "listing consultation" copy for "loan application intake" framing |
| Consultant Rachel | Swap "three ways to use it" section for a single "add to your intake checklist" message |
| Co-branded version | Add Rachel's logo to the header bar alongside Yardstake (Phase 2) |

For Oregon Beta, one standard brief covers all three Rachel variants.
