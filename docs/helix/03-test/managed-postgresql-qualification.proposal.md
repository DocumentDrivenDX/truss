# Managed PostgreSQL qualification — candidate 0.1

Authority: the selected local deployment contract, installation/migration plan,
CONTRACT-008/011 and complete consumer STP-040–044. Aurora and Lakebase remain
independent P4 targets. This defines additional managed qualification schedules;
no service was provisioned, queried or qualified by this review.

## Provider constraints reviewed 2026-10-10

[Lakebase compatibility](https://docs.databricks.com/aws/en/oltp/projects/compatibility)
documents loss of unlogged data on compute restart/scale-to-zero, idle connection
closure with lost session state, restricted superuser/filesystem access and no
native PostgreSQL logical replication. These constraints affect deployment;
they do not alter Truss's durable receipt or original-custody contracts.

[Lakebase's extension inventory](https://docs.databricks.com/aws/en/oltp/projects/extensions)
lists `vector` separately from search-enabled `lakebase_vector`.
[Aurora's versioned extension inventory](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html)
lists pgvector availability by engine version. Availability documentation alone
does not admit an installed version, privileges or semantic equivalence. No
vector extension is added to Truss's required runtime by this review.

## Independent managed schedules

Freeze the actual account/project, region, service variant, engine/build, settings,
roles, driver/transport and complete installation/security/resource tuple. Bind
provider identity through the existing target-admission procedure; matching names
or version numbers cannot supply it. Use real installed public operations and
independent full graph/history/receipt/feed observations, never administrative
component fixtures as the service acceptance oracle.

| Case | Required schedule and observation |
| --- | --- |
| MP-01 durable homes | Commit populated graph, journal, receipts, feed and recovery records; restart compute and compare full inventories. Temporary/unlogged homes cannot carry promised durability. |
| MP-02 ended sessions | Close the original live connection during adopted work or staged reads. Refuse further disclosure/admission; retain uncertain custody. A replacement connection cannot revive old leases, issuers or snapshots. |
| MP-03 managed privileges | Install and operate under actual available administrative/ordinary roles; verify denied bypass and observer rights. Do not inherit local superuser evidence. |
| MP-04 feed independence | Run durable replica/ACK restart cases through Truss's complete feed. Native replication or LISTEN notifications cannot substitute for complete membership and recovery. |
| MP-05 settings and instrumentation | Observe actual enforceable settings, timing and complete native outcomes. Missing server-log access cannot turn a timeout or absent response into confirmed rollback. |
| MP-06 extension correspondence | For every actually required extension, verify exact available/installed version, complete dependency/callable inventory and ordinary-role behavior. A compatible replacement needs explicit separate admission. |

These schedules are Truss's proposed responses to provider restrictions, not
claims that the provider guarantees Truss behavior. Repeat applicable cases on
Aurora under its own exact tuple; Lakebase documentation cannot qualify Aurora.
All cases are `not_run`. Unsupported role, setting or observability requirements
leave the dependent capability unavailable; no retry loop, automatic weakening,
new pool requirement or hidden installation step is selected here.
