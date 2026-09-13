# Commerce: the estimate the host supplies, and the quote the page sends

The configurator page ([`../prototype/`](../prototype/)) has a footer for a
**project cost estimate** and a **Get your quote** button (#112). Both are
**slots**. The page prices nothing: a model knows dimensions, materials and
arrangements, and a price is regional, changes often and has no drawing to
trace to. The Rails app supplies the estimate and receives the quote. This
document is the contract between them. `verify_prototype.py` checks that the
example below is valid for the real manifest, that the page and
`model_contract` accept the same estimate fields, and that every event the page
uses is named here.

## The estimate

```json
{
  "model": "barn_cabin_524",
  "currency": "USD",
  "low": 150000,
  "high": 175000,
  "list": { "low": 160000, "high": 185000 },
  "note": "Placeholder figures for this contract, not a price.",
  "configuration": {
    "model": "barn_cabin_524",
    "view": "dollhouse",
    "sets": {
      "color_theme": "sage",
      "roof_colour": "weathered",
      "trim_colour": "white",
      "main_flooring": "walnut",
      "bath_flooring": "slate",
      "cabinet_finish": "natural",
      "countertop": "white_granite",
      "sconce_finish": "galvanized"
    },
    "presence": {
      "bedroom_layout": "office",
      "living_layout": "sofa",
      "porch_layout": "chairs"
    }
  }
}
```

| field | holds | required |
|---|---|---|
| `model` | the id of the model priced; an estimate for another model is refused | yes |
| `currency` | a three-letter code, e.g. `USD` | yes |
| `low`, `high` | the range, positive, `low` ≤ `high`; equal shows one figure. Whole amounts show without cents; if any figure has cents, every figure shows the currency's usual decimals | yes |
| `list` | `{low, high}`, shown struck through above the range; at or above it, since it claims a discount | no |
| `note` | one line under the range, at most 200 characters | no |
| `configuration` | the [configuration](CONFIGURATION.md) this estimate priced | no |

**Without `configuration`**, the estimate is for the model and stands for
whatever the buyer picks. **With it**, the page shows the figures only while
that is still the buyer's configuration. Once the buyer changes a choice, the
footer says the estimate is updating and shows no number until a matching
estimate arrives. A page never shows a price for a building the buyer didn't
choose.

**No estimate at all is a supported state.** The footer shows the quote button
alone. The prototype has no pricing, and a page that only works with pricing
can't be demoed.

An estimate that breaks any rule is **refused whole**. It replaces the current
estimate with none (never a half-read range, and never the previous estimate,
which may be for another configuration). The refusal is reported on the console
(`Ignoring the estimate from …`) and in `window.__viewer.commerce.problems`.

## Supplying it

Either or both:

- **In the page**, rendered by the server: `<script type="application/json"
  id="commerce-data">…</script>`. It's read once, when the model loads.
- **As an event**, at any time once the page's script has run (from
  `DOMContentLoaded` on, even while the model is still loading): dispatch
  `adu:estimate` on `document` with the estimate as `detail`, or `null` to
  clear it. The latest one sent before the footer appears is applied when it
  does, and wins over `#commerce-data`, since it's later. The page copies each
  estimate as it arrives, so changing your object afterwards changes nothing.

## Events

All on `document`, all `CustomEvent`s.

| event | sent by | `detail` | when |
|---|---|---|---|
| `adu:configuration` | the page | the configuration | once the controls have their starting choices, then on every change |
| `adu:estimate` | the host | an estimate, or `null` | whenever the host has a price, e.g. in answer to `adu:configuration` |
| `adu:quote` | the page | `{configuration, estimate, disclosure, link}` | the buyer presses **Get your quote** |

The page only **sends** `adu:configuration`. It never reads it back, so a
script that dispatches one can't make a stale estimate look current. Each
`detail` the page sends is a fresh copy, and a listener that changes it
changes nothing on the page.

In `adu:quote`, `estimate` is the one on screen, or `null` when none is shown
(none supplied, refused, or stale). `disclosure` is the manifest's disclosure,
or `null`. `link` is the page's address, which carries the configuration.

`adu:quote` is **cancelable**. A host that handles the quote calls
`event.preventDefault()`. If nobody does, the page opens its own dialog: the
chosen options by label, the estimate if one is shown, the disclosure, and the
configuration it would have sent. That's the prototype's behaviour, and it
says that nothing was sent.

```text
document.addEventListener('adu:configuration', (e) => fetchEstimate(e.detail));
document.addEventListener('adu:quote', (e) => { e.preventDefault(); startQuote(e.detail); });
```

## Where a range comes from

This is the plan's open question 2, and the contract is built not to settle it:

| source | what the host does |
|---|---|
| **per model**: one range per building | supplies one estimate without `configuration` |
| **per model plus option deltas**: the range moves as you pick | answers each `adu:configuration` with an estimate carrying that `configuration` |
| **a quote request**: no number | supplies nothing and handles `adu:quote` |

Deltas, if they come, are joined on option ids in Rails. They don't go into
`variants.json`, whose every number traces to a drawing.

## The disclosure, at the point of quoting

When the manifest has a disclosure, the footer shows it beside the button, and
`adu:quote` and the page's dialog carry it. It isn't only in the option rail.

## For the Rails app

Check an estimate before sending it with the same rules as
`model_contract.estimate_problems()`. Check a posted quote's configuration with
`model_contract.configuration_problems()`: a stale one means the buyer should
see what changed before they're quoted.
