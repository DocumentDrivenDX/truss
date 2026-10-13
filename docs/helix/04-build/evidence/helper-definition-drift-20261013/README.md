# Committed helper owner and definition drift — 2026-10-13

Four actual PostgreSQL18.6 controls pass on Truss0.53-candidate:4/24.831s.
ALTER FUNCTION changes current-helper owner to the excluded postgres owner,
changes SECURITY DEFINER to INVOKER, changes context-helper search_path, or
changes current-helper VOLATILE to STABLE. Each change is committed before the
caller's READ COMMITTED operation and the executor is freshly adopted. Original
event triggers remain on. Each requires the exact helper snapshot primary,
zero encoding, no publication and contained custody without cleanup error.
The current verifier implementation already rejects these changes; these tests
add concrete native execution evidence, not a newly discovered bypass.

The actual external TLS peer also sees committed owner-change denial: exact
503{} after unknown-bearer401, then reuse403; the service checks the exact native
snapshot cause and zero encoding. Its SQL probe is denied. All three owned
resources are confirmed absent. The original positive mode still returns r1
with salary Withheld, original consumer and both source cuts before wire, one
operation and denied reuse/SQL. A first fixture CLI syntax error prevented
startup; its failed packet and complete owned cleanup are retained separately.
It is not a native drift counterexample or passing control.

Only the trusted test owner may select this mutation. All three mutation flags
must be exact Booleans and at most one true. Service and runner accept the same
four exact CLI choices. The owner change also rewrites native ACL ownership;
the exact snapshot primary precedes the ACL check and isolates the intended
owner mismatch. The inherited native fixture teardown completes for the four
unittest controls; no separate cleanup receipt was retained for that run. The
external fixture separately checks native cleanup and resource absence.

Trace US-056AC9, US-057AC7 and SPIKE-004 CH04/CH05/CH08 prerequisites. These
controls do not establish full ownership/role/handler/DDL lifetime, inherited
role closure, all routine semantics or truss.B11 admission. No backend case is
promoted. Existing shared policy and direct-ACL conditional formal evidence are
unchanged; no new native or formal-refinement theorem is asserted. Source-built
Weft, fixture certificate identity/issuer and service-private local PostgreSQL
premises remain those qualified by the preceding external-peer evidence.
