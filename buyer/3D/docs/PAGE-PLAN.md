# The configurator page — plan

A prototype of the page a buyer configures an ADU on, modelled on
[studio-home.com/products/larch](https://www.studio-home.com/products/larch?step=2),
built against `barn_cabin_524` and **structured so that Concord, Richmond and
Sacramento drop in without touching the page**.

Eventually Rails. The prototype is static files and JSON so the port is
mechanical rather than a rewrite.

---

## The constraint that shapes everything

Concord, Richmond and Sacramento are not jurisdictions. They are **the next
models**:

| set | what is on disk |
|---|---|
| `concord_plans` | six pre-approved ADU plans (2025 CRC) |
| `richmond_plans` | one 1-bed bungalow permit set |
| `sacramento_adus` | A1 "Laurel" 460 sf and A2 "Willow", with renderings |

The procedure for turning one of those plan sets into a model is written up in
[adapting-a-plan-set.html](adapting-a-plan-set.html), which ends with a worked
first day on Laurel.

Model two is already planned on `adu/laurel-a1-460-plan`, and it was chosen
**precisely because it shares almost no typology with the barn cabin**:

> single storey, slab on grade, no loft, no dormers, no porch

So the page will, quite soon, be handed a model with **no ladder, no loft, no
porch, and a different bounding-box floor**. Every assumption the prototype
makes about this building is a bug waiting for that day.

**The rule for the whole prototype: the page knows nothing about any
building.** Everything it draws comes from a manifest. If the page contains
the string `barn_cabin`, a room name, or a set id, that is a defect.

---

## What we already ship

`export/variants.json`, validated at export and gated in `verify_views.py`:

| block | contents | page uses it for |
|---|---|---|
| `model` | id, display name, area with its key and source, storeys, thumbnail | the header, without a second fetch |
| `sets` | 8 sets, 23 options — each a `baseColorFactor` | the finishes rail |
| `presence` | 3 room arrangements, node names to **show** | the layout rail |
| `views` | 4 modes, node names to **hide** | SHOW INTERIOR |
| `dimensions` | 3 footprints + ridge, in feet | SHOW DIMENSIONS |
| `disclosure` | the furniture-not-included text — copy only, at most 200 characters; the reasoning is `disclosure_note` | required UI copy, on screen |

Plus `barn_cabin_524.glb` (960 KB, Draco), `lod1` (234 KB), `lod2` (30 KB).

**Reference implementations already written**: `applyChoice()` and
`applyLayout()` in [TIER-2](../models/barn_cabin_524/docs/TIER-2-materials-and-textures.md),
with two traps documented — the manifest's colours are **linear** (passing
them to `color.set()` washes everything out) and a **UI swatch needs the sRGB
encoding of the same value**, or the chip and the building disagree.

---

## What the page must supply

Read off the `.glb` rather than assumed:

- **a Draco decoder.** `extensionsRequired: ["KHR_draco_mesh_compression"]` —
  without `DRACOLoader` configured, nothing renders at all
- **lighting.** `cameras 0`, no `KHR_lights_punctual`. The reference's studio
  look is an environment map
- **transmission** for `adu_glass` (`KHR_materials_transmission`), which needs
  a transmission render target

---

## Styles, roof form and bed count — what the reference actually does

**This section used to be a guess, and the guess was wrong.** It said those
three controls were "different buildings" and would become a model switcher.
They are not. The reference page offers all three against one product. Read
off its own source, so nobody re-derives it:

Every Studio Home model ships a **composition table** in its product JSON, and
the configurator holds a fifteen-line reader:

```js
const A = w.optionKeys ?? ["interiorOption","styleOption","bedroomOption"];
const M = {...i.defaultConfiguration, ...e};   // defaults, then the choices
const S = A.map(O => M[O] ?? "").join("|");    // compose a lookup key
const P = w.files?.[S];
P?.obj ? n.push({id:`larch_${S}`, url:P.obj})
       : t.base?.obj && n.push({id:"base", url:t.base.obj});   // fallback
const N = uI(t.larchRoofs, M);                 // a SECOND, independent lookup
N?.obj && n.push({id:`roof_larch_${N.key}`, url:N.obj, optional:true});
```

