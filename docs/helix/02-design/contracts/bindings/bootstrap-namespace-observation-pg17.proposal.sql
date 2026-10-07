-- Unexecuted PostgreSQL 17 namespace observation proposal.
-- $1: original admitted unique nonnull one-dimensional namespace oid[] <=256.
-- Includes deployment namespace and every reached lookup/definition namespace.
SELECT n.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       n.oid::pg_catalog.text AS object_oid,
       n.nspowner::pg_catalog.text AS owner_oid,
       n.nspacl::pg_catalog.text AS nspacl_native_text,
       pg_catalog.array_dims(n.nspacl) AS nspacl_native_dimensions,
       pg_catalog.to_jsonb(n)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_namespace AS n
WHERE n.oid = ANY($1::pg_catalog.oid[])
ORDER BY n.oid;
