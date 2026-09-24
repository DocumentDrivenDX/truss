---
ddx:
  id: truss.product-vision
  type: product-vision
  activity: discover
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.competitive-analysis
      kind: informed_by
    - id: truss.vision-input
      kind: informed_by
    - id: truss.naming-research
      kind: informed_by
---

# Product Vision

## Mission Statement

truss lets teams store, query and constrain connected data inside the PostgreSQL
databases they already run, with every property value typed by a UMF schema and
every enforcement claim explicit.

## Positioning

For data platform engineers who keep connected, evolving domain data in
PostgreSQL and describe it with UMF (the DocumentDrivenDX machine-readable
metamodel and schema interchange fabric), truss is a property-oriented graph
engine that stores and queries that data in their own database. Unlike Apache
AGE (a Cypher extension for PostgreSQL), Sqlg (a Gremlin layer over relational
databases) or tables generated from UMF, truss keeps every value exact without
per-type migrations and reports, for every rule, whether PostgreSQL enforces
it, truss enforces it, or nothing does.

## Vision

A team adds a new kind of entity or relationship by publishing a UMF schema
revision instead of writing table migrations. Every property value carries its
type, schema revision and origin, and stays readable with plain SQL. Engineers
traverse relationships, change single properties and check constraints in the
same PostgreSQL database their other systems use. A rule that cannot be enforced
is visible before anyone relies on it, and data that fits no known field is kept
rather than dropped. Document views over the graph remain possible without
making the document the unit of storage.

**North Star**: Teams run connected data on PostgreSQL through truss with every
stored UMF assertion carrying a verified enforcement status and zero silent loss.

## User Experience

A platform engineer has a UMF document describing Customer, Order and OrderLine
records and their relationships. They register it with truss against their
PostgreSQL database. truss returns a binding report: PostgreSQL enforces the
Order key; truss enforces "every Order has at least one OrderLine" inside each
transaction; nothing enforces an aggregate invariant that UMF carries as opaque
text. The engineer imports existing order data. Three records carry a field the
schema does not define; truss keeps those values and lists them. They query
customers whose orders include a given product, two hops away, and inspect the
SQL truss generated. Later they publish a schema revision that shortens a text
limit, and truss lists the stored values that would violate it before accepting
the revision. This scenario describes intended behavior; nothing is implemented.

## Target Market

| Attribute | Description |
|-----------|-------------|
| Who | Data platform engineers in organizations that already run PostgreSQL and maintain UMF or TableSpec schemas for connected, evolving domain data. The owner reports this need; wider audience validation is pending. |
| Pain | Evolving connected data forces a choice between migration churn on per-type tables, schemaless JSONB that hides integrity, or a separate graph database. None shows which rules are actually enforced. |
| Current Solution | Hand-built per-type schemas with recursive queries; JSONB or entity-attribute-value tables; Apache AGE; Neo4j beside PostgreSQL. Working hypothesis pending user research. |
| Why They Switch | Adding a type or relationship should not need a migration; teams need evidence of which rules hold; they cannot or will not move data out of PostgreSQL. Assumption to validate. |

## Key Value Propositions

| Value Proposition | Customer Benefit |
|-------------------|------------------|
| Property-level storage in the user's PostgreSQL | Change or audit one value, with its history and origin, in plain SQL and without a second database. |
| Schema from UMF | The schema the team already maintains drives storage and validation; there is no second model to keep in sync. |
| Enforcement report per assertion | Before go-live, engineers know which rules PostgreSQL enforces, which truss enforces and which nothing enforces. |
| Nothing silently dropped | Imports never lose information quietly; unrecognized values are retained and listed. |

## Success Definition

Proposed strategic measures for the first 12–24 months of use; targets are not
yet agreed with the owner.

| Metric | Target |
|--------|--------|
| Enforcement transparency (primary KPI) | 100% of UMF assertions in the conformance corpus carry a machine-readable enforcement status (database, engine, none), verified by the conformance suite on every supported PostgreSQL version |
| No silent loss | 0 values dropped across the import corpus; every unbound value appears in the retained-value report, measured by round-trip tests |
| Evidence-backed claims | 100% of published support claims name the PostgreSQL version, UMF core version and subset, and link executable evidence |
| Performance | Single-object fetch and 1–3 hop traversal p95 within 2× of a hand-designed schema for the same data on the benchmark corpus (target to validate in `frame`) |
| Adoption | At least 1 production consumer outside the truss maintainers |

## Why Now

UMF's experimental core 0.5.0 carries field, nullability, cardinality and facet
ideals, with qualified PostgreSQL bindings for the first three, and UMF's tracker
opened relationship and physical-binding work (FEAT-006, TD-045 to TD-049) on
2026-09-24. A consumer can now type storage from UMF instead of inventing a
schema language. PostgreSQL reverted native SQL/PGQ graph queries from
PostgreSQL 19 on 2026-09-07, so no built-in standard graph layer can ship before
PostgreSQL 20. Prior graph-on-SQL efforts have thinned: Gel's company shut down
in December 2025 and Kuzu was archived in October 2025. Evidence is in the
[competitive analysis](competitive-analysis.md).

## Review Checklist

- [x] Mission statement is specific — names the user, the problem, and the approach
- [x] Positioning statement differentiates from the current alternative
- [x] Vision describes a desired end state, not a feature list
- [x] North star is a single measurable sentence
- [x] User experience section describes a concrete scenario, not abstract benefits
- [x] Target market identifies specific pain points and switching triggers
- [x] Value propositions map to customer benefits, not internal capabilities
- [ ] Success metrics are measurable and time-bound (targets proposed; owner agreement pending)
- [x] Why Now section names a specific change, not a vague opportunity
- [x] Business case details, competitor matrices, requirements, and technical choices are left to their own artifacts
- [x] No implementation details (technology choices, architecture) — those belong in design
- [ ] Audience, alternatives and switching triggers validated with prospective users