**Join the chosen option ids with `|`, look up a file, load it.** Larch's
twenty-eight `.obj` files split in two:

| | axes | files |
|---|---|---|
| **body** | 2 bed counts × 3 interiors × 4 styles | **24** — the whole cross product, pre-baked |
| **roof** | 2 forms × 2 styles | **4**, named by size (`roof-490-cross-gable…`) |

So composition is **half real**:

- **The roof genuinely is a separate additive part** — its own mesh, its own
  axes, `optional: true`, and namespaced by the shell's square footage rather
  than the model name. That is layering, and it works.
- **Interior layout and style are not composed at all.** Shell and interior
  ship as one file **per combination of all three axes** — 2 bed counts × 3
  interiors × 4 styles, which is where the 24 comes from. And style changes
  *geometry*, not a texture: `…_center-hall_craft` and `…_center-hall_trad`
  are different files with the same interior.

**Material and colour are a third, orthogonal axis** — flooring, counters,
cabinets and siding are plain PNG/JPG applied over whichever body loaded.

**That axis is our `sets` block, but the mechanism is not the same, and the
difference is the page's to implement.** They swap the *picture*: a different
image file per option. We swap a **`baseColorFactor`** — all 8 sets declare
`property: "baseColorFactor"`, 23 options are RGBA values, and
`export/variants.json` references no image at all. The albedo, normal and
roughness maps ship **once** in the base asset and every option tints the same
ones.

That is the cheaper arrangement and it is why ours has normal maps to begin
with: one texture set serves N options instead of N texture sets serving N
options. It also means `applyChoice()` writes a factor, never a map — and that
the manifest's colours are **linear**, which is the first of the two traps
documented in TIER-2.

Four things follow that are ours to act on:

1. **The key-join pattern is worth copying.** It serialises into a URL,
   degrades to `base` rather than an empty viewer when a combination is
   missing, and our `presence` options are already ids.
2. **They pay the cross product in files**, per model, and Robinia, Rowan and
   Raintree each carry their own set. It is the price of never solving an
   alignment problem — and it is why *"one builder wants to move a wall"* is
   outside this design entirely. A continuous parameter cannot live in a
   lookup table.
3. **They have tried runtime assembly and retreated.** The bundle still
   carries a dead branch that places `frontPanel / backPanel / leftPanel /
   rightPanel / roof` procedurally from width and depth in inches, and another
   that loads `base.left` + `base.right` halves. Larch uses neither. Only the
   roof is composed at runtime. That is a measured result, not an oversight.
4. **Their reader has five copy-pasted branches** — one each for Laurel,
   Robinia, Larch, Rowan and Raintree, identical but for the roof helper.
   Model-specific code in the page is what this plan's central rule already
   forbids; this is what breaking it looks like at five models. Read one
   generic `combinations` block, not a branch per builder.

