# Atomic owned import — 2026-10-16

Explicit owned input uses the existing group executor once, with original indexed
source attachments inside the same host operation/savepoint. Legacy input keeps
its original per-record behavior. No release or performance claim is made.

- Basic public PG18.6 workflows: 6 PASS /19.722s, including engine-owned atomic
  commit and real published SDK37 upgrade without access reconfiguration.
- Original per-record host/engine workflows: 4 PASS /12.077s.
- Second source attachment fault: 1 PASS /4.154s; SQLSTATE P9999 confirms the
  intended trigger was reached, all aggregate/source/attempt rows rolled back,
  and caller work before the operation survived.
- Runtime source recipe:222 routines; Python module boundaries:1532 imports.

Astra Ultra focused re-review cleared both blockers:222-routine inventory and
explicit upgrade grants after owner-only custody checks, preserving PUBLIC
revocation. Its source clearance excludes performance/release qualification.
The initial native parser failure is retained and corrected by parenthesizing
CASE in the source predicate. Current native logs use Python3.11.17,
psycopg3.3.6, pgserver-pg18 18.6.1/PostgreSQL18.6 and Bun1.4.2.
