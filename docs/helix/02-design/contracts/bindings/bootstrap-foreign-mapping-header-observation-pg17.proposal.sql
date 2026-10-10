-- Unexecuted restricted PG17 catalog header; original disclosure required.
-- $1 is an admitted unique nonnull nonzero server-oid[] batch, 1D/lower1/1..256.
-- Server batching does not bound mapping fanout; whole-attempt/native bounds apply.
-- No options, whole-row JSON, role name join, redaction or foreign execution.
SELECT c.tableoid::pg_catalog.text AS catalog_class_oid,
       c.oid::pg_catalog.text AS mapping_oid,
       c.umuser::pg_catalog.text AS local_role_oid,
       c.umserver::pg_catalog.text AS server_oid
FROM pg_catalog.pg_user_mapping AS c
WHERE c.umserver = ANY($1::pg_catalog.oid[])
ORDER BY c.umserver, c.oid;
