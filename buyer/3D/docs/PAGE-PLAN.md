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
| `disclosure` | the furniture-not-included text | required UI copy |

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
  models.json         the index — which models exist                             (#106, done)
  fixtures/           a generated second model and its own index, for ?index=fixtures/models.json
buyer/3D/
  build_index.py      writes prototype/models.json from every exported model
  verify_index.py     gates it, no Blender
  verify_prototype.py gates the page: it names nothing any model publishes, three.js
                      is pinned, the fixture meets the contract — no browser
  model_contract.py   what a valid identity, index row and .glb read are —
                      imported by finish_adu.py, build_index.py, verify_index.py
```

Every model contributes its own directory of `.glb` + `variants.json`, exactly
as `barn_cabin_524` does today.

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

---

## Issues

Sequenced. Each is small enough to review.

| # | | why it is where it is |
|---|---|---|
| [#106](https://github.com/captproton/yardstake-ux/issues/106) | **Model index + manifest identity** | the page cannot list models it has to be told about — **done** ([#115](https://github.com/captproton/yardstake-ux/pull/115)); its one unprovable box, a real second export, moved to #111 |
| [#107](https://github.com/captproton/yardstake-ux/issues/107) | **Viewer shell** | Draco, environment, orbit, framing from the model's own bbox — **done** ([#116](https://github.com/captproton/yardstake-ux/pull/116)); proved against a generated second model in `prototype/fixtures/` |
| [#108](https://github.com/captproton/yardstake-ux/issues/108) | **SHOW INTERIOR and SHOW DIMENSIONS** | the two controls under the reference viewer |
| [#109](https://github.com/captproton/yardstake-ux/issues/109) | **The option rail** | `sets` and `presence`, rendered generically |
| [#110](https://github.com/captproton/yardstake-ux/issues/110) | **Configuration state and deep links** | the `?step=2` pattern, and the object Rails will persist |
| [#111](https://github.com/captproton/yardstake-ux/issues/111) | **Survive a manifest that is missing things** | Laurel has no porch and no loft |
| [#112](https://github.com/captproton/yardstake-ux/issues/112) | **Commerce slots** | cost estimate and CTA as stubs the Rails app fills |

Not in the sequence, because nothing above is blocked on it:

| # | | |
|---|---|---|
| [#113](https://github.com/captproton/yardstake-ux/issues/113) | **Three tiers of variant** | the pre-bake / compose boundary, needed before a SECOND builder arrives |
| [#117](https://github.com/captproton/yardstake-ux/issues/117) | **Declare the model's front** | the viewer assumes +Z; a model exported another way opens from behind. Needed before a second real model |

**Open questions, which are the user's rather than the model's:**

1. ~~Is a model "the product" or one of a family?~~ **Answered, and not by
   us.** The reference offers styles, interiors and bed count against one
   product, so a model is the product *and* the options are real. The live
   question is narrower and it is a cost question: **which variants do we
   pre-bake, and which do we compose?** [#113](https://github.com/captproton/yardstake-ux/issues/113).
2. Where does the price range come from?
3. Is there a target device? It decides KTX2, which is currently **declined
   with reasons** — 68 MB of texture memory that nobody on a desktop feels.
