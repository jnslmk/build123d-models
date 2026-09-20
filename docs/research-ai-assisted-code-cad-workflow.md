# AI-assisted code-CAD workflow controls

**Accessed:** 2026-09-20  
**Scope:** source-backed controls for an AI agent that writes or changes parametric CAD source in this repository. This is workflow guidance, not a geometry or manufacturing specification.

## Source-backed facts

1. **Prompts should separate stable instructions, examples, and task-specific context.** OpenAI's prompt-engineering guide says Markdown headings/lists and XML can mark logical boundaries; it describes a typical developer message as identity, instructions, examples, then context. It also recommends typed inputs/schemas, representative fixtures and evaluation checks before production prompt changes, and staged rollout where needed. [O1]
2. **Prompt/model output is not a deterministic CAD oracle.** OpenAI describes generated content as non-deterministic and recommends pinning model snapshots and building tests/evaluation suites to monitor prompt behavior while iterating or changing model versions. [O1]
3. **build123d is parametric BREP CAD, and its own example derives geometry from named parameters.** The documented cup example defines `wall_thickness` and derives `fillet_radius` from it; it also ends with a numeric volume assertion. [B1]
4. **build123d feature selections are unordered until explicitly refined.** Its topology guide says a selector returns a `ShapeList`; sorting is a critical isolation step because a selector's `ShapeList` is unordered. The guide supports selection by geometric type, location/direction, size, and custom predicates, as well as history-scoped `Select.LAST` and `Select.NEW`. [B2]
5. **This repository already supplies distinct visual and physical interfaces.** `uv run view <name>` produces a self-contained HTML viewer artifact and the convention requires a visual result after every model edit. `uv run check <name>` runs a model's optional physical geometry gate. Existing guidance says a useful gate protects a named ship-risk and asserts an independently observable relation (for example, interference, one solid in print pose, or tool envelope), rather than restating construction constants. [R1] [R2]
6. **The repository deliberately stages concept selection before full modelling.** Its convention calls for multiple low-fidelity, rendered sketch variants when the open question is shape; sketches are not committed and the chosen concept is rebuilt properly under `models/`. [R2]

## Recommendations (inferences from the facts above)

### 1. Give the agent a constrained CAD brief, not an aesthetic-only request

Use a structured request with these fields:

```text
Goal and use case
Known dimensions and their evidence (measured / nominal hardware / assumed)
Print material, print pose, manufacturing constraints, and named fit class
Required interfaces and forbidden collisions
Named geometric invariants and tolerances
Required views or comparison alternatives
Permitted files/APIs and explicit non-goals
Required proof: target geometry gate, visual views, and acceptance observation
```

Treat unknown dimensions as questions or explicit assumptions. Ask the agent to expose source-of-truth dimensions as named parameters and derive dependent dimensions from them; do not ask it to tune unrelated literals. This makes the result inspectable and aligns the brief with parametric source rather than a one-off mesh ([B1]).

### 2. Make reusable skills a small, stable instruction layer

Keep a short skill per recurring physical concern (fits, fasteners, closures, edge treatment, text, or selected topology). A skill should state: applicability trigger; allowed source-of-truth inputs; named invariant(s); preferred construction pattern; check/visual evidence; and failure modes. Pass the active skill plus local model context as distinct prompt sections, rather than embedding a broad design manual in each request. This follows the documented separation of instructions, examples, and context ([O1]) and makes updates reviewable.

### 3. Request geometry invariants that can fail deterministically

For each meaningful requirement, specify a predicate that a completed BREP can prove: solid count/print pose, clearance or interference between posed parts, material at a required point, fastener and driver envelope, minimum wall/edge condition, or a derived fit relation. Implement a `checks.py`/`check()` gate only when it blocks a named physical failure, and prove that the assertion rejects deliberately broken geometry before treating it as coverage ([R1]). Visual review complements these predicates; it does not replace them.

### 4. Avoid topology-fragile feature addressing

Do not select `edges()[n]` or `faces()[n]` from an unrefined list. Select features through stable meaning—plane/axis, geometry type, radius/area, position, adjacency, a custom predicate, or immediately-created history—and then make any ordering explicit. When a selection is hard to express robustly, change the construction so the target exists at a known stage, or verify the intended result with a geometry predicate. This directly addresses the unordered-selection contract ([B2]).

### 5. Use a two-loop cadence: choose, then prove

1. **Concept loop:** for an unresolved shape question, generate several deliberately low-fidelity sketches with the same comparison criteria; render them side by side; obtain the choice; discard the sketches ([R2]).
2. **Implementation loop:** make one coherent source change; run the narrow physical gate when the model has an earned one; render/view the changed model in the required orientations; inspect the result against the brief; then stage the next change. Keep prompt/model changes behind fixtures or evaluation cases and pin the model snapshot when production repeatability matters ([O1] [R1]).

This cadence keeps visual feedback early while reserving expensive or brittle checks for the physical claims they can actually establish.

## Sources

- **[O1] OpenAI — “Prompt engineering.”** Official OpenAI Developers documentation. <https://developers.openai.com/api/docs/guides/prompt-engineering> (accessed 2026-09-20).
- **[B1] build123d — “About.”** Official build123d documentation; includes the parametric teacup example and volume assertion. <https://build123d.readthedocs.io/en/latest/> (accessed 2026-09-20).
- **[B2] build123d — “Topology Selection and Exploration.”** Official build123d documentation. <https://build123d.readthedocs.io/en/latest/topology_selection.html> (accessed 2026-09-20).
- **[R1] build123d-models — `AGENTS.md`, “Commands” and “Model Contract.”** Repository-maintained primary project guidance. [`../AGENTS.md`](../AGENTS.md) (accessed 2026-09-20).
- **[R2] build123d-models — “Project Conventions,” “Sketch before you model,” “Post-Update Verification,” and “Geometry checks.”** Repository-maintained primary project guidance. [`conventions.md`](conventions.md) (accessed 2026-09-20).
