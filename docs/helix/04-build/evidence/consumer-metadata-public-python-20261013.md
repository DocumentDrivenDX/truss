# Original consumer metadata and public Python workflow — 2026-10-13

Runtime 0.32-candidate retains owner-produced vocabulary/extension artifacts and warned module actions without interpreting them. The original consumer model and SQL remain unchanged. Required core interpretation is still mandatory. Correspondence checks bind retained report content to original preparation bytes; they do not authenticate execution of the UMF producer.

Tested tuple: DocumentDrivenDX pgserver-pg18 18.6.1 / PostgreSQL18.6 / psycopg3.3.6 binary/libpq18.6, Weft backend0.4.5.

Installed wheel SHA256: `4bef292054c982c81505fca9caf7c22f5a90aa6d2b9e0a8476920d73b8cd2518`. Weft extension SHA256: `7885b7e9fdec56f6e5d3c25b9f0c7adef2887ed307f9f35992ed7a88be447ebf`.

Basic native checks: four tests passed (30.541s): original consumer authority reads, real .31→.32 upgrade, portable basic workflow and exact scalar workflow. Legacy .31 public mutation/filter/count/read-only query passed with the new extension (6.722s). Contract typing passed five fixtures/twenty expected negative errors; module boundaries passed873 imports; SQL-owner roundtrips passed21 fixtures. Astra Ultra reviewed the plan and implementation and found no remaining scoped functional blocker.

The original consumer adapter registers original bytes, writes fixtures through public groups, commits and replays, checks reached in a fresh read-only transaction, then executes unchanged SQL and expectations. Four extension occurrences and original partial diagnostics are retained. Only two authority read cases are exercised; replicas are explicitly unavailable. This is not a full41-case or independent-interchange claim. The public preview0.6 retains the earlier preview corpora unchanged.

Latest security changes are integrated separately; protected security activation remains unavailable. The full implementation goal remains open.
