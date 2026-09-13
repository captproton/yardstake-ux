// app.js — the viewer shell (#107), the two controls under it (#108) and the
// option rail beside it (#109).
//
// THE PAGE KNOWS NOTHING ABOUT ANY BUILDING. It reads an index, picks a row,
// reads that row's manifest for the header, the controls and the rail, and
// loads the row's .glb levels. No model id, display name, room, node,
// material, set, option or view id appears in this file, and
// verify_prototype.py fails if one does.
//
// Served from buyer/3D, so this page is /prototype/index.html and the index's
// ../models/<id>/ paths resolve. A server rooted at prototype/ reaches nothing.
//
//   ?model=<id>              which row of the index to show (default: the first)
//   ?index=<same-site path>  a different index, e.g. fixtures/models.json

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

// THE DRACO DECODER MUST MATCH THE LOADER'S RELEASE. The import map in
// index.html pins the release; REVISION reads it back, so the version is
// written down exactly once. The loader only decodes what a file asks for:
// a level that REQUIRES KHR_draco_mesh_compression -- every level finish_adu.py
// exports does -- renders nothing without it, and a plain glTF such as the
// fixture never touches it.
const DRACO_DECODERS =
  `https://cdn.jsdelivr.net/npm/three@0.${THREE.REVISION}.0/examples/jsm/libs/draco/gltf/`;

// THE FRONT FACES +Z IN THE EXPORTED FILE, read off the .glb rather than off
// the axis notes: the covered entry, its posts and the entry door all sit at
// the maximum-Z end of the box. The first view looks at that end from a three-
// quarter angle above it, and the width dimension is drawn along it. No
// manifest declares a front yet (#117); until one does, this is an export
// convention the page assumes, and the only one.
const VIEW_DIRECTION = new THREE.Vector3(0.7, 0.45, 1).normalize();

const LEVEL = /^lod(\d+)$/;

// UNITS ARE READ, NEVER ASSUMED. A manifest in a unit this page does not know
// gets no overlay rather than an overlay at the wrong scale. Keep in step with
// model_contract.DIMENSION_UNITS; verify_prototype.py gate 4 checks.
const UNITS = {
  feet: { metres: 0.3048, label: 'ft' },
  foot: { metres: 0.3048, label: 'ft' },
  ft: { metres: 0.3048, label: 'ft' },
  metres: { metres: 1, label: 'm' },
  meters: { metres: 1, label: 'm' },
  m: { metres: 1, label: 'm' },
};

// WHICH FOOTPRINT THE OVERLAY DRAWS. The manifest carries several and says
// which question each answers; the overlay draws the building a buyer sees --
// the whole slab first, then the heated box, then the extent over the eaves --
// and LISTS every footprint beside it. Collapsing them into one "size" throws
// away the difference a setback check needs. Any other footprint a manifest
// declares is listed after these, in the manifest's own order.
const FOOTPRINT_ORDER = ['with_porch', 'main_body', 'overall'];

// The only material property and the only node property this page applies.
// A block that asks for anything else is refused whole, not half-applied.
const SET_PROPERTY = 'baseColorFactor';
const PRESENCE_PROPERTY = 'visible';

// The disclosure is buyer-facing copy, shown verbatim. A paragraph of notes
// for developers is not copy; model_contract.DISCLOSURE_MAX_CHARS agrees.
const DISCLOSURE_MAX_CHARS = 200;

const $ = (id) => document.getElementById(id);

function setStatus(text) {
  $('status').textContent = text;
  $('status').hidden = !text;
}

main().catch((err) => {
  console.error(err);
  setStatus(`Could not load the model: ${err.message}`);
  window.__viewer = { state: 'error', error: err.message };
});

