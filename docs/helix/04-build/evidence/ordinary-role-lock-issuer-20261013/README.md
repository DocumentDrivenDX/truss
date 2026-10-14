# Fixed native role-lock issuer

The original SQL defines a no-argument SECURITY DEFINER routine with pinned search_path and only the two qualified SHARE NOWAIT locks. PUBLIC execution is revoked in the same installation transaction. The PostgreSQL18.6 native test grants one ordinary caller execution, confirms no UPDATE privilege on either catalog, confirms two held locks, blocks independent privilege/membership writers, refuses an ungranted caller and verifies rollback release.

Production installation must pin a trusted privileged owner and exact routine/ACL before granting only the private executor. Do not grant role-catalog writes or general caller access. This primitive uses cluster-wide locks; its installer, owner/callable lifetime and integration into the ordinary executor remain open. The existing role-fenced producer still acquires direct privileged locks.
