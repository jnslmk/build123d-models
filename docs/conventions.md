# Project Conventions

## Sketch before you model

**When the open question is *which shape*, do not answer it by building one
model well. Build four badly and put them side by side.** Everything below this
section — named fits, edge treatments, `checks.py`, registration, CI — is the
cost of being *right*, and paying it before the shape is chosen means paying it
three more times.

The numbers are lopsided enough to settle the argument. A concept-grade variant
(boxes and cylinders, no fillets, no clearances, no checks) builds in ~0.03 s and
renders in ~0.05 s. `led_psu_enclosure.create()` takes 37 s and
`drill_storage.wood.base` 16 s, before lint, types, a commit and a Pages deploy.
Four options cost **one interpreter start, not four models**.

```bash
uv run sketch box_closure     # sketches/box_closure.py -> exports/sketch-box_closure.html
```

A sketch is a plain module in `sketches/`, which is **gitignored on purpose**:

```python
"""How should a small parts box close?"""      # the question -- becomes the heading

from build123d import *
from sketch import variant

FIDELITY = "Massing only -- dimensions invented"   # stamped on the sheet
NOTES = "Free-text argument, rendered at the bottom."

@variant(spec={"Parts": "2", "Reopens": "freely"}, views=("iso", "right"))
def stepped_rabbet():
    """Lid drops onto a recessed shelf. No undercuts, prints either way up."""
    ...
    return part
```

The sheet is read off that: module docstring is the question, each decorated
function is a lettered candidate (name → title, docstring → prose), and the
`spec` dicts become one comparison table whose columns are the union of their
keys — so **keep the keys identical across variants**, or a key only one
declares reads as a gap in the others rather than as the difference it is.

Then **publish the HTML as an artifact and give the user the link.** That is the
delivery step, the same way a render is for a finished model. The file is one
self-contained page — inline SVG bound to `currentColor`, so it follows the
reader's theme and stays sharp at any zoom, and no external anything.

Three rules keep this from rotting into a second, worse `models/`:

- **A sketch is never committed.** `sketches/` is gitignored, and that is the
  whole mechanism. A sketch has invented dimensions, no fits from
  `models.lib.fits`, no edge treatments and no checks; committed, it would sit
  in the tree looking like a model, breaking every rule below, indistinguishable
  from the real thing in six months. `sketch.py` and its test are repo
  furniture; what they consume is not.
- **A winning sketch is rebuilt, not promoted.** The chosen candidate gets
  written properly under `models/` from scratch, and the sketch is deleted. It
  was an argument, not a draft.
- **Say the fidelity, per sheet.** How crude to be depends on the question:
  topology needs blocks, proportion needs measured massing. `FIDELITY` is
  stamped on the sheet so a reader can never mistake which one they are looking
  at. When it is proportion under discussion, say in chat that the massing is
  measured — the default stamp claims the opposite.

Scale is not depth: four variants differing only in a fillet radius are not a
sheet, they are one model rendered four times. Vary the thing the question is
about.

## Core-first CAD iteration

For new assembly work, a feature family, or a change with an unresolved shape or
dependent interface, work one **current slice** at a time. The executable
procedure is the local `cad-iteration` skill; this section is its policy and
record.

A current slice is the smallest reviewable design unit: its anchor part, the
requirements it must meet, the evidence behind its dimensions, and the questions
that must be decided before another part depends on it. Start its
`cad-contract.md` from the skill's reference template and keep it current.

1. **Resolve real choices before geometry.** Record already-decided constraints
   and evidence-backed dimensions in the contract. For a genuinely open design
   decision, ask the human to invoke the existing user-invoked
   `grill-with-docs` process; do not resolve or implement that choice until it
   completes and its decision is recorded. It owns the rigorous design tree and
   its ADR/glossary capture. If the unresolved question is shape, make sketches
   under the workflow above and show the alternatives before choosing.
2. **Build the anchor only.** Implement just the current anchor part. Describe
   dependent connectors, fasteners, cable paths, and interfaces as constraints
   in the contract rather than modelling them.
3. **Prove and show the slice.** Run the targeted physical proof appropriate to
   the part, then present the relevant visual views using the post-update
   verification workflow below. State which contract predicates that proof and
   those views cover.