async function main() {
  const params = new URLSearchParams(location.search);
  const indexUrl = new URL(params.get('index') ?? 'models.json', location.href);
  if (indexUrl.origin !== location.origin) {
    throw new Error('the index must be served from this site');
  }

  const index = await fetchJSON(indexUrl);
  const rows = Array.isArray(index?.models) ? index.models : [];
  if (!rows.length) throw new Error(`${indexUrl.pathname} lists no models`);
  const row = rows.find((r) => r.id === params.get('model')) ?? rows[0];

  renderPicker(rows, row, params);
  const viewer = createViewer($('viewer'));

  // The manifest's own identity block is the header's source, so a page that
  // loaded one model needs nothing else. The index row carries the same
  // fields, and stands in if the manifest cannot be read.
  const manifest = await fetchJSON(new URL(row.manifest, indexUrl)).catch(() => null);
  renderHeader(manifest?.model ?? row);

  const levels = orderLevels(row, indexUrl);
  if (!levels.length) throw new Error(`${row.id} lists no level to load`);

  for (const [i, level] of levels.entries()) {
    const last = i === levels.length - 1;
    setStatus(i === 0 ? 'Loading…' : 'Loading full detail…');
    let gltf;
    try {
      gltf = await viewer.load(level.url);
    } catch (err) {
      if (i === 0) throw err;
      // The coarse level is already on screen and orbitable. Say so rather
      // than replacing a working view with an error -- and END in a state, so
      // anything waiting for the viewer to settle stops waiting.
      console.error(err);
      setStatus('Showing a simplified model — full detail did not load.');
      window.__viewer = { ...window.__viewer, state: 'degraded', error: err.message };
      return;
    }
    const framed = viewer.show(gltf.scene);
    window.__viewer = {
      ...window.__viewer,
      state: last ? 'ready' : 'loading',
      model: row.id,
      level: level.name,
      levels: levels.map((l) => l.name),
      ...framed,
      fits: viewer.fits,
      pose: viewer.pose,
      visibility: viewer.visibility,
      overlay: viewer.overlay,
      tints: viewer.tints,
      presence: viewer.presence,
      material: viewer.material,
      isVisible: viewer.isVisible,
    };
    // The controls and the rail need something on screen to act on, so they
    // appear with the first level. Every choice is re-applied when full
    // detail replaces it: its materials and nodes are new objects.
    if (i === 0) {
      const problems = [];
      renderControls(readViews(manifest, problems), readDimensions(manifest, problems), viewer);
      const presence = readPresence(manifest, problems);
      if (presence.failClosed.length) viewer.setPresence(presence.failClosed, []);
      renderRail(readSets(manifest, problems), presence.groups,
        readDisclosure(manifest, problems), viewer);
      window.__viewer = { ...window.__viewer, manifestProblems: problems };
    }
  }
  setStatus('');
}

// LEVELS, COARSEST FIRST. The coarsest level is tens of kilobytes, so there is
// a building on screen almost at once; full detail replaces it when it lands.
// At most two are loaded -- a one-building page gains nothing from distance-
// based switching, since the whole building is always in view.
function orderLevels(row, base) {
  const levels = Object.entries(row.levels ?? {})
    .map(([name, path]) => ({ name, n: Number(LEVEL.exec(name)?.[1]), url: new URL(path, base) }))
    .filter((l) => Number.isInteger(l.n))
    .sort((a, b) => b.n - a.n);
  if (!levels.some((l) => l.n === 0) && row.primary) {
    levels.push({ name: 'primary', n: 0, url: new URL(row.primary, base) });
  }
  return levels.length > 2 ? [levels[0], levels[levels.length - 1]] : levels;
}

// ── manifest blocks: whole or not at all ──────────────────────────────────
// An ABSENT block renders no control, quietly: a model need not describe what
// it lacks (#111). A PRESENT block that is malformed ANYWHERE renders no
// control either, and says why -- on the console and in
// window.__viewer.manifestProblems. Acting on the entries that happen to
// parse would show a mode that hides less than it claims, a legend that omits
// a footprint, or a finish that tints half its materials, and nothing would
// look wrong. The same rules are model_contract.display_problems(), which
// finish_adu.py and verify_index.py run, so a malformed block should never
// reach this page at all.

const DIMENSION_FIELDS = new Set(['units', 'note', 'height_to_ridge']);

const positive = (n) => typeof n === 'number' && Number.isFinite(n) && n > 0;
const text = (s) => typeof s === 'string' && s.trim() !== '';
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function refuse(problems, block, problem) {
  problems.push(`${block}: ${problem}`);
  console.error(`Ignoring the manifest's ${block}: ${problem}`);
}

function readViews(manifest, problems) {
  const views = manifest?.views;
  if (views == null) return [];
  const problem = viewsProblem(views);
  if (problem) {
    refuse(problems, 'views', problem);
    return [];
  }
  return views.map((v) => ({
    id: v.id,
    label: v.label,
    desc: v.desc ?? '',
    isDefault: v.default === true,
    hide: v.hide,
  }));
}

function viewsProblem(views) {
  if (!Array.isArray(views)) return 'not a list';
  const ids = new Set();
  let defaults = 0;
  for (const [i, v] of views.entries()) {
    const at = `views[${i}]`;
    if (!isObject(v)) return `${at} is not an object`;
    if (!text(v.id)) return `${at}.id is not a non-empty string`;
    if (ids.has(v.id)) return `${at}.id repeats an earlier id`;
    ids.add(v.id);
    if (!text(v.label)) return `${at}.label is not a non-empty string`;
    if (v.desc !== undefined && typeof v.desc !== 'string') return `${at}.desc is not a string`;
    if (v.default !== undefined && typeof v.default !== 'boolean') return `${at}.default is not true or false`;
    if (v.default === true) defaults += 1;
    if (!Array.isArray(v.hide) || !v.hide.every((n) => typeof n === 'string')) {
      return `${at}.hide is not a list of strings`;
    }
  }
  return defaults > 1 ? 'more than one view is the default' : null;
}

