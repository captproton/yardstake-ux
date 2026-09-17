# Homeowner ADU Backyard Visualization — Remote-First Design (Salt Lake City)

Grounded in the `/3D` docs (`options to present an ADU 3D model…`, `glTF.rtf`, `Salt Lake City LiDAR scan of neighborhood parcels`, `Potree tutorial for use with Rails 8`) plus web search verifying what is actually available right now (mid-2026).

---

## The problem with "step 3"

In the `glTF.rtf` workflow, **step 3 was "Capture the High-Fidelity Textures (The Video's Method)"** — sending a phone or drone to the property to shoot ground-level video, then running it through a Gaussian-splatting pipeline (Luma/Polycam/Postshot) to reconstruct the backyard photorealistically.

Everything downstream (the splat, the merge/georeference, the `.glTF` export) depends on that on-site capture. **No parcel access = no step 3 = no splat.** And the `KHR_gaussian_splatting` standard is only a few months old (Khronos RC, Feb 2026), so betting the core product on it today is risky.

So the real design question is: **how do we reconstruct enough of a homeowner's backyard — remotely — to convincingly place a modular ADU, using Salt Lake City data we can get without ever visiting?**

The web search surfaced three remote-first methods. The right answer is to **layer them**, not pick one.

---

## What's actually available for SLC remotely (verified)

| Source | What it gives you | Access | Best for |
|---|---|---|---|
| **Google Photorealistic 3D Tiles** (via CesiumJS) | Textured 3D mesh of the *entire* SLC neighborhood from aerial photogrammetry — same as Google Earth, in OGC `glTF`/Draco format | API key, streamed, no download | The "wow" remote visualization |
| **UGRC / USGS 3DEP LiDAR** | QL1 point cloud, 8 pts/m², 0.5 m DEM, <10 cm vertical accuracy for Salt Lake County (2023) | Free `.laz` download or EPT streaming | Accurate slope, roofline, setbacks, measurement |
| **Salt Lake County / SLC GIS Open Data** | Parcel boundaries, APNs, zoning, Title 19 setbacks — feature services updated **monthly** (last update May 2026) | ArcGIS REST / GeoJSON | Legal "buildable envelope" overlay |
| **`<model-viewer>` AR (WebXR / Scene Viewer / Quick Look)** | Drops the ADU into the homeowner's *real* yard, live | The homeowner's own phone | Sidestepping site access entirely |

Key insight: **Google already photogrammetrically mapped Salt Lake City.** That single fact replaces step 3 — you don't need to capture the backyard, Google did it from the air, and Cesium streams it as `glTF` (the same "JPEG moment" format the docs describe).

---

## Recommended design: three layers, tiered by fidelity

One view, backed by three interchangeable "context" sources, chosen by what you have and what the homeowner needs.

### Layer 1 — Photoreal context: Google 3D Tiles + ADU glTF (default "wow")

Remote replacement for the Gaussian splat. In a CesiumJS scene:

1. `Cesium.createGooglePhotorealistic3DTileset()` streams the SLC neighborhood mesh.
2. Geocode the homeowner's address → lat/long (or pull the parcel centroid from the County parcel service).
3. Anchor the ADU `.glb` at that coordinate, clamped to terrain:

```js
// app/javascript/controllers/digital_twin_controller.js (Stimulus)
const position = Cesium.Cartesian3.fromDegrees(lon, lat, groundHeight);
const hpr = new Cesium.HeadingPitchRoll(heading, 0, 0);   // homeowner can rotate
const model = await Cesium.Model.fromGltfAsync({
  url: this.aduUrlValue,                                   // Active Storage URL
  modelMatrix: Cesium.Transforms.headingPitchRollToFixedFrame(position, hpr)
});
viewer.scene.primitives.add(model);
```

Both Google's tiles and your ADU use real-world metric scale (the `1 unit = 1 meter` export rule), so the ADU sits correctly next to the actual house, trees, and rooflines. The carousel just swaps `aduUrlValue` and reloads the model. **Zero site access; works for any SLC address today.**

### Layer 2 — Survey-grade context: UGRC LiDAR → Potree