4. **Wait for human acceptance.** A slice is accepted only when the human
   explicitly accepts it or gives an instruction that clearly approves this
   specific slice. “Continue” alone means continue improving the current slice;
   it does not authorise downstream work.
5. **Advance deliberately.** After acceptance, make the next dependent
   connector, fastener, cable path, or other interface its own current slice,
   update the contract, and load the specialised skill that applies before
   modelling it.

The acceptance gate is a design boundary, not a formality: downstream geometry
is allowed only after the current anchor has been accepted.

## Post-Update Verification

**After every edit to a model, verify it visually and put the result in front
of the user — immediately, without being asked.** That is the last step of any
model change. Both environments now share one way of showing a model: a
self-contained HTML artifact, built by `uv run view`, that renders the model
with the same three.js viewer the deployed site uses. There is no second,
cloud-only path to keep in sync.

```bash
uv run view lens_cap                 # exports/lens_cap.html — one self-contained file
uv run view lens_cap --serve         # also serve it on http://127.0.0.1:8000, for your own browser
```

The artifact is one file: three.js and its loaders are inlined, and the model's
GLB (colour) — or STL if the GLB is missing — is embedded as a base64 data URI.
It renders the same house-blue default, ground grid, orbit controls and camera
framing as the site, from the shared `website/viewer.js`. It builds the GLB on
demand if the model has not been built yet, so it works straight after a source
edit. It is what the agent *shows*; it is not a build step and is never
committed (`exports/` is gitignored).

Then **put it in front of the user**:

- **Locally**, open the HTML file in a new browser window on the user's machine:
  `xdg-open exports/<name>.html` (not a tab in the headless browser tool).
  Or `uv run view <name> --serve` and open the printed URL in a new window.
- **In the Claude cloud environment**, publish the HTML file as an artifact,
  which hands the user a private claude.ai URL and opens it in their browser.
  Because the file is self-contained under the artifact's strict CSP (no
  external requests), it renders as-is — nothing else needs to be shipped
  alongside it.

`uv run show` (the OCP viewer) still exists and is still the right tool when
you need to *interact* with the geometry — picking a face or edge with the
Element Picker to get a build123d selector, say — rather than merely present
it. The artifact is for showing the result, not for inspecting the model.

When an artifact cannot be shown — a model whose embedded GLB would exceed the
cloud artifact's ~16 MiB rendered cap, or a session without artifact support —
fall back to the rendered image:

```bash
uv run render lens_cap --png          # exports/lens_cap_iso.png
```

`--png`, not the default SVG: an SVG sent to the Claude app arrives as a
*download card*, while the PNG of the same projection renders inline. `render`
is also what produces `docs/` assets. Say which of the two you did — a render
is hidden-line art from `create()`, not the shaded live view, and the gap
matters when colour is the question.

### In the cloud, every `uv run` wants `--no-sync`

A cloud container has no display, and the `viewer` group's `pygobject` ships no
Linux wheel — a plain `uv sync` dies on `girepository-2.0` before anything is
installed. Drop that one group (the model build never imports it) and pass
`--no-sync` to every `uv run` — otherwise a bare `uv run` re-syncs the default
groups and fails again:

```bash
uv sync --no-group viewer                     # once per container
uv run --no-sync view lens_cap
uv run --no-sync check lens_cap
```

Drop **only** `viewer`. The `pdf` group's `pycairo` is also a source build but
its headers *are* present, so it installs fine — and dropping it costs a
spurious `unresolved-import: cairo` in `uv run ty check .`. Detect the
environment rather than guessing at it: `CLAUDE_CODE_REMOTE=true` is set in a
cloud session and `DISPLAY` is not.

## Model documentation

Every public `tessellate_models.MODELS` entry resolves to one documentation unit:
the nearest enclosing package `README.md`. Resolve from the entry's containing
package upward; a child-package README overrides its parent family README. The
resolved repository-relative path is the model's documentation path.

The executable gate is the `model-documentation` skill. Before geometry or a
model-contract change, read the resolved README and wait for the user to confirm
both its purpose and the proposed accepted-design-decision delta.

Lead each README with its concise purpose. Its `## Design decisions` section
records durable accepted choices with their rationale and consequence. CAD
contracts own current-slice evidence and open questions; sketches own reversible
alternatives. Do not place an unresolved choice in a README.

