# PostgreSQL role catalog lock feasibility

On PostgreSQL18.6, SHARE locks on both pg_authid and pg_auth_members block independent ALTER ROLE BYPASSRLS and role GRANT with55P03. Each individual lock leaves the other writer path open. After rollback, both independent writes commit with exact flag/membership readback. Ordinary LOGIN lock acquisition refuses42501. The owned temporary cluster is removed on exit.

Integration must acquire both catalog locks before reading role authority and retain them through receiver completion and transaction settlement. These are cluster-wide locks; a privileged isolated lock issuer and its callable/owner closure require design and admission. Do not grant ordinary callers general catalog mutation rights. The current comparison-only producer does not yet acquire this cut. Superuser/OS administrators remain outside the selected ordinary-role boundary; catalog locking does not prove ABA protection, all role/config writes, or backend acceptance.
