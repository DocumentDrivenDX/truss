# Truss design documents

The documents that govern the code. Start at the [repository README](../../README.md).

- [Product vision](00-discover/product-vision.md) and [PRD](01-frame/prd.md)
- Features: [FEAT-001 to FEAT-008](01-frame/features/)
- Architecture: [architecture](02-design/architecture.md)
- Decisions: [ADR-001 to ADR-009](02-design/adr/) (ADR-009 is withdrawn)
- Contracts: [CONTRACT-001 to CONTRACT-014](02-design/contracts/); the storage, journal, catalog,
  mutation, embedding and Weft handoff boundaries. `contracts/bindings/` is TypeScript source used by
  `packages/postgresql`; `contracts/*.json` and `models/` are schemas and UMF models read by code.

Technical designs, user stories, test plans, spikes, handoff audits and run evidence were removed
from the tree; they remain in git history. What is built is in [CHANGELOG](../../CHANGELOG.md); what is
not is in [ROADMAP](../../ROADMAP.md).
