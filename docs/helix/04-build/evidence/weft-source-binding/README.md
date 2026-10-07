# Concrete Truss source binding for Weft review

Status: synthetic, unregistered, source-only. No query executed and no native layout or adapter qualified.

[binding.json](binding.json) is an actual `truss-postgresql-binding/0.1.0` packet using the selected Truss 0.4 declaration layout. It describes one original UMF Record (`Item`) and one required nonnullable string Field (`label`), assigned synthetic catalog IDs 17 and 23. This small fixture establishes assembly and review, not coverage of all Truss value/query families.

The packet contains exact original logical model/source/definition bytes, a complete declared 30-table/264-column physical identity map, the actual generated layout SQL, property/value/codec/presence/read-context definitions, explicit execution refusal and source-only qualification. Profile definitions are static data; their hashes do not confer registry authority or load code. No `{}` placeholder stands in for an accepted definition or original source.

The application UMF model and Truss's internal storage UMF model are distinct. `basis.modelBundle` contains the original logical application input. `basis.layoutSql` contains the selected storage DDL. The compact `layoutInventory` pins the full source-effect inventory and saved native AST, and provides explicit declared selectors. Its physical identities are review labels, not admitted native object identities. A matching column name or source pointer cannot establish installed correspondence.

The exact fixture model bytes are [original-model.json](original-model.json); the binding's model pin and source artifacts preserve those bytes without an added newline. [profile-definitions.json](profile-definitions.json) contains every original profile body referenced by a pin. [nested-definitions.json](nested-definitions.json) provides readable decoded home/value/presence/codec/context objects. [declaration-map.json](declaration-map.json) contains the same exact declaration map embedded in the packet.

## Reproduce

From Truss's main checkout:

```sh
python3 docs/helix/04-build/evidence/design-audit/build-weft-source-binding.py
bun docs/helix/04-build/evidence/design-audit/check-weft-source-binding.ts /private/tmp/weft-build/node_modules/ajv/dist/2020.js
python3 docs/helix/04-build/evidence/design-audit/check-weft-source-binding.py
```

The Ajv path is the currently observed test dependency, not a published package or production requirement. The check uses Ajv 2020 through the existing local dependency and UMF's current `readDocument`; it validates the binding and five nested definitions, plus original UMF document validity. The independent Python check verifies canonical base64/digests, every original profile body, source/model pins, typed-owner/property consistency, selector correspondence, complete declaration-map coverage, absence of fabricated qualification and the recursively decoded occurrence budget.

Current binding size is 206,405 bytes; recursively decoded artifact occurrences total 200,916 bytes across 23 occurrences. Both fit the four-MiB limits inspected in Weft's current `binding.rs`. Repeated artifacts are charged by occurrence; no deduplication allowance or universal capacity claim is inferred. Larger logical catalogs may require a separately designed bounded export scope or jointly versioned transport; do not silently drop required mappings to fit a limit.

## Owner review requested

1. Compare the packet and nested definitions with current Weft admission grammars and original-source correspondence. Record any concrete field/profile incompatibility.
2. Confirm that the original logical model is distinct from the internal storage model, and that compact source inventory plus explicit selectors is reviewable without implying native admission.
3. Review the selected full-byte key/reservation and immutable acceptance-report homes in CONTRACT-012. This fixture maps no logical key or relationship and does not qualify those paths.
4. Record which exact trusted registry/executor/native evidence is still required before adapter registration. Unknown/unregistered source profiles must refuse before SQL.

This request is for interface review. It does not ask Weft to implement Truss mutations, catalog lifecycle, database bootstrap, resource accounting or native guards. Weft continues to own compilation, result metadata and compiler embedding. Truss must supply actual accepted catalog/layout/native/profile/authority/decoder admission before production execution.

## Planned fixture expansion

Add separate original-model fixtures for optional/nullable properties, exact numeric tokens, native row scalar roots, recursive values, typed endpoints and ordered/composite keys after their original profiles and supported compiler subsets are reconciled. Expected presence/values/refusals must be authored independently. Do not label the current one-field packet as those tests or use compiler-generated expectations as their oracle.