When accuracy matters (does it fit, what's the slope, will it shade the garden), back the same parcel with the LiDAR point cloud. The `Potree tutorial` and `Salt Lake City LiDAR` docs already nail this:

- Pull the parcel polygon from the County service → store in PostGIS.
- Background job: PDAL `filters.crop` the state `.laz` to that parcel → PotreeConverter → octree → S3/`public/`.
- Serve via the Potree WebGL viewer.
- **Discard the raw `.laz`, cache the octree permanently** (per the caching doc).

LiDAR Class 6 (buildings) extrudes the existing house; Class 2 (ground) gives true terrain slope; Classes 3–5 give tree canopy. This is the engineering/compliance view.

### Layer 3 — Live AR: the homeowner *is* your capture device

The most elegant answer to "we don't have access" — don't reconstruct the yard, let the homeowner point their phone at it. Google's `<model-viewer>` does this with one tag; AR is automatic:

```erb
<model-viewer
  src="<%= url_for(@adu.model_file) %>"          <!-- .glb for Android/WebXR -->
  ios-src="<%= url_for(@adu.usdz_file) %>"        <!-- .usdz for iOS Quick Look -->
  ar ar-modes="webxr scene-viewer quick-look"
  camera-controls auto-rotate
  alt="3D model of <%= @adu.name %>">
</model-viewer>
```

Desktop dashboard = orbit viewer; phone = "View in your space" drops the real-scale ADU onto the actual grass. One extra production cost: **export a `.usdz` alongside each `.glb`** so iOS Quick Look works.

---

## Rails architecture (your two datasets)

Two datasets, decoupled rendering.

**Dataset 1 — Parcel Digital Twin (context, dynamic)**
- `PostgreSQL + PostGIS`, gems `rgeo` / `rgeo-activerecord`.
- `Parcel`: `address`, `apn`, `geometry` (polygon, State Plane NAD83 Utah Central — *not* Web Mercator, per the alignment doc), `centroid_lat/lon`, `zoning_code`, `potree_folder`, `status`.
- A nightly/triggered job hits the **Salt Lake County parcel + zoning REST service** to populate boundary, APN, and Title 19 setbacks — no homeowner upload needed.
- Optional LiDAR job (Layer 2) via `Sidekiq`/`SolidQueue` → PDAL → PotreeConverter → S3.

**Dataset 2 — Modular ADU Catalog (product, static)**
- `AduModel`: `name`, `sqft`, `width_m`, `depth_m`, `height_m`, `price`, `model_file` (`.glb`), `usdz_file` (`.usdz`) — both in Active Storage.
- Strict export rules: 1 unit = 1 meter, origin at bottom-center of foundation.

**The fit check (compliance overlay, server-side):**
With the parcel polygon + zoning setbacks in PostGIS and the ADU footprint dimensions, compute the **buildable envelope** and validate fit before rendering, then draw that "safe zone" box in the 3D scene:

```ruby
buildable = parcel.geometry.buffer(-parcel.required_setback_m)  # rgeo/PostGIS
fits = buildable.contains?(adu_footprint_at(placement_point))
```

That turns the visualizer into a *qualification* tool (what `ADU_qualifications` reaches toward) — the homeowner sees not just a pretty render but proof it's legal.

**Presentation layer:** Rails serves ERB; a Stimulus controller (`digital_twin_controller.js`) bridges data attributes → the JS engine. **CesiumJS for Layer 1**, **Potree for Layer 2**, **`<model-viewer>` for Layer 3** — all three can live behind tabs on one `parcels#show` view.

---

## Suggested rollout

1. **Phase 0 (ship now, no site access):** Address → geocode → **Google 3D Tiles + ADU carousel** (Layer 1) + **`<model-viewer>` AR** (Layer 3). Delivers the full homeowner experience remotely. No LiDAR, no splats, no PDAL.
2. **Phase 1:** Add the **County parcel + zoning overlay** and the server-side fit/setback check — converts "looks nice" into "fits legally."
3. **Phase 2:** Add **Layer 2 LiDAR/Potree** for parcels where engineering accuracy matters.
4. **Phase 3 (optional, future):** Once `KHR_gaussian_splatting` matures and you *do* get site access, fold the original step-3 splat pipeline back in as a premium "true twin" tier — Cesium already supports streaming Gaussian splats with LOD (Apr 2026 release).

---

## Gotchas

- **CORS:** Active Storage serves `.glb` via redirect to S3/GCS — set bucket CORS to allow `GET` from your Rails domain, or the 3D canvas blocks the download.
- **Google 3D Tiles is a paid Google Maps Platform API** with per-session/usage cost and attribution requirements — budget for it; not the free UGRC route.
- **Geocoding accuracy:** address→lat/long can be off by a house. Prefer the **County parcel centroid** as the anchor, not a raw geocoder pin.
- **Projection discipline:** do all fit/setback math in NAD83 State Plane, render in WGS84.
- **iOS AR needs `.usdz`** — budget that second export per ADU.

---

## Sources

- [CesiumJS: Photorealistic 3D Tiles from Google Maps Platform](https://cesium.com/learn/cesiumjs-learn/cesiumjs-photorealistic-3d-tiles/)
- [Photorealistic 3D Tiles | Google Maps Tile API](https://developers.google.com/maps/documentation/tile/3d-tiles)
- [Cesium: 3D Gaussian Splats with Hierarchical LOD (Apr 2026)](https://cesium.com/blog/2026/04/27/3d-gaussian-splats-lod/)
- [Salt Lake County Open Data (GIS)](https://gisdata-slco.opendata.arcgis.com/)
- [Utah SGID — Salt Lake County Parcels LIR](https://opendata.gis.utah.gov/datasets/utah-salt-lake-county-parcels-lir/about)
- [UGRC — Utah Parcels](https://gis.utah.gov/data/cadastre/parcels/)
- [Greater Salt Lake MSD — Land Use & Zoning (Title 19)](https://msd.utah.gov/208/Land-Use-Zoning)
- [Augmented reality with `<model-viewer>` | Google ARCore](https://developers.google.com/ar/develop/webxr/model-viewer)
- [Apple AR Quick Look (USDZ)](https://developer.apple.com/augmented-reality/quick-look/)
- [Cesium `Model` docs — anchoring glTF via `headingPitchRollToFixedFrame`](https://cesium.com/learn/ion-sdk/ref-doc/Model.html)