Documentation makes a standalone public entry a package: promote
`models/<name>.py` to `models/<name>/__init__.py` before documenting or
registering it. The Python import `models.<name>` and its `MODELS` roster name
remain unchanged.

## Model Structure

A model is either **one file** or **one package**. There is no third shape, and
which one a model gets is decided by the promotion rule below, not by taste.

### Tier 1 — single-file model

```text
models/<name>.py
```

For a one-part model built in one file that nothing else imports. A standalone
public model needs its own README documentation unit and is therefore promoted
to Tier 2; a public module inside a documented family resolves that family's
README unless a child package overrides it.

### Tier 2 — model package

```text
models/<name>/
  __init__.py      # headline create(), IS_ASSEMBLY, re-exports, the docstring people read first
  config.py        # measured + derived numbers. No geometry.
  <part>.py        # one printed part per module, each with its own create()
  assemblies/      # scenes, one module each, each IS_ASSEMBLY = True
  printable.py     # print layout for the slicer, when the headline view is a scene
  checks.py        # physical geometry gates, only when a model has one
  README.md        # documentation unit unless a child package README overrides it
  docs/            # design-notes.md, part-data.md, assets/ (datasheets, SVGs)
```

Not every package needs every entry — `config.py`, `assemblies/`, `printable.py`,
`checks.py`, and `docs/` appear when the model earns them. A family package
needs a README when it is the nearest documentation scope; a child README exists
only to override that scope. `__init__.py` is always required.

### The promotion rule

Promote a single file to a package as soon as **any one** of these becomes true.
Do not wait for the second one:

1. **It is a standalone public entry.** Registration in `MODELS` requires its
   own package README documentation unit.
2. **A sibling wants to import from it.** One model reaching into another
   model's module is the signal that they are one family sharing one library.
3. **It grows a second showable view or a second printable part.** Each of them
   needs its own module to be addressable by name.
4. **It needs measured hardware constants.** Those belong in a `config.py` next
   to the geometry that consumes them, not scattered as module-level literals.
5. **It earns a physical geometry gate or written design notes.** A gate gets
   `checks.py`; design notes get `docs/`.

The promotion is mechanical: `models/<name>.py` becomes
`models/<name>/__init__.py`, the shared numbers move to `config.py`, and each
part moves to its own module. The top-level import `models.<name>` and existing
`MODELS` roster name stay identical; only separately public child views add
dotted roster names. The website resolves a package name to its `__init__.py`
automatically (`website._source_path`), so the Code panel keeps working.

### Rules that hold in both tiers

- **`create()` is the contract.** Zero-arg (or all-defaulted), returns a `Part`
  or `Compound` **already in print pose**. Every entry point calls exactly this.
  Named builders (`create_endcap()`, `create_print_layout()`) are welcome
  alongside it, but `create()` is what the tooling binds to.
- **One model, one module.** If a view cannot be reached as
  `models.<something>`, it is not a model — it cannot be shown, exported,
  rendered or put on the site. Splitting a second scene into its own module
  costs nothing and buys it a name.
- **Never encode hierarchy in underscores.** The TPU cartridge of the wood set is
  `drill_storage.wood.insert`, not `drill_storage_wood_insert`; the assembled
  scene is `drill_storage.wood`, not `drill_storage_wood_assembly`. Dots are the
  hierarchy; underscores are only for multi-word single names.
- **No private cross-module imports.** `from models.other_model import _helper`
  means the two are one family: make it a package and make the helper public in
  a shared module.
- **Shared geometry goes down, not sideways.** Shared within one family →
  a module in that package (`led_profiles.cradle`). Shared across families →
  `models/lib/`, and only once it is genuinely needed twice.
- **Declare what the model is.** `PARAMS` (list of dicts) makes it parametric on
  the website; `IS_ASSEMBLY = True` marks a scene that is not a print job, so no
  STL/STEP download is offered. Both live in the model, never in a list
  elsewhere that would drift.
- **Use a physical gate when it earns one.** A package with a gate gets
  `checks.py` with a `main()`; a single-file model gets `check()`. `uv run check
  <name>` finds either. Do not add a check merely because geometry changed.
- **No `main()` in a model.** Building and exporting is `main.py`'s and
  `export_model.py`'s job, and a `main()` that re-implements the export paths
  drifts from them. `uv run show/export/render/check <name>` is the interface.
