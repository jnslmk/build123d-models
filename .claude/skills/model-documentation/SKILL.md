---
name: model-documentation
description: >-
  Resolves the README that documents a public CAD model and gates geometry or
  model-contract work on user confirmation of its purpose and accepted-decision
  delta. Use before changing geometry; before creating or revising a CAD
  contract; when documentation scope changes through a nested package or a
  standalone-model promotion. TRIGGER: about to edit a public model's geometry
  or CAD contract; choose which README owns a model; promote a documented
  standalone public model to a package.
---

# Model documentation

**The README is the public entry point; the detailed specification owns accepted
intent.** Read the resolved README and any applicable specification before every
geometry or model-contract change, then make the human confirm the model's
purpose and accepted-decision delta before geometry begins.

## Resolve the documentation unit

1. Identify the public `tessellate_models.MODELS` entry being changed, or the
   intended roster name for a new public model.
2. For a new or documented standalone public model, promote
   `models/<name>.py` to `models/<name>/__init__.py` first. Its Python import
   (`models.<name>`) and `MODELS` roster name stay identical.
3. Starting at the entry's containing package, resolve the nearest enclosing
   `README.md`. A README in a child package is that child's documentation unit
   and overrides its parent family README. If none exists, establish one at the
   family scope that owns the model.
4. Read the resolved README in full. Follow the applicable active
   `docs/<subject>-specification.md` link, if the change has a detailed design
   subject. When `CONTEXT-MAP.md` exists, read the narrowest mapped
   `CONTEXT.md` for that family.
5. For a new documentation unit, draft only its concise purpose before the gate.
   For a new design subject, start its specification from
   `skill://grill-with-docs/references/model-specification.md`; accepted
   requirements remain empty until the user confirms them.

## User gate

Before changing geometry or a model contract:

1. State the README's current purpose and the applicable specification's purpose
   in the terms of the proposed change.
2. State the exact accepted-decision delta: which requirement will be added,
   changed, removed, or that there is no accepted-decision change.
3. Ask the user to confirm both the purpose and that delta. Wait for their
   response; do not begin geometry or alter the model contract while it is
   pending.
4. After confirmation, update the applicable specification when a requirement
   changed, update the README pointer if the documentation entry changed, then
   make the approved geometry or contract change.

## README and specification content

Lead the README with the concise public purpose and link every active design
subject to its detailed specification. The specification records durable
accepted requirements once, each with its source or rationale and consequence.
Keep unresolved technical definitions, current-slice evidence, and acceptance
state in the CAD contract; keep reversible alternatives in sketches. A scoped
`CONTEXT.md` contains only the terms that make those records unambiguous.
