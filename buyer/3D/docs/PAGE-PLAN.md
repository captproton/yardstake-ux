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

## What is *not* a page problem

**Styles / Roof form / Studio-vs-1-Bed.** The reference page offers four
styles, two roof shapes and a bedroom-count switch. Those are **different
buildings** — the first two change the envelope, the third moves partitions.
Our `presence` sets swap furnishings inside a fixed plan.

This is the one thing that could stop a faithful clone, and it is a product
decision rather than an engineering gap: *is a model "the product", or one
configuration of a family?* With six Concord plans and two Sacramento models
arriving, the family answer looks likely — in which case those controls become
a **model switcher**, not a morph, and the prototype should treat them that
way.

**Pricing** is a Rails concern. The page needs a slot, not a number.

---

## Shape of the prototype

Static, no build step, so Rails can serve it as-is:

```
buyer/3D/prototype/
  index.html          the page
  app.js              ES modules, three.js pinned from a CDN
  models.json         the index — which models exist
```

Every model contributes its own directory of `.glb` + `variants.json`, exactly
as `barn_cabin_524` does today.

---

## Issues

Sequenced. Each is small enough to review.

| # | | why it is where it is |
|---|---|---|
| 1 | **Model index + manifest identity** | the page cannot list models it has to be told about |
| 2 | **Viewer shell** | Draco, environment, orbit, framing from the model's own bbox |
| 3 | **SHOW INTERIOR and SHOW DIMENSIONS** | the two controls under the reference viewer |
| 4 | **The option rail** | `sets` and `presence`, rendered generically |
| 5 | **Configuration state and deep links** | the `?step=2` pattern, and the object Rails will persist |
| 6 | **Survive a manifest that is missing things** | Laurel has no porch and no loft |
| 7 | **Commerce slots** | cost estimate and CTA as stubs the Rails app fills |

**Open questions, which are the user's rather than the model's:**

1. Is a model "the product" or one of a family? Decides whether the style
   controls are a switcher or dead UI.
2. Where does the price range come from?
3. Is there a target device? It decides KTX2, which is currently **declined
   with reasons** — 68 MB of texture memory that nobody on a desktop feels.