function readDimensions(manifest, problems) {
  const d = manifest?.dimensions;
  if (d == null) return null;
  const problem = dimensionsProblem(d);
  if (problem) {
    refuse(problems, 'dimensions', problem);
    return null;
  }
  const rank = (key) => {
    const i = FOOTPRINT_ORDER.indexOf(key);
    return i < 0 ? FOOTPRINT_ORDER.length : i;
  };
  const footprints = Object.entries(d)
    .filter(([key]) => !DIMENSION_FIELDS.has(key))
    .map(([key, v]) => ({ key, width: v.width, depth: v.depth, note: v.note ?? '' }))
    .sort((a, b) => rank(a.key) - rank(b.key));
  return {
    unit: UNITS[d.units.toLowerCase()],
    footprints,
    ridge: d.height_to_ridge ?? null,
  };
}

function dimensionsProblem(d) {
  if (!isObject(d)) return 'not an object';
  if (typeof d.units !== 'string' || !UNITS[d.units.toLowerCase()]) {
    return `units ${JSON.stringify(d.units)} is not a unit this page knows`;
  }
  if (d.note !== undefined && typeof d.note !== 'string') return 'note is not a string';
  if (d.height_to_ridge !== undefined && !positive(d.height_to_ridge)) {
    return 'height_to_ridge is not a positive number';
  }
  let footprints = 0;
  for (const [key, v] of Object.entries(d)) {
    if (DIMENSION_FIELDS.has(key)) continue;
    if (!isObject(v)) return `${key} is neither a footprint nor units, note or height_to_ridge`;
    if (!positive(v.width) || !positive(v.depth)) return `${key} needs a positive width and depth`;
    if (v.note !== undefined && typeof v.note !== 'string') return `${key}.note is not a string`;
    footprints += 1;
  }
  return footprints ? null : 'no footprint';
}

// The option list both rail blocks share: non-empty, unique ids, labels, at
// most one default. `each` checks what an option of that block carries.
function optionsProblem(options, at, each) {
  if (!Array.isArray(options) || !options.length) return `${at}.options is not a non-empty list`;
  const ids = new Set();
  let defaults = 0;
  for (const [j, o] of options.entries()) {
    const oat = `${at}.options[${j}]`;
    if (!isObject(o)) return `${oat} is not an object`;
    if (!text(o.id)) return `${oat}.id is not a non-empty string`;
    if (ids.has(o.id)) return `${oat}.id repeats an earlier id`;
    ids.add(o.id);
    if (!text(o.label)) return `${oat}.label is not a non-empty string`;
    if (o.default !== undefined && typeof o.default !== 'boolean') return `${oat}.default is not true or false`;
    if (o.default === true) defaults += 1;
    const problem = each(o, oat);
    if (problem) return problem;
  }
  return defaults > 1 ? `${at} has more than one default option` : null;
}

function groupsProblem(groups, block, property, each, extra) {
  if (!Array.isArray(groups)) return 'not a list';
  const ids = new Set();
  for (const [i, g] of groups.entries()) {
    const at = `${block}[${i}]`;
    if (!isObject(g)) return `${at} is not an object`;
    if (!text(g.id)) return `${at}.id is not a non-empty string`;
    if (ids.has(g.id)) return `${at}.id repeats an earlier id`;
    ids.add(g.id);
    if (!text(g.label)) return `${at}.label is not a non-empty string`;
    if (g.property !== property) return `${at}.property is not ${property}, the only one this page applies`;
    const problem = extra(g, at) ?? optionsProblem(g.options, at, each);
    if (problem) return problem;
  }
  return null;
}

// COLOURS ARE LINEAR, as glTF requires of baseColorFactor. Three or four
// numbers from 0 to 1; an alpha other than 1 would need transparency this
// page does not set up, so it is refused rather than dropped.
function colourProblem(o, at) {
  const v = o.value;
  if (!Array.isArray(v) || (v.length !== 3 && v.length !== 4)
      || !v.every((n) => typeof n === 'number' && n >= 0 && n <= 1)) {
    return `${at}.value is not three or four numbers from 0 to 1`;
  }
  return v.length === 4 && v[3] !== 1 ? `${at}.value has an alpha other than 1, which this page does not render` : null;
}

function readSets(manifest, problems) {
  const sets = manifest?.sets;
  if (sets == null) return [];
  const problem = groupsProblem(sets, 'sets', SET_PROPERTY, colourProblem, (g, at) => (
    !Array.isArray(g.targets) || !g.targets.length || !g.targets.every(text)
      ? `${at}.targets is not a non-empty list of names` : null));
  if (problem) {
    refuse(problems, 'sets', problem);
    return [];
  }
  return sets.map((s) => ({
    id: s.id,
    label: s.label,
    targets: s.targets,
    options: s.options.map((o) => ({ id: o.id, label: o.label, isDefault: o.default === true, rgb: o.value.slice(0, 3) })),
  }));
}

