# UMF domain-pack schema fixtures

`originals.json.gz` retains the exact UTF-8 ontology bytes for all 21 historical `format: umf` schema entries from DocumentDrivenDX/umf commit `cbb6fb8718aad59fd2061b62d12976387570db2f`. These originals remain unchanged as historical evidence and are not the positive inputs to the current-runtime registration test.

`successors-0.10.0.json.gz` contains the corresponding current ontology documents from the actual producer at DocumentDrivenDX/umf commit `4fc64adf30e2f49eae28162cf476ecd01ce505e3`. Each entry includes its current source path and digest plus the path and digest of its historical predecessor. The 21 current documents are the positive registration inputs. No source datasets are bundled; the 256 TableSpec entries are excluded, including files located under directories named `umf`.

The public registration test verifies the successor bytes and their historical lineage, then covers preparation, acceptance, commit, and idempotent retry. It does not imply mutation or query coverage for every model shape, or support for every valid UMF schema.