Tracked as [#113](https://github.com/captproton/yardstake-ux/issues/113), which sets out the three tiers of variant
and says which of them we can already do.

**Pricing** is a Rails concern. The page needs a slot, not a number. The
reference agrees — it ships pricing as three separate bundles
(`studio-pricing-data.js`, `studio-pricing-runtime.js`,
`studio-price-components.js`) that the viewer never touches.

---

## Shape of the prototype

Static, no build step, so Rails can serve it as-is:

```
buyer/3D/prototype/
  index.html          the page; three.js 0.186.0 pinned once, in its import map   (#107, done)
  app.js              ES modules: index → manifest header → levels, coarse first  (#107, done)
                      view modes and the dimension overlay under the viewer      (#108, done)
                      the option rail: finishes, layouts, disclosure             (#109, done)
                      the configuration, kept in the address bar                 (#110, done)
                      the commerce footer: an estimate the host supplies, the quote (#112, done)
  models.json         the index — which models exist                             (#106, done)
  fixtures/           four generated models and their own index, for ?index=fixtures/models.json:
                      a slab box (2 finish sets, a bench layout, 3 view modes, no `with_porch`);
                      identity only (`{"model": ...}`); one view mode; and the barn
                      cabin reduced (#111) -- its own .glb files, minus a layout
                      group, two view modes and `with_porch`. The directory must be
                      exactly what make_fixtures.py generates (gate 3, --check)
buyer/3D/
  adu_kit/            what every model's Blender scripts share: the geometry kernel,
                      the .glb export, inside_mesh() (#126)
  build_index.py      writes prototype/models.json from every exported model
  verify_index.py     gates it, no Blender
  verify_prototype.py gates the page: it names nothing any model publishes, three.js
                      is pinned, the fixture meets the contract, both documents match
                      the page — no browser
  adu_kit/schema/model_contract.py
                      what a valid identity, index row, .glb read, configuration and
                      estimate are — imported by finish_adu.py, build_index.py,
                      verify_index.py, verify_prototype.py
  docs/CONFIGURATION.md  what a buyer chose, as a link and as the object Rails persists
  docs/COMMERCE.md       the estimate Rails supplies and the events the page sends (#112)
  probes/run_probes.py   the probe suite: every break-one-thing case, against a copy (#121, done);
                         --self-check checks the harness itself
```

Every model contributes its own directory of `.glb` + `variants.json`, exactly
as `barn_cabin_524` does today.

**Run the probe suite before merging** a change to `verify_index.py`,
`verify_prototype.py`, `build_index.py`, `adu_kit/schema/model_contract.py`,
`finish_adu.py`, `adu_kit/`, `prototype/app.js` or the fixtures:
`python3 buyer/3D/probes/run_probes.py`. Every gate passing on a clean tree
says nothing about whether it still catches its case; the suite does. It
breaks a temporary copy, never the working tree. A change that adds a gate
adds its cases to the matching `probes/cases_*.py`; a change to the harness
itself runs `run_probes.py --self-check` too.

**CI runs the checks that need no Blender** on every pull request and push to
`main` that touches `buyer/3D/`
([`.github/workflows/buyer-3d-checks.yml`](../../../.github/workflows/buyer-3d-checks.yml),
#139): `build_index.py --check`, `verify_index.py`, `verify_prototype.py`,
`make_fixtures.py --check`, the probe suite and its self-check, on Python 3.12,
and the plan-set harvester's tests (`adu_kit/test_sheets.py`, #127) and the spec
lint on Laurel's spec (`adu_kit/spec_lint.py`, #128), for which it installs
`pdftotext` and PyYAML, and Laurel's `verify_spec.py`. A model with a spec and
no export yet must declare it in an `EXPORT_PENDING` file whose `issue: #N`
line names the issue that will export it; gate 6 of `verify_index.py` lists it
instead of failing.
**It does not run** the barn cabin's nine Blender gates or the byte-identical
export check. Those are still run by hand, and a PR that touches a model or
`adu_kit/` says so when it has run them.

**Serve `buyer/3D`, not `prototype/`.** Every path in `models.json` is relative
to the index and climbs out of it (`../models/<id>/…`), so the page lives at
`/prototype/index.html` under a server rooted one level up. A server rooted
at `prototype/` cannot reach a single model. Locally:
`python3 -m http.server 8316 --directory buyer/3D`, then `/prototype/`.

**What the viewer shell found, reading the `.glb` rather than the notes**
([#116](https://github.com/captproton/yardstake-ux/pull/116)):

- **The front faces +Z in the export** — the covered entry, its posts and the
  entry door sit at the maximum-Z end. The axis notes in
  [`adapting-a-plan-set.html`](adapting-a-plan-set.html) imply −Z. The viewer
  follows the file, and the page's one remaining assumption about a building
  is which end to show first: [#117](https://github.com/captproton/yardstake-ux/issues/117).
- **The box floor depends on the level.** `lod0` reaches the footing at
  −1.175 m; `lod1` and `lod2` stop at −0.972 m. The ground sits at the floor
  of the level shown first, the coarsest, and does not drop when detail lands.
- **Framing fits the box's eight corners, not a sphere**, and refits on
  resize and when a finer level reaches past the coarse box — without
  undoing a buyer's orbit. `window.__viewer.fits()` and `.pose()` are the
  hooks a browser test reads.

**What the two controls settled**
([#118](https://github.com/captproton/yardstake-ux/pull/118)):

- **A manifest block is whole or refused.** `views` or `dimensions` absent:
  no control, quietly (#111). Present but malformed *anywhere*: no control,
  a console error, and an entry in `window.__viewer.manifestProblems` —
  never a mode that hides less than it says, or a legend missing a
  footprint. The same rules are `model_contract.views_problems()` and
  `dimensions_problems()`, run by `finish_adu.py` before it writes,
  `verify_index.py` gate 8, and the fixtures; gate 7 now checks every node a
  view hides is in the `.glb` (55 names).
- **Modes are the manifest's, not the page's.** Its order, its labels, its
  default; four buttons for the barn cabin, three for a fixture, none for
  one mode — which is still applied — or for none.
- **Footprints are listed, one is drawn.** The overlay draws `with_porch`,
  else `main_body`, else `overall`, and the legend lists every footprint
  with the manifest's own note. Sizes carry no position, so the drawn one is
  centred: exact for `with_porch` and `overall` here, 0.914 m out for
  `main_body` — [#119](https://github.com/captproton/yardstake-ux/issues/119).
- **Units are read, and kept in step.** An unknown unit refuses the block;
  `verify_prototype.py` gate 4 fails if `app.js` and `model_contract` accept
  different units.

**What the option rail settled**
([#120](https://github.com/captproton/yardstake-ux/pull/120)):

- **Linear in, sRGB out.** A finish writes the manifest's linear value with
  `setRGB(…, LinearSRGBColorSpace)`; its swatch chip is the sRGB encoding of
  the same colour. All 23 options checked: every chip equals its material's
  own colour. Charcoal's chip is `#6c6e6f`; painting the manifest's numbers
  would have given `#262829`.
- **Layouts are applied on load, and combine with view modes.** A node is
  visible only if the view mode does not hide it *and*, when a layout names
  it, a chosen layout shows it — checked under all four modes.
- **Presence fails closed.** A malformed `presence` block hides every node it
  names and renders no layout control: unfurnished is plain, every
  arrangement at once is broken. It cannot hide a node the manifest never
  names; `finish_adu.py`'s check that every furniture node is controlled
  covers that at export.
- **A manifest that cannot be read stops the page.** Error, no model. It is
  not "a model with no options" — without it nothing can hide the
  arrangements the model ships together.
- **The disclosure is copy.** The barn cabin's had a paragraph of reasoning
  after the sentence, in capitals, which would have gone on screen.
  `spec.yaml` now splits it into `disclosure` and `disclosure_note`;
  `model_contract` caps the copy at 200 characters, counted as code points on
  both sides, and gate 4 keeps the two limits equal.
- **Not browser-verified:** re-applying choices when full detail replaces the
  coarse level — the detail loaded before a click could land.
- **Open, and the owner's call:** dark finishes read lighter than their names
  (Charcoal quartz is a medium grey, `#69696a`). The page decodes the values
  correctly; if they look wrong, the fix is in `spec.yaml`.

**What the configuration settled**
([#122](https://github.com/captproton/yardstake-ux/pull/122)) — the contract is [`CONFIGURATION.md`](CONFIGURATION.md):

- **A link is a configured building.** `?model=…&view=…&set.<group>=…&presence.<group>=…`,
  rewritten with `replaceState` as the buyer chooses, so the address bar is
  always the configuration and a choice adds no history entry. The same
  value, as JSON, is what Rails will store and send with a quote.
- **Ids, never values; every group, not only non-defaults.** A link must
  survive a colour being corrected and a default being changed.
- **A stale link falls back and says so.** An unknown model (which used to
  show the first model silently), view, option or group is reported on the
  console and in `window.__viewer.configurationProblems`, and the address is
  rewritten to what is actually shown.
- **One shape for "no views":** `view` is omitted, never `null` — in the
  page's published object, the document, and the check.
- **Ids are data, not keys to trust.** Id-keyed collections have no
  prototype, so a link naming `set.__proto__` is reported like any unknown
  group instead of vanishing.
- **Rails has a check to run.** `model_contract.configuration_problems()`
  validates a stored configuration against its manifest and never raises on
  malformed input; `verify_prototype.py` gate 5 holds the document's example
  and link to the real manifest.
- **A process finding.** The command that opened #122 ran a probe that
  failed and did not stop on it, so the PR went up with a traceback in gate
  5; the fix followed in the same PR. The probes are the only thing that
  proves a gate still catches its case, and they are not yet in the repo —
  [#121](https://github.com/captproton/yardstake-ux/issues/121).

**What the probe suite settled**
([#123](https://github.com/captproton/yardstake-ux/pull/123)):

- **One command, 92 cases, about 15 seconds.** One module per PR round
  (#115, #116, #118, #120, #122) plus clean runs; a case passes only if every
  script exits as expected, prints no traceback, and prints the expected
  message. The #115 round had not run since #115, and one message had
  drifted.
- **It breaks a copy.** About 3 MB of what the checks read, rebuilt fresh for
  each case in a temporary directory; thumbnail paths are contained, so
  nothing is read or written outside it.
- **A stale case says so.** A setup whose target file, text or node has gone
  — or whose text now matches more than once — fails as *stale*, rather than
  running against an unbroken file and passing. A Blender case runs its setup
  before it is skipped, so machines without Blender still report one that
  has drifted.
- **The harness is checked too.** `--self-check` runs 13 checks of the
  harness's own failure modes: escaping and unusable paths, a malformed
  index, a hanging script, a Blender that cannot start, a contract result
  that is not text, and stale setups.
- **Proved by breaking real gates.** Disabling the alpha rule, disabling the
  disclosure-limit comparison, and reintroducing the `rows or []` traceback
  that shipped in #122 each turned their case BAD; undoing each harness fix
  turned its self-check BAD.
- **Still outside the repo:** those break-a-real-gate mutation scripts. The
  suite proves each gate catches its case; nothing in the repo yet proves
  the suite itself would notice a gate being weakened. And the browser
  checks — swatches against materials, layouts under view modes, framing —
  were one-off JavaScript and belong in a browser test runner.

**What a model with parts missing settled**
([#124](https://github.com/captproton/yardstake-ux/pull/124)):

- **Taking parts away breaks nothing.** The reduced barn cabin renders two
  layout groups and two view buttons with no problems and no console errors;
  the identity-only model loads and orbits with no controls and no rail.
- **Missing `with_porch` falls back, but in the wrong place.** The overlay
  draws `main_body`, labelled correctly, 0.914 m from the real heated box,
  because a manifest gives footprints no position — measured here, carried
  by [#119](https://github.com/captproton/yardstake-ux/issues/119).
- **A fixture is only as good as its freshness.** The reduced fixture is
  derived from the barn cabin's manifest, not copied, and generation stops
  if the barn cabin no longer has what it removes. Gate 3 and
  `make_fixtures.py --check` require the directory to be exactly what the
  generator makes: a stale, missing or leftover file fails, and a normal run
  removes leftovers, so "re-run make_fixtures.py" is always the remedy.
- **Every published level is read.** A missing or corrupt lod0 *or* lod2 in
  the barn cabin is a named generation failure, not a traceback and not a
  pass; fixture rows list levels in `build_index.py`'s order.
- **Three review rounds, each proved.** 20 fixture cases, 112 in the suite;
  disabling each new check (the freshness comparison, leftover reporting,
  leftover removal, the level reads, the level order) turned its cases BAD.

**What the commerce slots settled**
([#125](https://github.com/captproton/yardstake-ux/pull/125)):

- **The page prices nothing, and still demos.** With no estimate the footer
  is the quote button alone, with the disclosure beside it. An estimate comes
  from the host, as a `#commerce-data` block or an `adu:estimate` event, and
  is checked whole. A refused one shows no figure: never a half-read range,
  and never the previous estimate.
- **A price is never shown for a building the buyer didn't choose.** An
  estimate may name the configuration it priced. It's shown only while that
  is still the configuration; after a change the footer says it is updating.
- **Open question 2 doesn't block the page.** The contract serves all three
  answers: one range per model, a range that moves with each choice (answer
  each `adu:configuration`), or no number (handle `adu:quote`). Deltas would
  join on option ids in Rails, not live in `variants.json`.
- **Events are a trust boundary.** Three review rounds found the same
  kind of hole three ways: an estimate sent during start-up was lost; the
  page kept objects a listener could edit, or a script could forge an
  `adu:configuration` to make a stale estimate look current; and a `BigInt`
  or a loop inside an estimate threw instead of being refused, once stopping
  the page from loading. The rules now: listen from the start, copy
  everything that crosses, never read back an event the page sends, and
  accept only plain JSON.
- **An unreadable file is a failed gate.** Every page file and document is
  read through one guard, whether the filesystem refuses or the bytes are
  not text.
- **Proved both ways.** Each JavaScript finding failed in the browser on the
  unfixed page before passing, and each Python fix turned its probes BAD
  when undone. 27 commerce cases, 139 in the suite. A browser test caught
  itself running a cached `app.js`; the resource size shows which copy ran.
- **Left for later:** on a narrow screen the rail's disclosure and the
  footer's sit next to each other; one should hide there.

---

## Issues

Sequenced. Each is small enough to review.

**The sequence is complete** (as of #125). The page configures an ADU from
its manifest: it lists models, frames them, offers view modes, dimensions,
finishes and layouts, keeps the configuration in a link, and hands an
estimate slot and a quote to Rails, all without naming any building. What
remains is below: #111's second-export box, the issues outside the
sequence, and the open questions.

**Done:** [#112](https://github.com/captproton/yardstake-ux/issues/112), the commerce slots ([#125](https://github.com/captproton/yardstake-ux/pull/125)). [#121](https://github.com/captproton/yardstake-ux/issues/121), the probe suite ([#123](https://github.com/captproton/yardstake-ux/pull/123)) — first, as planned, because
the probes that proved every gate lived only outside the repo.
[#111](https://github.com/captproton/yardstake-ux/issues/111), a model with parts missing ([#124](https://github.com/captproton/yardstake-ux/pull/124)) — all but the box
carried from #106, so the issue stays open until a second model is exported.

| # | | why it is where it is |
|---|---|---|
| [#106](https://github.com/captproton/yardstake-ux/issues/106) | **Model index + manifest identity** | the page cannot list models it has to be told about — **done** ([#115](https://github.com/captproton/yardstake-ux/pull/115)); its one unprovable box, a real second export, moved to #111 |
| [#107](https://github.com/captproton/yardstake-ux/issues/107) | **Viewer shell** | Draco, environment, orbit, framing from the model's own bbox — **done** ([#116](https://github.com/captproton/yardstake-ux/pull/116)); proved against a generated second model in `prototype/fixtures/` |
| [#108](https://github.com/captproton/yardstake-ux/issues/108) | **SHOW INTERIOR and SHOW DIMENSIONS** | the two controls under the reference viewer — **done** ([#118](https://github.com/captproton/yardstake-ux/pull/118)); the manifest's modes and footprints, whole or refused |
| [#109](https://github.com/captproton/yardstake-ux/issues/109) | **The option rail** | `sets` and `presence`, rendered generically — **done** ([#120](https://github.com/captproton/yardstake-ux/pull/120)); linear colours in, sRGB swatches out, layouts applied on load |
| [#110](https://github.com/captproton/yardstake-ux/issues/110) | **Configuration state and deep links** | the `?step=2` pattern, and the object Rails will persist — **done** ([#122](https://github.com/captproton/yardstake-ux/pull/122)); the contract is [`CONFIGURATION.md`](CONFIGURATION.md) |
| [#111](https://github.com/captproton/yardstake-ux/issues/111) | **Survive a manifest that is missing things** | Laurel has no porch and no loft — **done except one box** ([#124](https://github.com/captproton/yardstake-ux/pull/124)): the barn cabin reduced (its own `.glb` files, minus a layout group, two view modes and `with_porch`) renders a working page; the identity-only fixture loads and orbits with no controls and no rail; fixtures must match their generator. **Open:** the box carried from #106 — a real second export lands as a row with no page code — until a second model is exported |
| [#112](https://github.com/captproton/yardstake-ux/issues/112) | **Commerce slots** | cost estimate and CTA as stubs the Rails app fills — **done** ([#125](https://github.com/captproton/yardstake-ux/pull/125)); the contract is [`COMMERCE.md`](COMMERCE.md). The quote carries the configuration from [`CONFIGURATION.md`](CONFIGURATION.md); the footer works with no price, and serves every answer to open question 2 |

Not in the sequence, because nothing above is blocked on it:

| # | | |
|---|---|---|
| [#113](https://github.com/captproton/yardstake-ux/issues/113) | **Three tiers of variant** | the pre-bake / compose boundary, needed before a SECOND builder arrives |
| [#117](https://github.com/captproton/yardstake-ux/issues/117) | **Declare the model's front** | the viewer assumes +Z; a model exported another way opens from behind. Needed before a second real model: step 6 of the [Laurel plan](../models/laurel_a1_460/docs/PLAN.md), before Laurel's export |
| [#119](https://github.com/captproton/yardstake-ux/issues/119) | **Declare where each footprint sits** | `dimensions` gives sizes, not positions; the overlay centres the footprint, which puts `main_body` 0.914 m out. Needed before an off-centre footprint is drawn: step 9 of the Laurel plan |
| [#121](https://github.com/captproton/yardstake-ux/issues/121) | **Keep the probe suite** | the break-one-thing checks that proved every gate, in the repo with one command, run against a copy — **done** ([#123](https://github.com/captproton/yardstake-ux/pull/123)); 92 cases at the time, 139 now, and 13 harness self-checks |
| [#139](https://github.com/captproton/yardstake-ux/issues/139) | **Run the checks in CI** | nothing ran them on GitHub; every "green" was a hand run on one Mac — **done** ([#140](https://github.com/captproton/yardstake-ux/pull/140)); the six checks that need no Blender run on every PR and push to `main` touching `buyer/3D/`, proved to fail on a deliberate break. Not yet a required check on `main` |

**Open questions, which are the user's rather than the model's:**

1. ~~Is a model "the product" or one of a family?~~ **Answered, and not by
   us.** The reference offers styles, interiors and bed count against one
   product, so a model is the product *and* the options are real. The live
   question is narrower and it is a cost question: **which variants do we
   pre-bake, and which do we compose?** [#113](https://github.com/captproton/yardstake-ux/issues/113).
2. Where does the price range come from? **Still open, and no longer
   blocking.** [`COMMERCE.md`](COMMERCE.md) serves one range per model, a
   range that moves with each choice, or no number at all. The answer decides
   what Rails builds, not what the page does.
3. Is there a target device? It decides KTX2, which is currently **declined
   with reasons** — 68 MB of texture memory that nobody on a desktop feels.
4. **Are the dark finish values what you intend?** The page decodes them
   correctly, and they read lighter than their names: Charcoal quartz shows
   as a medium grey (`#69696a`), because 0.14 linear is 14% reflectance. If
   that is wrong, the fix is the values in `spec.yaml`, not the page.
5. **Commit `.claude/launch.json`?** It starts the preview server rooted at
   `buyer/3D` on port 8316. Committed, anyone previewing the page gets the
   same server; left local, each person sets their own up.