// PRESENCE FAILS CLOSED. The model ships every arrangement at once, so a
// refused presence block must not leave them all on screen through each
// other. Every node the block names -- as far as it can be read -- is hidden,
// and no layout control renders: the building shows unfurnished, which is
// plain rather than broken.
function readPresence(manifest, problems) {
  const presence = manifest?.presence;
  if (presence == null) return { groups: [], failClosed: [] };
  const problem = groupsProblem(presence, 'presence', PRESENCE_PROPERTY, (o, at) => (
    !Array.isArray(o.show) || !o.show.every((n) => typeof n === 'string')
      ? `${at}.show is not a list of strings` : null
  ), (g, at) => (g.room !== undefined && typeof g.room !== 'string' ? `${at}.room is not a string` : null));
  if (problem) {
    refuse(problems, 'presence', problem);
    const named = [];
    for (const g of Array.isArray(presence) ? presence : []) {
      for (const o of Array.isArray(g?.options) ? g.options : []) {
        for (const n of Array.isArray(o?.show) ? o.show : []) if (typeof n === 'string') named.push(n);
      }
    }
    return { groups: [], failClosed: named };
  }
  return {
    groups: presence.map((g) => ({
      id: g.id,
      label: g.label,
      options: g.options.map((o) => ({ id: o.id, label: o.label, isDefault: o.default === true, show: o.show })),
    })),
    failClosed: [],
  };
}

function readDisclosure(manifest, problems) {
  const d = manifest?.disclosure;
  if (d == null) {
    if (Array.isArray(manifest?.presence) && manifest.presence.length) {
      refuse(problems, 'disclosure', 'the manifest shows furniture and carries no disclosure');
    }
    return '';
  }
  if (!text(d)) {
    refuse(problems, 'disclosure', 'not a non-empty string');
    return '';
  }
  if (d.length > DISCLOSURE_MAX_CHARS) {
    refuse(problems, 'disclosure', `${d.length} characters is notes, not copy (at most ${DISCLOSURE_MAX_CHARS})`);
    return '';
  }
  return d;
}

// ── the viewer ────────────────────────────────────────────────────────────

