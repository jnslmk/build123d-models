---
name: grill-with-docs
description: Interview a CAD design and capture its vocabulary, specification, and current-slice constraints.
disable-model-invocation: true
---

# CAD definition interview

**Separate language, durable intent, and current work.** This user-invoked
interview turns a genuinely open CAD design into a reviewable definition without
silently authorizing geometry.

Load `grilling`, `domain-modeling`, `model-documentation`, and `cad-iteration`
before the first question. Their roles remain distinct: grilling owns the design
tree, domain modeling owns vocabulary and earned ADRs, model documentation owns
the public-model purpose gate, and CAD iteration owns the later anchor slice.

## Resolve the document scope

1. Identify the public model entry and resolve its documentation-unit `README.md`
   with `model-documentation`. State the model purpose in the terms of the
   discussion.
2. Read `CONTEXT-MAP.md` when it exists, then the narrowest mapped `CONTEXT.md`.
   Treat it as a glossary, never as a requirements scratchpad.
3. Resolve the design subject's `docs/<subject>-specification.md`. Read it when
   present; otherwise start it from `references/model-specification.md`. Read the
   active `docs/cad-contract.md` only to learn the current anchor and constraints.
4. State the exact accepted-decision delta before questioning: new, changed,
   removed, or none. Name the specification that will own the result.

## Interview the decision tree

Use the `grilling` rounds exactly: map the design tree, ask every currently
unblocked frontier question in one numbered round with a recommendation, and
wait for the user's answers. Find repository and external facts yourself. A
question whose answer depends on another open answer waits for a later round.

Ask about design intent and durable requirements here. Keep implementation
sizing, fits, geometry predicates, and dependent interfaces in the later CAD
contract unless their architecture itself is the decision under discussion.
When form is open, prepare a reversible sketch before asking the user to choose
it.

## Capture each settled branch

Update the owning records in the same round that a term or decision settles:

- **Vocabulary:** add or sharpen a physical term in the narrowest `CONTEXT.md`.
  Keep each term in one glossary and exclude implementation facts.
- **Specification:** record each user-accepted requirement once with a stable
  subject-local ID, source or rationale, scope, and consequence. Keep explicit
  non-claims and open technical definitions visible rather than implying that a
  decision sized a feature.
- **ADR:** write one under the model family's `docs/adr/` only when the decision
  is hard to reverse, surprising without context, and chosen among real
  alternatives. Link it from the specification.
- **CAD contract:** update only the current slice's requirement IDs and their
  immediate consequences. It must not become a second specification.
- **README:** make the public documentation unit point to the detailed
  specification. Keep the purpose legible there without copying requirement
  tables.

A user answer can change an accepted requirement. Update its specification
record and every affected contract reference together; preserve the superseded
reason only when an ADR earns it.

## Complete the definition

The interview completes only when every reachable design-tree branch is either
accepted in the specification or explicitly open with its blocking effect. Then
verify that the context, specification, contract, ADRs, and README links agree.
Report the named next anchor slice, but leave geometry for `cad-iteration` and
its separate human acceptance gate.
