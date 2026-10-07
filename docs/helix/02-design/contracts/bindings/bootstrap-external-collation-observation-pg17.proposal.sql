-- Unexecuted PG17 original admitted reference batch; unique nonnull 1D oid[] <=256.
-- Range/enum input is actual pg_type identity; collation input actual pg_collation.
-- No namespace restriction; complete scope/cut/transport/resource admission required.
SELECT x.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       x.oid::pg_catalog.text AS object_oid,
       x.collnamespace::pg_catalog.text AS namespace_oid,
       pg_catalog.to_jsonb(x)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_collation AS x
WHERE x.oid = ANY($1::pg_catalog.oid[])
ORDER BY x.oid;