function createViewer(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.shadowMap.enabled = true;
  container.append(renderer.domElement);

  // Dimension labels are HTML, laid over the canvas, so they stay crisp and
  // readable at any zoom.
  const labels = new CSS2DRenderer();
  labels.domElement.className = 'labels';
  container.append(labels.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf2f0eb);

  // THE FILE SHIPS NO LIGHTS AND NO CAMERA (no KHR_lights_punctual, cameras 0).
  // Image-based light from a generated studio room gives the soft look with
  // no download. Transmission (KHR_materials_transmission) needs nothing
  // here: three.js allocates its transmission pass when a material asks.
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();

  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.maxPolarAngle = THREE.MathUtils.degToRad(88); // stay above the ground

  // One light, for the ground shadow only; the environment does the lighting.
  const sun = new THREE.DirectionalLight(0xffffff, 1.2);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  scene.add(sun, sun.target);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.ShadowMaterial({ opacity: 0.18 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  ground.visible = false;
  scene.add(ground);

  const loader = new GLTFLoader();
  loader.setDRACOLoader(new DRACOLoader().setDecoderPath(DRACO_DECODERS));

  const sanitize = (name) => THREE.PropertyBinding.sanitizeNodeName(name);

  let current = null;
  let fitted = null; // the box and centre of the first level shown
  let info = null;
  let hidden = new Set(); // nodes the current view mode hides
  let controlled = new Set(); // nodes any layout option names
  let shown = new Set(); // of those, the ones the chosen layouts show
  let visibility = { found: 0, missing: [] };
  let presenceState = { controlled: 0, found: 0, missing: [] };
  const tints = new Map(); // material name → linear RGB, from the chosen finishes
  let tintState = { found: 0, missing: [] };
  let overlay = null;
  let overlayInfo = null;

  // KEEP THE BUILDING IN FRAME WHEN THE PANE CHANGES SHAPE, without undoing
  // the buyer's orbit or zoom. The camera keeps its direction and its target,
  // and its distance keeps the same ratio to a full fit; only the fit is
  // recomputed for the new aspect. Narrowing the pane backs the camera off
  // rather than cropping the building.
  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (!w || !h) return;
    const before = fitted && fitDistance(fitted.box, fitted.center, viewDirection(), camera.aspect);
    renderer.setSize(w, h, false);
    labels.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    if (before) {
      const scale = fitDistance(fitted.box, fitted.center, viewDirection(), camera.aspect) / before;
      // The offset is read BEFORE the position is written. Chaining
      // position.copy(target).add(position - target) evaluates the argument
      // after the copy, sees a zero offset, and drops the camera onto its
      // target -- which OrbitControls then pushes to minDistance, straight down.
      const offset = camera.position.clone().sub(controls.target).multiplyScalar(scale);
      controls.maxDistance *= scale;
      camera.position.copy(controls.target).add(offset);
      controls.update();
    }
  }
  resize();
  new ResizeObserver(resize).observe(container);

  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
    labels.render(scene, camera);
  });

  function viewDirection() {
    return camera.position.clone().sub(controls.target).normalize();
  }

  // FRAMING COMES FROM THE LOADED MODEL'S OWN BOX, never from numbers. A
  // camera distance tuned to one building frames the next one wrong.
  //
  // FIT THE CORNERS, NOT A SPHERE. A bounding sphere is as wide as the box's
  // diagonal in every direction, so a long, low building ends up small in
  // the frame. Instead each of the box's eight corners is put in camera space
  // for the given view, and the distance is the least at which all of them
  // are inside both the horizontal and the vertical field of view.
  function fitDistance(box, center, direction, aspect) {
    const tanV = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    const tanH = tanV * aspect;
    const forward = direction.clone().negate();
    const right = new THREE.Vector3().crossVectors(forward, THREE.Object3D.DEFAULT_UP);
    if (right.lengthSq() < 1e-8) right.set(1, 0, 0); // looking straight down
    right.normalize();
    const up = new THREE.Vector3().crossVectors(right, forward);
    let distance = 0;
    for (const x of [box.min.x, box.max.x]) {
      for (const y of [box.min.y, box.max.y]) {
        for (const z of [box.min.z, box.max.z]) {
          const o = new THREE.Vector3(x, y, z).sub(center);
          const towardCamera = o.dot(direction);
          distance = Math.max(distance,
            Math.abs(o.dot(right)) / tanH + towardCamera,
            Math.abs(o.dot(up)) / tanV + towardCamera);
        }
      }
    }
    return distance * 1.08; // a margin, so the building does not touch the edge
  }

  function frame(box) {
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    const r = sphere.radius;
    const distance = fitDistance(box, sphere.center, VIEW_DIRECTION, camera.aspect);
    fitted = { box: box.clone(), center: sphere.center.clone() };

    camera.position.copy(sphere.center).addScaledVector(VIEW_DIRECTION, distance);
    camera.near = distance / 100;
    camera.far = distance * 20;
    camera.updateProjectionMatrix();
    controls.target.copy(sphere.center);
    controls.minDistance = r * 0.25;
    controls.maxDistance = distance * 4;
    controls.update();

    // THE GROUND IS THE FLOOR OF THE FRAMED BOX. That box is the COARSEST
    // level's, because it is shown first: a building on footings can reach
    // lower in full detail than its massing does, and the ground stays where
    // the massing put it rather than dropping when detail arrives.
    const floor = box.min.y;
    ground.position.set(sphere.center.x, floor - r * 1e-3, sphere.center.z);
    ground.scale.setScalar(r * 12);
    ground.visible = true;

    // From above and in front, on the camera's side, so the shadow falls
    // behind the building rather than across the view of its front.
    sun.target.position.set(sphere.center.x, floor, sphere.center.z);
    sun.position.copy(sphere.center).add(new THREE.Vector3(r * 0.8, r * 2, r * 1.2));
    const s = sun.shadow.camera;
    s.left = s.bottom = -r * 1.5;
    s.right = s.top = r * 1.5;
    s.near = r * 0.1;
    s.far = r * 6;
    s.updateProjectionMatrix();

    return {
      floor,
      radius: r,
      distance,
      center: sphere.center.toArray(),
      size: box.getSize(new THREE.Vector3()).toArray(),
    };
  }

  // VISIBILITY HAS TWO SOURCES, AND BOTH MUST AGREE TO SHOW A NODE. The view
  // mode hides nodes by exact name (never by prefix); the layouts hide every
  // node any layout names except the ones the chosen layouts show. A node is
  // visible only if the view mode does not hide it AND, when a layout names
  // it, a chosen layout shows it. Names go through the same sanitisation
  // GLTFLoader applies. A level that lacks a named node -- massing has no
  // ceilings and no furniture -- simply has nothing to hide there.
  function applyVisibility() {
    if (!current) return;
    const seenHidden = new Set();
    const seenControlled = new Set();
    current.traverse((o) => {
      if (o === current) return;
      const name = o.name;
      if (hidden.has(name)) seenHidden.add(name);
      if (controlled.has(name)) seenControlled.add(name);
      o.visible = !hidden.has(name) && (!controlled.has(name) || shown.has(name));
    });
    visibility = { found: seenHidden.size, missing: [...hidden].filter((n) => !seenHidden.has(n)) };
    presenceState = {
      controlled: controlled.size,
      found: seenControlled.size,
      missing: [...controlled].filter((n) => !seenControlled.has(n)),
    };
  }

  // FINISHES WRITE A LINEAR COLOUR, NEVER A MAP. glTF's baseColorFactor is
  // linear and three.js keeps material.color in its linear working space, so
  // the manifest's numbers go in through setRGB(..., LinearSRGBColorSpace).
  // color.set('#rrggbb') would decode them as sRGB a second time and wash every
  // finish out. Matched by material name; one name can be several material
  // objects, since the loader clones a material a mesh needs to vary.
  function applyTints() {
    if (!current) return;
    const seen = new Set();
    current.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of [].concat(o.material)) {
        const rgb = m && tints.get(m.name);
        if (!rgb) continue;
        m.color.setRGB(rgb[0], rgb[1], rgb[2], THREE.LinearSRGBColorSpace);
        seen.add(m.name);
      }
    });
    tintState = { found: seen.size, missing: [...tints.keys()].filter((n) => !seen.has(n)) };
  }

  // THE DIMENSION OVERLAY. The manifest gives each footprint's width and
  // depth, not where it sits, so the drawn footprint is centred on the
  // building's plan box. That is exact when the footprint is symmetric within
  // the box -- a slab with even eaves around it -- and wrong for one pushed to
  // an end by an appendage, which is why the overlay draws only the first
  // footprint and lists the rest rather than placing them all (#119).
  function buildOverlay(dims) {
    const fp = dims.footprints[0];
    const w = fp.width * dims.unit.metres;
    const d = fp.depth * dims.unit.metres;
    const c = fitted.box.getCenter(new THREE.Vector3());
    const y = info.floor + fitted.box.getSize(new THREE.Vector3()).y * 0.004;
    const x0 = c.x - w / 2;
    const x1 = c.x + w / 2;
    const z0 = c.z - d / 2;
    const z1 = c.z + d / 2;
    const gap = Math.max(w, d) * 0.08; // dimension lines stand off the footprint
    const tick = gap * 0.35;

    const segments = [
      // the footprint itself
      [x0, z0, x1, z0], [x1, z0, x1, z1], [x1, z1, x0, z1], [x0, z1, x0, z0],
      // width, along the front edge, with end ticks
      [x0, z1 + gap, x1, z1 + gap],
      [x0, z1 + gap - tick, x0, z1 + gap + tick], [x1, z1 + gap - tick, x1, z1 + gap + tick],
      // depth, along the +X side, with end ticks
      [x1 + gap, z0, x1 + gap, z1],
      [x1 + gap - tick, z0, x1 + gap + tick, z0], [x1 + gap - tick, z1, x1 + gap + tick, z1],
    ];
    const positions = segments.flatMap(([ax, az, bx, bz]) => [ax, y, az, bx, y, bz]);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    // Drawn over the building, so the whole footprint reads even where walls
    // stand on it.
    const lines = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({
      color: 0x23211d, depthTest: false, transparent: true, opacity: 0.9,
    }));
    lines.renderOrder = 10;

    const group = new THREE.Group();
    group.add(lines);
    const label = (content, x, z) => {
      const el = document.createElement('div');
      el.className = 'dimension-label';
      el.textContent = content;
      const obj = new CSS2DObject(el);
      obj.position.set(x, y, z);
      group.add(obj);
    };
    label(`${formatLength(fp.width)} ${dims.unit.label}`, c.x, z1 + gap);
    label(`${formatLength(fp.depth)} ${dims.unit.label}`, x1 + gap, c.z);

    overlayInfo = {
      footprint: fp.key,
      width: w,
      depth: d,
      centre: [c.x, c.z],
      x: [x0, x1],
      z: [z0, z1],
      y,
    };
    return group;
  }

  function removeOverlay() {
    if (!overlay) return;
    scene.remove(overlay);
    // Removing a group does not tell its children, so their label elements
    // would stay in the page: remove them explicitly.
    overlay.traverse((o) => {
      if (o.isCSS2DObject) o.element.remove();
      o.geometry?.dispose();
      o.material?.dispose();
    });
    overlay = null;
    overlayInfo = null;
  }

  const api = {
    load: (url) => loader.loadAsync(url.href),
    show(root) {
      root.traverse((o) => {
        if (o.isMesh) {
          o.castShadow = true;
          o.receiveShadow = true;
        }
      });
      scene.add(root);
      if (current) {
        scene.remove(current);
        dispose(current);
      }
      current = root;
      // Every choice survives a level swap: the new level's materials and
      // nodes are new objects, so the chosen finishes, layouts and view mode
      // are applied to them again.
      applyTints();
      applyVisibility();
      const box = new THREE.Box3().setFromObject(root);
      if (!fitted) {
        info = frame(box);
      } else if (!fitted.box.containsBox(box)) {
        // FULL DETAIL CAN REACH PAST ITS MASSING -- a footing below the
        // stemwall is the case in hand. Grow the fitted box to cover both, and
        // back the camera off only if the building no longer fits, so a buyer
        // who is already orbiting keeps their view. The ground stays at the
        // floor frame() set: it should not drop when detail lands.
        fitted.box.union(box);
        if (!api.fits()) {
          const dir = viewDirection(); // read before the position is written
          const needed = fitDistance(fitted.box, controls.target, dir, camera.aspect);
          controls.maxDistance = Math.max(controls.maxDistance, needed * 4);
          camera.position.copy(controls.target).addScaledVector(dir, needed);
          controls.update();
        }
        info = { ...info, size: fitted.box.getSize(new THREE.Vector3()).toArray() };
      }
      return info;
    },
    setHidden(names) {
      hidden = new Set(names.map(sanitize));
      applyVisibility();
      return visibility;
    },
    setPresence(controlledNames, shownNames) {
      controlled = new Set(controlledNames.map(sanitize));
      shown = new Set(shownNames.map(sanitize));
      applyVisibility();
      return presenceState;
    },
    setTint(targets, rgb) {
      for (const name of targets) tints.set(name, rgb);
      applyTints();
      return tintState;
    },
    setDimensions(dims) {
      removeOverlay();
      if (dims && fitted) {
        overlay = buildOverlay(dims);
        scene.add(overlay);
      }
      return overlayInfo;
    },
    // For tests: which of the current mode's nodes this level has.
    visibility: () => ({ hidden: [...hidden], ...visibility }),
    // For tests: which layout-controlled nodes this level has, and which show.
    presence: () => ({ ...presenceState, shown: [...shown] }),
    // For tests: which tinted material names this level has.
    tints: () => ({ tinted: [...tints.keys()], ...tintState }),
    // For tests: is the named node rendered -- visible, and every ancestor
    // visible? null when this level has no such node.
    isVisible(name) {
      const node = current?.getObjectByName(sanitize(name));
      if (!node) return null;
      for (let o = node; o && o !== current; o = o.parent) if (!o.visible) return false;
      return true;
    },
    // For tests: a material's colour as the building has it -- sRGB hex, and
    // the linear numbers the manifest wrote.
    material(name) {
      let hit = null;
      current?.traverse((o) => {
        if (hit || !o.isMesh) return;
        hit = [].concat(o.material).find((m) => m?.name === name) ?? null;
      });
      return hit && { name, hex: `#${hit.color.getHexString()}`, linear: [hit.color.r, hit.color.g, hit.color.b] };
    },
    // For tests: what the dimension overlay is drawing, or null.
    overlay: () => overlayInfo && {
      ...overlayInfo,
      labels: [...container.querySelectorAll('.dimension-label')].map((el) => el.textContent),
    },
    // For tests: where the camera is, relative to what it orbits.
    pose() {
      return {
        position: camera.position.toArray(),
        target: controls.target.toArray(),
        aspect: camera.aspect,
        distance: camera.position.distanceTo(controls.target),
        pane: [container.clientWidth, container.clientHeight],
      };
    },
    // For tests: is every corner of the framed box on screen right now?
    fits() {
      if (!fitted) return false;
      camera.updateMatrixWorld();
      const { min, max } = fitted.box;
      const p = new THREE.Vector3();
      for (const x of [min.x, max.x]) {
        for (const y of [min.y, max.y]) {
          for (const z of [min.z, max.z]) {
            p.set(x, y, z).project(camera);
            if (Math.abs(p.x) > 1 || Math.abs(p.y) > 1) return false;
          }
        }
      }
      return true;
    },
  };
  return api;
}

