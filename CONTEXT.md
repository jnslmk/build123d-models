# CAD model language

Domain terms used to distinguish physical parts and design intent in this model collection.

## Language

### Stella profile connectors

**Vertex core**:
The central body at a Stella vertex, where three profile arms meet.
_Avoid_: Connector when it could mean an arm or an electrical connector.

**Profile arm**:
The structural connector between one lamp-profile end and a vertex core.
_Avoid_: Core when referring to the branch rather than the central body.

**Profile keeper**:
The removable retaining piece that completes the capture of a profile at its support.

**Organic core form**:
A continuous outline following the three branches, with broad, smoothly blended roots.
_Avoid_: Round core as a synonym; rounded transitions do not imply a circular body.

## Public model documentation

**Public model**:
A `tessellate_models.MODELS` entry exposed to model tooling and the website.

**Model family**:
A package hierarchy that groups related public models and shared implementation.

**Documentation unit**:
The nearest enclosing package `README.md` that documents a public model; a child
package README overrides its parent family README.

**Accepted design decision**:
A durable, user-confirmed choice recorded in a documentation unit with its
rationale and consequence; open choices remain in CAD contracts or sketches.
