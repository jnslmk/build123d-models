---
name: viewer-frontend
description: >-
  Guides changes to the 3D CAD viewer's JavaScript frontend across the three
  sibling checkouts this project uses - build123d-models (the CAD models),
  vscode-ocp-cad-viewer (Python backend and VS Code extension) and
  three-cad-viewer (the Three.js frontend). Covers which repo a given change
  belongs in, the edit then npm run build then copy-the-bundle then uv run show
  test loop, and the fact that the JS and CSS under vscode-ocp-cad-viewer are
  gitignored build artifacts so frontend commits belong in three-cad-viewer
  instead. Use when modifying the viewer UI, adding or changing a viewer tool,
  rebuilding the viewer bundle, or when a frontend edit does not show up in the
  viewer. Keywords: viewer, three-cad-viewer, frontend, ocp-cad-viewer, bundle,
  npm build, rollup, UI tool, esm.js. Load BEFORE editing
  `ocp_vscode/static/js/three-cad-viewer.esm.js` or
  `ocp_vscode/static/css/three-cad-viewer.css` directly — those two compiled
  files are gitignored build artifacts, not source; the real source is
  `three-cad-viewer/src/`, and an edit belongs there instead. TRIGGER: about to
  add or change a viewer toolbar tool, run `npm run build`, copy a rebuilt
  bundle, or a frontend edit is not appearing in `uv run show`.
---

# Viewer frontend

The viewer this repo shows models in is not built here. It is assembled from three
checkouts that sit side by side under `~/git-projects`:

| Checkout | Role |
| --- | --- |
| `build123d-models/` | This repo — the Python CAD models. Consumes the viewer. |
| `vscode-ocp-cad-viewer/` | Python backend (`ocp_vscode`) plus the VS Code extension. Serves the frontend from `ocp_vscode/static/`. |
| `three-cad-viewer/` | The JavaScript/TypeScript frontend (Three.js). **Where frontend source lives.** |

## The one rule that matters

**`ocp_vscode/static/js/three-cad-viewer.esm.js` and
`ocp_vscode/static/css/three-cad-viewer.css` are gitignored build artifacts**
(`vscode-ocp-cad-viewer/.gitignore` lines 21-22). Copying a fresh bundle in is a
deployment step, not a change.

**Frontend changes get committed in `three-cad-viewer`, never in
`vscode-ocp-cad-viewer`.** Editing the copied bundle directly, or trying to commit
it, loses the work on the next build.

`three-cad-viewer/dist/` is likewise gitignored there (`.gitignore` line 4) — it is
published to npm via the `files` field, not tracked in git.

## The build loop

```bash
# 1. Make the change in three-cad-viewer
cd ~/git-projects/three-cad-viewer
# ... edit src/tools/cad_tools/, src/core/viewer.ts, src/ui/, ...

# 2. Build the bundle
npm run build

# 3. Copy the built files into vscode-ocp-cad-viewer
cp dist/three-cad-viewer.esm.js ~/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/js/
cp dist/three-cad-viewer.css   ~/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/css/

# 4. Test with a model from this repo
cd ~/git-projects/build123d/build123d-models
uv run show lens_cap
```

`npm run build` runs `scripts/copy_version.cjs` then rollup with
`BUILD:production`, emitting into `dist/`. Only the two files above need copying —
the ESM bundle and the stylesheet.

## Source layout of three-cad-viewer

The source is TypeScript under `src/`:

| Path | Contents |
| --- | --- |
| `src/index.ts` | Package entry point |
| `src/core/` | `viewer.ts`, `viewer-state.ts`, `studio-manager.ts`, `patches.ts`, `types.ts` |
| `src/tools/cad_tools/` | `measure.ts`, `select.ts`, `tools.ts`, `ui.ts`, `zebra.ts` — the interactive tools |
| `src/ui/` | `toolbar.ts`, `treeview.ts`, `display.ts`, `info.ts`, `slider.ts`, `index.html` |
| `src/rendering/`, `src/scene/`, `src/camera/`, `src/utils/`, `src/types/` | Three.js plumbing |

A new toolbar tool generally touches `src/tools/cad_tools/` (the behaviour) and
`src/ui/toolbar.ts` (the button).

Other useful scripts in that repo: `npm run lint` (eslint), `npm run format`
(prettier), `npm run test:run` (vitest), `npm run start` (rollup watch).

## When a change does not show up

Work down this list before debugging the code:

1. **Did the build run?** Compare mtimes: `dist/three-cad-viewer.esm.js` must be
   newer than the source file you edited.
2. **Did the copy run?** Compare `ocp_vscode/static/js/three-cad-viewer.esm.js`
   against `dist/three-cad-viewer.esm.js`. The deployed bundle can drift a long way
   from the current `src/` — it is a snapshot of whatever tree was last built and
   copied, and nothing enforces that they match.
3. **Is the viewer still running the old bundle?** The server is a long-lived
   process on port 3939 (see `viewer.py`). Restart it so the page reloads.
4. **Browser cache** — the bundle is several megabytes and is served statically;
   force a reload of the viewer window.

## Where a change belongs

| Change | Repo |
| --- | --- |
| Toolbar button, 3D interaction, rendering, tool behaviour | `three-cad-viewer` |
| Python `show()` API, tessellation, backend HTTP endpoints, VS Code extension | `vscode-ocp-cad-viewer` |
| The pywebview window wrapper, port and startup logic | this repo (`viewer.py`, `show.py`) |
| A model | this repo (`models/`) |