function dispose(root) {
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.dispose();
    for (const m of [].concat(o.material)) {
      for (const v of Object.values(m)) if (v?.isTexture) v.dispose();
      m.dispose();
    }
  });
}

// ── the page around the viewer ────────────────────────────────────────────

// THE CONTROLS ARE WHATEVER THE MANIFEST OFFERS: its modes, in its order,
// with its labels. Nothing here counts them. A block that is absent, or a
// single mode that offers no choice, renders no control at all.
function renderControls(views, dimensions, viewer) {
  let any = false;

  if (views.length) {
    const group = $('view-modes');
    let buttons = [];
    const select = (view) => {
      for (const [v, b] of buttons) b.setAttribute('aria-pressed', String(v === view));
      viewer.setHidden(view.hide);
      window.__viewer = { ...window.__viewer, view: view.id };
    };
    // ONE MODE IS NOT A CHOICE, but it is still how the manifest says the
    // model should be seen: apply it, and render no buttons.
    if (views.length >= 2) {
      buttons = views.map((view) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = view.label;
        if (view.desc) b.title = view.desc;
        b.addEventListener('click', () => select(view));
        group.append(b);
        return [view, b];
      });
      group.hidden = false;
      any = true;
    }
    select(views.find((v) => v.isDefault) ?? views[0]);
  }

  if (dimensions) {
    const toggle = $('dimensions-toggle');
    const legend = $('dimensions-legend');
    renderLegend(legend, dimensions);
    toggle.addEventListener('click', () => {
      const on = toggle.getAttribute('aria-pressed') !== 'true';
      toggle.setAttribute('aria-pressed', String(on));
      toggle.textContent = on ? 'Hide dimensions' : 'Show dimensions';
      legend.hidden = !on;
      viewer.setDimensions(on ? dimensions : null);
      window.__viewer = { ...window.__viewer, dimensionsShown: on };
    });
    toggle.hidden = false;
    any = true;
  }

  $('controls').hidden = !any;
}

