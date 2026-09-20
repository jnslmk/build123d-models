---
name: cad-iteration
description: >-
  Enforces human-gated, core-first iteration for a CAD assembly, feature family,
  or change with an unresolved shape or dependent interface. Use before modelling
  an anchor part alongside connectors, fasteners, cable paths, or other parts that
  depend on it; load when an accepted core must precede the next interface.
  TRIGGER: starting or extending a multi-part CAD design, choosing an anchor part,
  awaiting feedback on a current CAD slice, or about to add a dependent interface.
---

# CAD iteration

**Make the core reviewable before making its dependencies real.** A connector is
not harmless detail when its position, access, assembly sequence, or load path
can force a change in the part it attaches to. Keep that commitment out of the
model until the human accepts the part that owns it.

This skill implements the project policy in `docs/conventions.md` §"Core-first
CAD iteration". Keep the current slice's decisions in the compact template at
`references/cad-contract.md`.

Before changing this contract or its geometry, load `model-documentation`; it
owns README resolution and the purpose/accepted-decision user gate.

## Current-slice contract

Before writing geometry, name the current slice and its **anchor part**. Complete
the contract's locked decisions, evidence-backed dimensions, open decisions,
service/assembly sequence, required skills, verifiable predicates, visual review,
and acceptance gate.

The contract is a boundary, not a backlog. It may describe a downstream interface
as a requirement, envelope, or unanswered question, but the current model may
implement only the anchor part. A part is an anchor when the human can judge its
shape, proportions, purpose, and print pose without its dependants being made
real.

## Resolve only what is genuinely open

Separate a missing decision from an implementation detail:

- A locked decision or measured dimension belongs in the contract with its source.
- A genuinely open design choice must be handed explicitly to the existing
  user-invoked `grill-with-docs` process. Ask the human to invoke it; it owns the
  design-tree questioning and ADR/glossary capture. Do not resolve or implement
  that choice until the process has completed and its decision is recorded in the
  contract.
- When that open choice is shape, use the sketch workflow in
  `docs/conventions.md` §"Sketch before you model" to supply reversible
  alternatives for the decision. Do not promote a sketch to an anchor until the
  recorded decision permits it.

## Iterate the anchor

1. Implement only the anchor part named by the contract. Leave dependent
   connectors, fasteners, cable paths, mating features, and other interfaces as
   contract constraints.
2. Apply the skills listed by the contract before sizing their governed features.
   The normal downstream skills remain downstream: for example,
   `fasteners-and-inserts`, `part-joints`, `box-closures`, and
   `fdm-fits-and-clearances` start only in their accepted slice.
3. Run targeted physical proof only for the current anchor's verifiable
   predicates — an existing or earned geometry gate, a focused measurement, or
   another direct physical check. Keep predicates that depend on connectors,
   fasteners, cable paths, or assembly interaction pending for their own slice.
   A visual view is evidence of visible shape and presentation, not a substitute
   for proof of hidden geometry.
4. Produce only the views needed to judge the current anchor: normally an
   isometric view plus every orthographic or section-like view needed to assess
   its stated constraints. Connector geometry and assembly views remain pending
   until their dependent slice has passed its acceptance gate. Follow
   `docs/conventions.md` §"Post-Update Verification" to put the result in front
   of the human.
5. Report the current anchor's contract, proof, and views together, then ask for
   feedback or acceptance of this named slice.

Feedback revises the same anchor and repeats proof and presentation. The word
“continue” by itself means keep working in this current slice; it never opens the
next one.

## Acceptance gate

Open a dependent slice only after the human has either:

- explicitly accepted the named current slice; or
- issued an instruction that clearly approves that specific slice while directing
  the next work.

Record the acceptance signal in the contract. Then update it for the next slice,
make that connector, fastener, cable path, or interface its anchor, and repeat
this skill from the contract step. Do not infer approval from silence, a request
to “continue,” or a request that only refines the current anchor.
