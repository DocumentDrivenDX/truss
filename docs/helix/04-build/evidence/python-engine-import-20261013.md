# Engine import and diagnostic correspondence — 2026-10-13

SDK0.0.14/native0.51/layout0.16 pairs with Weft0.4.16/backend0.4.21.
`run_import_batches` owns a private connection and one-record transactions,
retaining the full-input index space and global objects-before-edges order.
Acknowledged settlements precede cleanup; COMMIT uncertainty is never relabeled
as rollback. Existing host-owned imports are unchanged. Reports require current
installation/source epoch/authorized scope and available disclosure machinery;
report absence does not prove absence of effects. Command witness hashes are
not receipt tokens. Repetition uses identity policy, not original report replay.

Installed-wheel engine tests cover create/skip/reject, empty input and a real
PostgreSQL deferred23514 second-batch COMMIT rejection after an earlier commit.
Both engine and two existing host import workflows passed in the six-test run
(113.928s); its legacy diagnostic fixture count assertion was corrected to the
complete original producer tape. Paired UMF0.7/0.8 diagnostic workflows then pass
2/24.830s, retaining exact source/opaque extensions and exact scalar writes,
reads and queries. Populated native0.50→0.51 upgrade passes1/11.022s.

Focused engine module typing and950-import boundaries pass. Astra Ultra reviewed
plan/source and settlement/disclosure fixes. No broad conformance, managed-server
or independent implementation claim. Basic defaults remain stock PostgreSQL
logical bounds and deadlines; no custom metrics/tracing are introduced.