// THE RAIL IS WHATEVER THE MANIFEST OFFERS: every finish group and every
// layout group, in its order, with its labels. Nothing here knows how many
// there are or what they are called, so a model with no covered entry simply
// brings one group fewer. Each group starts on its default option (or its
// first) and APPLIES it -- for layouts that is not optional, because the model
// ships every arrangement at once.
function renderRail(sets, presence, disclosure, viewer) {
  const rail = $('rail');
  const choices = { sets: {}, presence: {} };
  const publish = () => {
    window.__viewer = { ...window.__viewer, choices: structuredClone(choices) };
  };

  if (sets.length) {
    const section = railSection(rail, 'Finishes');
    sets.forEach((set, i) => {
      choiceGroup(section, set, `set-${i}`, true, (option) => {
        viewer.setTint(set.targets, option.rgb);
        choices.sets[set.id] = option.id;
        publish();
      });
    });
  }

  if (presence.length) {
    const section = railSection(rail, 'Layout');
    const controlled = presence.flatMap((g) => g.options.flatMap((o) => o.show));
    const chosen = new Map();
    presence.forEach((group, i) => {
      choiceGroup(section, group, `presence-${i}`, false, (option) => {
        chosen.set(group, option);
        viewer.setPresence(controlled, [...chosen.values()].flatMap((o) => o.show));
        choices.presence[group.id] = option.id;
        publish();
      });
    });
  }

  // REQUIRED COPY, ON SCREEN. The model cannot enforce what the disclosure
  // says, so the page shows it as text in the rail -- pinned to the rail's
  // foot so it stays in view while the options scroll -- never as a tooltip.
  if (disclosure) {
    const p = document.createElement('p');
    p.className = 'disclosure';
    p.textContent = disclosure;
    rail.append(p);
  }

  rail.hidden = !(sets.length || presence.length || disclosure);
  publish();
}

