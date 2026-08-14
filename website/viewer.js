// Self-contained three.js viewer for build123d models — the ONE viewer shared by
// the deployed site (website/index.html, three loaded from CDN via its import
// map) and the single-file agent artifact (uv run view <model>, three embedded).
// The import specifiers below must resolve in both; each page supplies its own
// import map. Keep this module the single source of truth for how a model is
// shown on screen: the site and the artifact must never drift apart.
//
// Z-up millimetre scene, with build123d's print-bed (XY) plane as the ground
// grid. Renders a colour-carrying GLB when available, else a colourless STL.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/**
 * Create a viewer drawing into `canvas`, sized by the positioned `container`
 * (the element whose size tracks the model viewport). Render failures report
 * through `onStatus(text, isErr)` and `onLog(message)` — a page that wants a
 * status overlay or a log hands them its own functions.
 *
 * @param {{ container: HTMLElement, canvas: HTMLCanvasElement,
 *           onStatus?: (text: string, isErr?: boolean) => void,
 *           onLog?: (message: string) => void }} opts
 * @returns {{ showStl: (bytes: Uint8Array, reframe: boolean) => void,
 *             showGlb: (bytes: Uint8Array, reframe: boolean) => void,
 *             triCount: (bytes: Uint8Array) => number,
 *             setGrid: (on: boolean) => void }}
 */
