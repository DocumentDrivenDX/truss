# Exact direct helper ACL admission — 2026-10-13

The original catalog helper verifier compared owners and routine definitions but
omitted ACLs. A committed PUBLIC EXECUTE grant before admission yielded an actual
Ok masked packet under the exact previous verifier. The retained baseline runner
extracts only _verify_helpers from git2010d1da's original source, executing it in
the original current native pipeline. helper-acl-committed-before.log records
that meaningful counterexample. The first before/after attempts left the grant
uncommitted; those logs are setup history and do not establish published drift.

The private verifier now obtains the original SESSION_USER's native role OID
and compares each exact helper's complete direct ACL: non-login ordinary owner
and original caller each have EXECUTE, issued by that owner, without explicit
grant option. Native TEXT descriptors and bounded complete row comparison are
required. PUBLIC, extra/missing rows, delegation and wrong grantor refuse.
Default NULL ACL expands through native acldefault, exposing PUBLIC and refusing.
Both existing verifier calls enforce this before Subject encoding and again
before publication. This is an exact fixture direct-grant profile; inherited
privileges, owner implicit rights and complete role/authority closure are separate.

Actual PostgreSQL18.6 controls pass for committed PUBLIC grants on both helpers,
caller grant option, missing caller EXECUTE and another role's EXECUTE. Each
requires exact ACL primary, contained custody, no cleanup error, no encoding and
no publication. Together with the two original TLS tests:7/77.081 seconds. A
separate late committed grant from an excluded administrative connection with
its own event triggers disabled is detected by the final comparator:1/11.700
seconds, no publication. Original executor event triggers remain on.

An actual external Linux TLS peer observes the committed PUBLIC-grant refusal:
unknown bearer401, admitted503{}, replay403, no native diagnostic, zero encoding
and denied SQL TCP probe. All three nonce-owned resources are confirmed absent.
Positive external read still returns only r1 with salary Withheld and native
consumer/both source cuts before wire; all resources removed. Runtime0.52 and
source-built Weft candidate/private-local-database premises remain qualified by
the earlier Linux and external-peer evidence; no production issuer is admitted.

Z3 4.15.4 yields three UNSAT and two SAT over exact direct ACL set equality:
accepted equality excludes unexpected rows, missing caller EXECUTE and PUBLIC;
positive equality is satisfiable, while checking only the two intended grants
allows an additional PUBLIC grant. This conditional abstract theorem assumes
faithful native capture and atomic equality. It does not prove the SQL query,
PostgreSQL role membership, concurrent lifetime or native refinement.

Trace US-056AC9/US-057AC7, SPIKE-004 CH04/CH05/CH08. This closes a selected helper
snapshot gap, not truss.B11 or the remaining132-case admission gate. Complete
owner/grant/membership/routine/policy/column mapping drift, inherited authority,
DDL/admin lifetime and other backend cases remain required.