function railSection(rail, title) {
  const section = document.createElement('section');
  section.className = 'rail-section';
  const h2 = document.createElement('h2');
  h2.textContent = title;
  section.append(h2);
  rail.append(section);
  return section;
}

// One radio group per manifest group: native inputs, so the keyboard and
// assistive technology get a real choice. Finishes show a swatch chip.
function choiceGroup(parent, group, name, swatches, onSelect) {
  const fieldset = document.createElement('fieldset');
  fieldset.className = swatches ? 'swatches' : 'layouts';
  const legend = document.createElement('legend');
  const title = document.createElement('span');
  title.textContent = group.label;
  const current = document.createElement('span');
  current.className = 'current';
  legend.append(title, current);
  fieldset.append(legend);

  const select = (option) => {
    current.textContent = option.label;
    onSelect(option);
  };
  const initial = group.options.find((o) => o.isDefault) ?? group.options[0];

  group.options.forEach((option, j) => {
    const label = document.createElement('label');
    label.className = 'choice';
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = name;
    input.value = String(j);
    input.checked = option === initial;
    input.addEventListener('change', () => {
      if (input.checked) select(option);
    });
    label.append(input);
    if (swatches) {
      const chip = document.createElement('span');
      chip.className = 'swatch';
      chip.style.backgroundColor = swatchColour(option.rgb);
      label.append(chip);
    }
    const caption = document.createElement('span');
    caption.className = 'choice-label';
    caption.textContent = option.label;
    label.append(caption);
    fieldset.append(label);
  });

  parent.append(fieldset);
  select(initial);
}

// A SWATCH IS THE sRGB ENCODING OF THE SAME COLOUR the building is given, not
// the manifest's numbers. Those are linear; CSS is sRGB. Painting the linear
// numbers into a chip makes every dark finish look lighter than the building,
// which reads as a fault in the model. getHexString() encodes from three.js's
// linear working space to sRGB -- the same encoding material.color reports.
function swatchColour(rgb) {
  return `#${new THREE.Color().setRGB(rgb[0], rgb[1], rgb[2], THREE.LinearSRGBColorSpace).getHexString()}`;
}

// Every footprint, with the manifest's own note on what it measures. The
// first is the one drawn; the rest are listed, never merged into it.
function renderLegend(legend, dims) {
  const describe = (fp) => {
    const size = `${formatLength(fp.width)} × ${formatLength(fp.depth)} ${dims.unit.label}`;
    return `${fp.key.replaceAll('_', ' ')} ${size}${fp.note ? ` — ${fp.note}` : ''}`;
  };
  const line = (heading, content) => {
    const li = document.createElement('li');
    const strong = document.createElement('strong');
    strong.textContent = `${heading} `;
    li.append(strong, content);
    legend.append(li);
  };
  const [drawn, ...others] = dims.footprints;
  line('Drawn:', describe(drawn));
  for (const fp of others) line('Also:', describe(fp));
  if (dims.ridge !== null) line('Ridge:', `${formatLength(dims.ridge)} ${dims.unit.label} above the floor datum`);
}

function formatLength(n) {
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

function renderHeader(identity) {
  const name = identity.name ?? identity.id ?? '';
  $('model-name').textContent = name;
  const facts = [];
  if (Number.isFinite(identity.area_sf)) {
    facts.push(`${identity.area_sf.toLocaleString()} sq ft`);
  }
  const count = identity.storeys?.count;
  if (Number.isInteger(count)) {
    facts.push(`${count} ${count === 1 ? 'storey' : 'storeys'}${identity.storeys.loft ? ' + loft' : ''}`);
  }
  $('model-facts').textContent = facts.join(' · ');
  if (name) document.title = `${name} — ADU configurator`;
}

function renderPicker(rows, chosen, params) {
  const picker = $('model-picker');
  if (rows.length < 2) return;
  for (const r of rows) {
    picker.append(new Option(r.name ?? r.id, r.id, false, r.id === chosen.id));
  }
  picker.hidden = false;
  picker.addEventListener('change', () => {
    params.set('model', picker.value);
    location.search = params.toString();
  });
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url.pathname} returned ${res.status}`);
  return res.json();
}
