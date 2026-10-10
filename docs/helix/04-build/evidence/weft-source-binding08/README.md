# Layout 0.8 source binding review packet

This separate packet preserves the earlier 0.4 packet unchanged. It contains original logical UMF 0.7.0 fixture bytes, full original definitions, concrete nested home/value/presence/codec/read-context definitions, actual layout 0.8 SQL and the complete 40-table/386-column declaration map. Synthetic type/property IDs are 17/23. Physical identities use the source-only review08 namespace; they are not installed runtime IDs.

The single required string fixture demonstrates review grammar/source correspondence. Keys, relationships, nullable/numeric/tree operations, accepted catalog, native installation and registered backend adoption remain unqualified. Unregistered fixture execution must refuse before SQL. Layout/profile hashes are distinct from the 0.4 packet; no cross-version compatibility is inferred.

Reproduce from the main checkout:

```sh
python3 docs/helix/04-build/evidence/design-audit/build-weft-source-binding08.py
python3 docs/helix/04-build/evidence/design-audit/check-weft-source-binding08.py
bun docs/helix/04-build/evidence/design-audit/check-weft-source-binding08.ts /private/tmp/weft-build/node_modules/ajv/dist/2020.js
python3 docs/helix/04-build/evidence/design-audit/check-weft-source-binding08-negatives.py
```

The local Ajv path is a development dependency location, not a published runtime import. integrity-receipt.json pins exact artifact/source/profile closure; negative-receipt.json records damaged payload/profile/model/map refusals. Six schema validations and UMF model admission do not execute the compiler or database. Review requests remain grammar/selector/profile feedback and explicit owner adoption of the exact versioned scope; no cross-chat delivery has occurred.
