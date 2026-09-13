# The configuration — what a buyer chose, and what Rails will persist

The configurator page ([`../prototype/`](../prototype/)) holds everything a buyer
has chosen as one small value. The address bar always carries it, so a link
reproduces a configured building. The Rails app will store the same value and
send it with a quote request. This document is the contract between the two.
`verify_prototype.py` checks that the example below is valid for the real
manifest and that its URL decodes to it, so this page can't quietly drift.

## The shape

```json
{
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
```

| field | holds | from |
|---|---|---|
| `model` | the model's id | `prototype/models.json` → `models[].id` |
| `view` | the chosen view mode's id; **omitted**, never `null`, when the model has no `views` | `variants.json` → `views[].id` |
| `sets` | for **every** finish group, the chosen option's id | `sets[].id` → `sets[].options[].id` |
| `presence` | for **every** layout group, the chosen option's id | `presence[].id` → `presence[].options[].id` |

## The same value as a link

```text
/prototype/?model=barn_cabin_524&view=dollhouse&set.color_theme=sage&set.roof_colour=weathered&set.trim_colour=white&set.main_flooring=walnut&set.bath_flooring=slate&set.cabinet_finish=natural&set.countertop=white_granite&set.sconce_finish=galvanized&presence.bedroom_layout=office&presence.living_layout=sofa&presence.porch_layout=chairs
```

`model`, `view`, then `set.<group>=<option>` and `presence.<group>=<option>`. The
page rewrites the address as the buyer chooses, with `history.replaceState`, so
the address bar is always the current configuration and choosing a finish adds
no history entry. An `index=` parameter, when present, points the page at a
different index (the test models) and isn't part of the configuration.

## The rules, and why

- **Ids, never values.** A configuration names `sage`, never
  `[0.4, 0.44, 0.36, 1.0]`. Every finish value is a measured or sampled
  colour, and those get corrected. A saved link must keep meaning "Sage" after
  Sage is fixed.
- **Every group is written, not only the ones that differ from a default.** A
  manifest's default can change. A link that left out "the default" would
  start showing a different building the day it did.
- **The model is part of it.** A link is to a configured building, not to a
  page that happens to have options.
- **Nothing that isn't a buyer's choice.** The dimensions overlay, the camera
  position and the index are ways of looking, not choices, and aren't
  persisted.

## Stale links

A link can outlive the manifest it was made from: an option renamed, a group
removed, a model retired. The page never renders something arbitrary in
response. Each unknown thing falls back and is **reported**, on the console
(`Configuration link: …`) and in `window.__viewer.configurationProblems`:

| the link names | the page shows | and reports |
|---|---|---|
| a model the index doesn't have | the index's first model | `model: the index has no "…"; showing "…"` |
| an option a group doesn't have | that group's default, or its first option when it declares none | `set.<group> has no option "…"; showing "…"` |
| a view the model doesn't have | the default view, or the first when none is declared | `view has no option "…"; showing "…"` |
| a group this model doesn't have | nothing for it | `set.<group>=… names a group this model does not have; ignored` |
| a view when the model has none | no view | `view=… names a view this model does not have; ignored` |

The address bar then carries the configuration **actually shown**, so copying
the link after a fallback gives a link that's accurate for today's manifest.

## For the Rails app

Store the JSON above as it is. Before trusting a stored or posted configuration,
check it against the manifest of the model it names with the same rules as
`model_contract.configuration_problems()`:
- `model` matches the manifest's `model.id`
- every group the manifest offers is chosen, and every chosen id exists in its group
- `view` is present, and one of the manifest's views, exactly when the manifest has views; absent (not `null`) when it has none
- every chosen id is a string
- no other fields

A configuration that fails is a stale one. Show the buyer what changed rather
than quoting a building they didn't choose.
