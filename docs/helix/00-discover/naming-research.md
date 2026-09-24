---
ddx:
  id: truss.naming-research
  activity: discover
  status: draft
  authoring:
    home: repo
  links: []
---

# Naming Research

**Decision (owner, 2026-09-24):** the project is named `truss`, hosted at
`DocumentDrivenDX/truss`. This note records the criteria, the candidates
considered, the checks run and the residual naming risks.

## Criteria

1. Short, single lowercase word, matching existing DocumentDrivenDX repository
   names: `umf`, `ddx`, `helix`, `axon`, `tablespec`, `innsigle`, `dun`.
2. No `umf-` prefix. truss consumes UMF, the DocumentDrivenDX machine-readable
   metamodel and schema interchange fabric; a `umf-` name would read as
   UMF's runtime or reference implementation and blur UMF's NFR-50 boundary,
   which places query execution and storage outside UMF.
3. No neuroscience metaphor. Axon, a DocumentDrivenDX project, is
   document-oriented; a neural name (dendrite, synapse, plexus) would read as
   part of Axon.
4. Evokes a graph on a foundation, or a structure that grows capabilities.
5. No collision with an existing graph or database project.

## Candidates

| Candidate | Meaning and fit | Findings (2026-09-24) | Outcome |
| --- | --- | --- | --- |
| `truss` | An engineering truss is joints (nodes) connected by members (edges) that carries load on a foundation: a graph on relational storage, rigid under constraints. | No graph or database project found. Namesakes in other domains: Baseten Truss (Python ML model-serving CLI), Homebound truss (TypeScript CSS DSL), and npm packages under `@truss-harness/*` (agent harness, published August 2026), `@nao1215/truss-*` (image transforms), `@truss-security/truss-sdk`, `@open-truss/open-truss` and `@ucsantacruz/truss`. Unscoped npm `truss` is a project generator last published 2013. `@truss/core` and `@truss/engine` are unpublished. | **Selected** |
| `rhizome` | A network that grows without hierarchy. | Unscoped npm name taken (URL router, last published 2013). Harder to spell. Web collisions not searched. | Runner-up |
| `quiver` | The category-theory term for a directed multigraph; the most precise fit. | In-domain collisions: Quiver GraphQL engine (`graphql-quiver`) and Verizon's Quiver Scala multigraph library; also a Python RAG framework. Unscoped npm name taken (last published 2015). | Rejected: in-domain collisions |
| `trellis` | A lattice that plants grow on. | Unscoped npm `trellis` describes an "event-sourced causal graph", published 2026-09-17: in-domain and active. | Rejected: in-domain collision |
| `weft`, `tessera`, `arbor`, `keel`, `mycelium` | Weaving, mosaic, tree, hull and fungal-network metaphors. | Unscoped npm names all taken; `keel` (backend framework) published 2026-09-23. Weaker graph metaphors. | Not pursued |
| `sqlgraph`, `graphtable` | Descriptive. | Unscoped npm names free. Generic and hard to search; `graphtable` echoes the SQL/PGQ `GRAPH_TABLE` operator. | Not pursued |
| `lattice` | Order-theory structure. | UMF's architecture explicitly rejects a universal type lattice; the name would signal the opposite of truss's intent. Registries not checked. | Rejected by criteria |
| `umf-graph`, `umf-store` | UMF-branded. | Violate criterion 2. Registries not checked. | Rejected by criteria |
| `dendrite`, `synapse`, `plexus` | Neural metaphors. | Violate criterion 3. Registries not checked. | Rejected by criteria |

## Method

- npm registry lookups of `https://registry.npmjs.org/<name>` for each checked
  candidate, reading the latest version's publish date, plus the registry
  search API for `truss`.
- Web searches for "quiver" graph databases and engines, "truss" graph
  databases on SQL, and notable open-source projects named Truss.
- DocumentDrivenDX repository listing through GitHub.

All checks ran on 2026-09-24. No trademark search was performed.

## Residual Risks

| Risk | Consequence | Mitigation |
| --- | --- | --- |
| Name is crowded outside the graph domain | Search results for "truss" favour Baseten and other namesakes | Use "truss graph engine" in descriptions and package metadata |
| npm scope `@truss` ownership unverified | An unpublished package name does not prove the scope is unclaimed | Claim the npm organization before the first publish, or publish under an existing DocumentDrivenDX scope |
| No trademark search | Unknown legal exposure | Run a trademark search before any public release |

## Sources

- [Baseten: why we open-sourced Truss](https://www.baseten.co/blog/why-we-open-sourced-truss/)
- [basetenlabs/truss](https://github.com/basetenlabs/truss)
- [homebound-team/truss](https://github.com/homebound-team/truss)
- [Quiver GraphQL engine (graphql-quiver)](https://github.com/graphql-quiver)
- [Verizon Quiver](https://verizon.github.io/quiver/)
- [Quiver entry, Enterprise DNA open-source directory](https://enterprisedna.co/directories/open-source/quiver/)
- [npm registry search for "truss"](https://registry.npmjs.org/-/v1/search?text=truss&size=15)
- npm registry entries: [truss](https://www.npmjs.com/package/truss),
  [quiver](https://www.npmjs.com/package/quiver),
  [rhizome](https://www.npmjs.com/package/rhizome),
  [trellis](https://www.npmjs.com/package/trellis),
  [keel](https://www.npmjs.com/package/keel)
