-- Unexecuted PG17 effective namespace rights; paired role/schema oid[] <=256.
-- Equal length, unique nonnull one-dimensional original pairs admitted first.
-- Real role OIDs only; no PUBLIC pseudo-role, Cartesian expansion or name lookup.
WITH pairs AS (
 SELECT f.role_oid, f.namespace_oid
 FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                 pg_catalog.unnest($2::pg_catalog.oid[])) AS f(role_oid,namespace_oid)
)
SELECT r.oid::pg_catalog.text AS role_oid,
       n.oid::pg_catalog.text AS namespace_oid,
       pg_catalog.has_schema_privilege(r.oid,n.oid,'CREATE') AS can_create,
       pg_catalog.has_schema_privilege(r.oid,n.oid,'CREATE WITH GRANT OPTION') AS can_grant_create,
       pg_catalog.has_schema_privilege(r.oid,n.oid,'USAGE') AS can_use,
       pg_catalog.has_schema_privilege(r.oid,n.oid,'USAGE WITH GRANT OPTION') AS can_grant_usage
FROM pairs AS f
JOIN pg_catalog.pg_roles AS r ON r.oid = f.role_oid
JOIN pg_catalog.pg_namespace AS n ON n.oid = f.namespace_oid
ORDER BY r.oid,n.oid;
