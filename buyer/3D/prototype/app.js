// app.js — the viewer shell (#107).
//
// THE PAGE KNOWS NOTHING ABOUT ANY BUILDING. It reads an index, picks a row,
// reads that row's manifest for the header, and loads the row's .glb levels.
// No model id, display name, room, node or material appears in this file, and
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
// quarter angle above it. No manifest declares a front yet; until one does,
// this is an export convention the page assumes, and the only one.
const VIEW_DIRECTION = new THREE.Vector3(0.7, 0.45, 1).normalize();

const LEVEL = /^lod(\d+)$/;

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
      state: last ? 'ready' : 'loading',
      model: row.id,
      level: level.name,
      levels: levels.map((l) => l.name),
      ...framed,
      fits: viewer.fits,
      pose: viewer.pose,
    };
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

function createViewer(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.shadowMap.enabled = true;
  container.append(renderer.domElement);

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

  let current = null;
  let fitted = null; // the box and centre of the first level shown
  let info = null;

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