export function createViewer({ container, canvas, onStatus = () => {}, onLog = console.warn }) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  // Clamp to 2: phones report devicePixelRatio 3+, which is 9x the fragments for
  // no visible gain and enough GPU load to make the device throttle.
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1e24);
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 20000);
  camera.up.set(0, 0, 1);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = 0.12;
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 0.9); key.position.set(120, 80, 200); scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.35); fill.position.set(-90, -130, 90); scene.add(fill);

  // ---------------------------------------------------------------------------
  // Ground grid on XY (build123d's print bed plane).
  // A GridHelper is a fixed-size lattice: at 400 mm it sits as a small patch in
  // the middle of the viewport for a 1500 mm profile, and vanishes entirely once
  // you zoom inside it. This is a plane that follows the camera, with its lines
  // drawn in the fragment shader from world coordinates — so it fills the view at
  // every zoom, and its cell size steps by decades with the camera distance
  // (0.1 -> 1 -> 10 -> 100 mm) instead of collapsing into moiré.
  // ---------------------------------------------------------------------------
  const gridUniforms = {
    uCell:  { value: 10 },                            // minor cell size, mm
    uFine:  { value: 1 },                             // minor lattice opacity, faded out before it changes decade
    uCam:   { value: new THREE.Vector3() },
    uFade:  { value: 1000 },                          // distance at which the grid is fully gone
    uMinor: { value: new THREE.Color(0x2a2f37) },
    uMajor: { value: new THREE.Color(0x3a4048) },
    uAxisX: { value: new THREE.Color(0x7a4149) },
    uAxisY: { value: new THREE.Color(0x3f6b48) },
  };
  const grid = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.ShaderMaterial({
      uniforms: gridUniforms,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      // Bias the grid away from the eye so a part resting on z=0 wins the depth
      // test against the coplanar bed instead of z-fighting with it.
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
      vertexShader: `
        varying vec3 vWorld;
        void main() {
          vec4 w = modelMatrix * vec4(position, 1.0);
          vWorld = w.xyz;
          gl_Position = projectionMatrix * viewMatrix * w;
        }
      `,
      fragmentShader: `
        precision highp float;
        uniform float uCell, uFine, uFade;
        uniform vec3 uCam, uMinor, uMajor, uAxisX, uAxisY;
        varying vec3 vWorld;

        // Coverage of the nearest line of a cell-spaced lattice, antialiased with
        // the screen-space derivative so lines stay ~1px wide at any zoom.
        float lattice(vec2 p, float cell) {
          vec2 c = p / cell;
          vec2 w = max(fwidth(c), 1e-8);        // cells crossed per pixel
          vec2 g = abs(fract(c - 0.5) - 0.5) / w;
          float line = 1.0 - min(min(g.x, g.y), 1.0);
          // Once a cell is only a few pixels wide the lattice is at its sampling
          // limit: every pixel lands on a line, so the lines stop reading as lines
          // and turn into a flat wash. Fade it out there instead — this is what
          // keeps the far field, where perspective packs decades of cells into a
          // few pixels near the horizon, from hazing over.
          // The ramp is deliberately wide — it spans ~30x in cell density, which
          // in a shallow view is a large stretch of floor. A tight ramp puts the
          // whole fade in a few pixels, and a lattice that ends on a line reads as
          // the grid changing size at that line rather than receding.
          return line * (1.0 - smoothstep(0.02, 0.6, max(w.x, w.y)));
        }

        void main() {
          vec2 p = vWorld.xy;
          float minor = lattice(p, uCell) * uFine;
          float major = lattice(p, uCell * 10.0);
          vec3 col = mix(uMinor, uMajor, major);
          float a = max(minor * 0.7, major);

          // The two world axes, drawn over the lattice they line up with.
          vec2 d = max(fwidth(p), 1e-8);
          float ax = 1.0 - min(abs(p.y) / d.y, 1.0);   // X axis runs along y = 0
          float ay = 1.0 - min(abs(p.x) / d.x, 1.0);
          col = mix(col, uAxisX, ax);
          col = mix(col, uAxisY, ay);
          a = max(a, max(ax, ay));

          a *= 1.0 - smoothstep(uFade * 0.25, uFade, length(vWorld - uCam));
          if (a < 0.004) discard;                      // keep the far field out of the depth/blend work
          gl_FragColor = vec4(col, a);
        }
      `,
    }),
  );
  grid.frustumCulled = false;   // the plane is re-centred every frame; its (unit) bounds lie
  grid.renderOrder = -1;        // about the camera, so culling it on them is meaningless
  scene.add(grid);

  // Re-centre and re-scale the grid for the current camera distance. Called every
  // frame, before the render.
  function updateGrid() {
    if (!grid.visible) return;
    const dist = Math.max(camera.position.distanceTo(controls.target), 1e-3);
    // Minor cells are the power of ten nearest 1/20th of the visible span, so the
    // lattice reads in round millimetres. Between two decades the count per screen
    // climbs 10x, which is what the cross-fade is for: the fine lattice is gone by
    // the time it would be dense enough to alias, and the coarse one it was drawn
    // over has become the new fine one.
    const decade = Math.log10(dist) - 1.3;
    const step = Math.floor(decade);
    gridUniforms.uCell.value = Math.pow(10, step);
    gridUniforms.uFine.value = Math.pow(1 - (decade - step), 1.5);
    // Stop short of the far plane: camera.far is set when a model is framed and
    // does not follow a later zoom-out, so an unclamped fade would end in a hard
    // circular clip rather than in nothing.
    gridUniforms.uFade.value = Math.min(dist * 6, camera.far * 0.8);
    gridUniforms.uCam.value.copy(camera.position);
    grid.position.set(camera.position.x, camera.position.y, 0);
    grid.scale.setScalar(dist * 20);
  }
  // Below this dihedral, two neighbouring triangles are shaded as one smooth
  // surface; above it the edge between them stays hard.
  //
  // It exists because a B-rep shell is not one surface, and neither the STL nor
  // the glTF hides that: STL carries no shared vertices at all, and glTF's normals
  // stop at every face boundary. A shell lofted from a stack of sections is *made*
  // of face boundaries -- `spiral_vase_lampshade` is 82 ruled patches, 2.24 mm
  // apart, meeting at 7 to 17 degrees -- so shading each patch on its own turned a
  // construction artefact 0.11 mm deep (half a print layer, invisible on the part)
  // into the fine horizontal banding that was the model's most obvious feature on
  // screen.
  //
  // 30 degrees clears that band by nearly a factor of two while leaving every edge
  // somebody actually designed alone: a 45 degree chamfer breaks 45 degrees, a rim
  // or a wall corner 90. So this smooths joins that are not features, and only
  // those.
  const CREASE_ANGLE = THREE.MathUtils.degToRad(30);
  const CREASE_DOT = Math.cos(CREASE_ANGLE);

  // Share normals between triangles that meet at a point and disagree by less
  // than CREASE_ANGLE — the ones that are the same surface seen twice.
  //
  // Takes a *list* of geometries and welds across all of them at once, which is
  // the whole trick: build123d's glTF writes one mesh per B-rep face (this shade
  // arrives as 168 of them), so the two sides of a loft seam are never in the same
  // buffer and welding each geometry on its own changes nothing at all.
  //
  // It averages the normals the meshes already carry rather than recomputing them
  // from the triangles. A glTF out of OpenCASCADE carries the *surface* normal at
  // every vertex, exact to the B-rep; rebuilding those from an irregular
  // triangulation (what BufferGeometryUtils.toCreasedNormals does) trades the
  // banding for a mottling that is just as visible. Only the seams need touching,
  // so only the seams are touched. Geometry with no normals of its own — an STL is
  // a bag of unshared triangles — gets facet normals computed first.
  function smoothNormals(geometries) {
    for (const g of geometries) if (!g.attributes.normal) g.computeVertexNormals();
    // 1e-4 buckets in the mesh's own units: far below any feature, far above the
    // float noise between two copies of one vertex. Hashed to a string because a
    // Map keyed on three numbers would cost an object per vertex.
    const at = new Map();
    geometries.forEach((geom, gi) => {
      const pos = geom.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        const k = `${Math.round(pos.getX(i) * 1e4)},${Math.round(pos.getY(i) * 1e4)},${Math.round(pos.getZ(i) * 1e4)}`;
        const g = at.get(k);
        if (g) g.push(gi, i); else at.set(k, [gi, i]);
      }
    });
    const out = geometries.map((g) => new Float32Array(g.attributes.normal.count * 3));
    const mine = new THREE.Vector3(), other = new THREE.Vector3(), sum = new THREE.Vector3();
    for (const group of at.values()) {
      for (let a = 0; a < group.length; a += 2) {
        mine.fromBufferAttribute(geometries[group[a]].attributes.normal, group[a + 1]);
        sum.set(0, 0, 0);
        for (let b = 0; b < group.length; b += 2) {
          other.fromBufferAttribute(geometries[group[b]].attributes.normal, group[b + 1]);
          if (mine.dot(other) >= CREASE_DOT) sum.add(other);   // same surface
        }
        if (sum.lengthSq() > 0) sum.normalize(); else sum.copy(mine);
        const buf = out[group[a]], i = group[a + 1];
        buf[i * 3] = sum.x; buf[i * 3 + 1] = sum.y; buf[i * 3 + 2] = sum.z;
      }
    }
    geometries.forEach((g, i) => g.setAttribute('normal', new THREE.BufferAttribute(out[i], 3)));
    return geometries;
  }
  const material = new THREE.MeshStandardMaterial({ color: 0x59a6ff, metalness: 0.1, roughness: 0.55 });
  const gltfLoader = new GLTFLoader();
  let currentObject = null;   // the currently displayed render object (STL mesh or glTF scene)

  function clearObject() {
    if (!currentObject) return;
    scene.remove(currentObject);
    currentObject.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { if (m !== material) m.dispose(); });
    });
    currentObject = null;
  }
  function frameMesh(obj) {
    obj.updateWorldMatrix(true, true);  // ensure scale/rotation are baked before measuring
    const box = new THREE.Box3().setFromObject(obj);
    if (box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    controls.target.copy(center);
    const dist = Math.max(size.x, size.y, size.z) * 1.7 + 30;
    camera.position.set(center.x + dist * 0.7, center.y - dist, center.z + dist * 0.6);
    camera.near = Math.max(0.1, dist / 500); camera.far = dist * 20; camera.updateProjectionMatrix();
    controls.update();
  }
  function showStl(bytes, reframe) {
    const buf = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const geom = new STLLoader().parse(buf);
    smoothNormals([geom]);
    clearObject();
    currentObject = new THREE.Mesh(geom, material);
    scene.add(currentObject);
    if (reframe) frameMesh(currentObject);
  }
  // Render a GLB (binary glTF). Carries per-part colour + transparency, which STL
  // can't. build123d exports glTF in metres and (via OpenCASCADE) Y-up, so scale
  // ×1000 back to millimetres and rotate +90° about X to bring it into the viewer's
  // Z-up mm scene, matching the STL path and grid.
  function showGlb(bytes, reframe) {
    const buf = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    gltfLoader.parse(buf, '', (gltf) => {
      const root = gltf.scene;
      root.scale.setScalar(1000);
      root.rotation.x = Math.PI / 2;   // glTF Y-up -> scene Z-up
      root.updateWorldMatrix(true, true);
      const byPlacement = new Map();
      root.traverse((o) => {
        if (!o.isMesh) return;
        // Grouped by world placement, because smoothNormals compares raw
        // coordinates: two parts of an assembly sitting at different locations
        // must not be welded to each other just because their local coordinates
        // happen to land in the same bucket. A single part is one group of one
        // placement, which is the case this exists for.
        const key = o.matrixWorld.elements.join(',');
        const g = byPlacement.get(key);
        if (g) g.push(o.geometry); else byPlacement.set(key, [o.geometry]);
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        for (const m of mats) {
          m.metalness = Math.min(m.metalness ?? 0, 0.1);   // OCC exports metalness 1; tame the flat look
          m.roughness = 0.55;
          if (m.transparent && m.opacity < 1) { m.depthWrite = false; m.side = THREE.DoubleSide; }
        }
      });
      // One pass over every mesh that shares a placement, not one pass each: the
      // seams that need shading across run *between* those meshes, and this file
      // has one mesh per B-rep face. See smoothNormals.
      for (const geoms of byPlacement.values()) smoothNormals(geoms);
      clearObject();
      currentObject = root;
      scene.add(root);
      if (reframe) frameMesh(root);
    }, (err) => { onStatus('failed to render colours (see log)', true); onLog('glTF: ' + err); });
  }
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();
  (function loop() { controls.update(); updateGrid(); renderer.render(scene, camera); requestAnimationFrame(loop); })();

  function triCount(bytes) {  // binary STL: uint32 triangle count at byte 80
    return bytes.byteLength >= 84 ? new DataView(bytes.buffer, bytes.byteOffset).getUint32(80, true) : 0;
  }

  return { showStl, showGlb, triCount, setGrid: (on) => { grid.visible = on; }, getGrid: () => grid.visible };
}