- **Documentation is resolved, not copied.** A public entry uses its nearest
  enclosing package README under the model-documentation policy above. A
  non-public single-file implementation may use its module docstring for local
  context.

### Geometry checks

A geometry check is a **physical gate**, not package furniture. Keep or add one
only when it protects a named failure a finished model could otherwise ship, and
prove it goes red on the pre-fix or deliberately broken geometry before relying
on it. An assertion that has never rejected an error has not earned its runtime
or maintenance cost.

Good gates assert an independently observable relation: one solid in print pose;
interference between separately posed parts; a fastener's head and driver
envelope; a sharp-edge survey; or a load/stress or packing calculation whose
input source is stated. A named fit rule may be a pure design gate when it is
the source of truth, rather than a result re-derived from the same configuration.

Retire or recast a check that:

- restates a constant, collection length, or coordinate produced by the same
  configuration or construction helper;
- labels a point probe as a stronger property than the point actually proves;
- preserves a current design choice rather than a physical failure mode;
- samples one family member while claiming family coverage; or
- allow-lists an edge by loose position. An edge exception instead matches its
  geometry identity (topology, radius, or face), carries a reason, and accounts
  for both `sharp` and `unclassifiable` survey results.

Input measurements, STL tessellation, and a human's assembly sequence are not
facts a B-rep probe can prove. Keep source dimensions with their evidence and
printing caveats; test export quality in the exporter; recast tool access as a
posed fastener/driver relation when geometry can express it.

Use `Report.solid_at()` or `solid_probe()` for repeated samples of one completed
solid. During an edit, run the affected leaf's targeted check. Run a whole-family
check only as a final integration gate after cross-part work; keep deliberately
slow exhaustive sweeps as explicit on-demand tools, not the default edit loop.
When an intent changes, delete the old intent check with it and replace it only
if the physical failure mode remains.

### Registering a model

Add the name to **`tessellate_models.MODELS`**. That is the whole procedure —
`main.py` builds straight from that list, the website reads it, CI reads it, so
there is no second place to keep in sync and no way for them to disagree.

Registration is a documentation commitment: the entry must resolve to its
nearest package README under §"Model documentation" before it is public.

Only modules with a zero-arg `create()` belong there. The shared pieces a part is
built from (`drill_storage.box`, `led_profiles.cradle`, `led_psu_enclosure.config`,
`models/lib`) are not models. A new package also has to be added to
`[tool.setuptools] packages` in `pyproject.toml` — subpackages are not implied by
their parent, so a missing line ships a wheel without that model.

**Enforceable, not just advised.** `tests/test_model_registry.py` fails on a
module that offers a zero-arg `create()` and is not in `MODELS`, on a roster name
that resolves to nothing, and on a package missing from `[tool.setuptools]
packages` — so forgetting any of the three breaks the build instead of quietly
shipping a model nobody can find. It is a static AST read, no model is imported,
and it runs in the default suite. As with `sharp_convex_edges`, genuine
exceptions are real and must be **named** in that file's `NOT_A_MODEL` list with
a reason rather than merely left out; a stale entry there fails too.

The dots earn their keep on the site as well: the page's picker is built from
the name grammar alone (`website/index.html`, `buildTree`/`renderPicker`), one
row of chips per level, each row holding only the siblings valid under what is
already chosen. So a well-named model lands in the right group for free, and
switching one level keeps the levels below it where they exist —
`drill_storage.wood.base` → `drill_storage.metal.base` is one click. Two
things follow. A name that encodes hierarchy in underscores flattens its whole
family into one long row, which is the practical cost of breaking the
"underscores are only for multi-word single names" rule. And a naming layer
with no `create()` of its own is fine (`drill_storage.hex.bits`,
`led_profiles.assemblies`): its chip resolves to the first model under it.

### Known deviations

Nothing to copy here — these are gaps, and closing one is welcome work:

- The three `drill_storage` variant packages (`wood`, `metal`, `stone`) have no
  `config.py` and no `docs/`, and their `checks.py` only forwards to the family's.
  That is deliberate: they are four-module naming layers over geometry and
  clearances that are deliberately shared, so the numbers live in
  `drill_storage/sets.py` and `config.py` and the argument in `drill_storage/docs/`.
  Copy the shape only for a package that is genuinely a thin leaf; a model that
  owns its own numbers still owns its own `config.py`.
