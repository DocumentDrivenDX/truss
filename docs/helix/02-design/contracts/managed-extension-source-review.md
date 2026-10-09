# Managed extension source review

Read-only documentation review, 2026-10-07. No provider account, database installation or native test was accessed. The owner requires any selected extension to ship with RDS PostgreSQL, Aurora PostgreSQL and Lakebase.

RDS publishes versioned [extension matrices](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html). Aurora separately publishes its [supported extensions by engine version](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html). Both list pg_stat_statements. These are availability sources, not evidence for Truss's native cumulative-account interfaces or a selected build/deployment tuple.

Databricks publishes [Lakebase extension tables](https://docs.databricks.com/aws/en/oltp/projects/extensions), including pg_stat_statements and plpgsql. Exact Lakebase product/major-version selection and extension versions still need pinning; the table does not qualify Truss's account protocol or custom module deployment.

PostgreSQL 17's [pg_stat_statements documentation](https://www.postgresql.org/docs/17/pgstatstatements.html) describes statistics collection, with planning/execution statistics updated at the respective phase end only for successful operations. Consequently, **our inference** is that this documented telemetry alone cannot establish charge-before-error, rollback-resistant original transaction spend or pre-materialization admission required by the native account proposal. Listing this common extension does not close the resource-account design.

No shipped extension implementing the complete Truss account contract has been identified or qualified in this review. This is not an exhaustive proof that none exists. Native C/Rust account packaging remains unselected; do not assume provider support for an arbitrary custom module. Preserve the [FR-43 reconciliation](resource-account-requirement-reconciliation.md) and select exact language/entrypoint/epoch/account/security/deployment evidence before adoption. SQL/protected PL/pgSQL producer planning can continue where its required semantics are explicit, without claiming that ordinary transactional rows preserve spent counters across rollback.


## Selected standard PostgreSQL orchestration languages after the resource decision

The owner-selected controlled-work scope removes a universal rollback-resistant account extension from the required default. The architecture now selects SQL for fixed relational observations and PL/pgSQL for protected writer orchestration, trigger handlers and complete-scope validators. This closes the orchestration-language choice; it does not adopt a complete native profile or select every codec/resource helper implementation. RDS's [versioned extension matrix](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html), Aurora's [extension matrix](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html) and Lakebase's [extension tables](https://docs.databricks.com/aws/en/oltp/projects/extensions) all list plpgsql. Exact service product/major/minor/build, installed language version and administrative creation/ownership privileges still require selection and native observation.

PostgreSQL 17 documents [sha256(bytea) as a binary-string function](https://www.postgresql.org/docs/17/functions-binarystring.html). Current key and request-receipt generated columns already call pg_catalog.sha256. Their source therefore does not require the separate pgcrypto digest API. Do not add pgcrypto merely to implement these existing SHA-256 routes, or turn a matching digest into full-input equality authority. Qualify the actual builtin overload/type/dependency and forced full-byte collision behavior under the chosen server tuple.

| Required boundary | Recommended routine realization | Meaning that still needs exact design/qualification |
| --- | --- | --- |
| Fixed original observation | SQL with exact descriptor/parameter custody | Native type/format/visibility, bounded transport and complete original result |
| Five trigger handlers | Protected PL/pgSQL trigger functions using actual trigger context | OLD/NEW attribution, complete operation collection, private registry custody and unavoidable event coverage |
| Two complete-scope validators | Ordinary private PL/pgSQL functions returning void | Write-free independent recomputation, full scope admission, original codec/event parity and finite controlled work |
| Mutation/acceptance/receipt producers | Protected PL/pgSQL entrypoints over the selected stores | Ordered locks, complete atomic effects, exact input/result/event/report encoding and trusted caller/commit/clock evidence |
| Toolkit conversion/validation | Portable TypeScript with pinned UMF primitives | Charge bounded token/tree/conversion work before processing; preserve unknown/source meaning |

SQL/PL/pgSQL availability is sufficient to continue authoring these bodies and their original inventories. It does not establish that every existing algorithm can be safely implemented without another dependency. If a required primitive remains unsupported, record the precise affected boundary and refuse that capability rather than assume a custom module or weaken graph integrity. Do not require pg_tle, PL/v8, PL/Python, C/Rust native libraries or pg_stat_statements as default correctness dependencies without separate selected need and all-target evidence. Optional telemetry is outside correctness admission.

The candidate keeps persistent row/byte capacity admission and protected transaction effects separate from toolkit-owned cumulative attempt accounting. Ordinary transactional ledger rows do not become rollback-resistant spent-work evidence. Cancellation, native memory/work, commit observation and managed-service privilege restrictions remain individually qualified; a language choice cannot close those claims. Exact native codec/collector/body/security/driver composition and all native fault schedules remain open.

## Managed-service lifecycle handoff refresh — 2026-10-08

Fresh [Lakebase compatibility documentation](https://docs.databricks.com/aws/en/oltp/projects/compatibility)
reports connection/session loss on scale-to-zero, nonpersistent unlogged
tables across compute restart, loss of cumulative statistics, restricted
parameter contexts and no native PostgreSQL logical replication. Its current
[extension table](https://docs.databricks.com/aws/en/oltp/projects/extensions)
lists plpgsql and pg_stat_statements. Aurora's
[engine-version matrix](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html)
also lists plpgsql. These are documentation observations, not installed Truss
qualification.

Truss implementation implications: durable receipt/feed/archive/recovery
custody stays in logged original stores; session locks, temporary state and
telemetry cannot serve as durable proof. Selected leases must observe original
connection termination and invalidate cached session custody before reuse.
The complete feed remains Truss's SQL protocol, with durable replica/ACK
semantics; no native logical-replication dependency is introduced. Qualify
restart/scale-to-zero fault schedules and actual configurable settings before
managed-service support. Treat session/statistics loss as evidence invalidation,
not a zero-work or no-change observation. Exact product/version/roles/pooling
and operational settings remain separately selected deployment outputs.
