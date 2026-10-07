-- Unexecuted PG17 operator frontier; unique original class/subobject-zero oid[] <=256.
-- No namespace/name filter; complete closure and native meaning separately admitted.
SELECT o.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       o.oid::pg_catalog.text AS object_oid,
       o.oprnamespace::pg_catalog.text AS namespace_oid,
       o.oprcode::pg_catalog.oid::pg_catalog.text AS oprcode_oid,
       o.oprrest::pg_catalog.oid::pg_catalog.text AS oprrest_oid,
       o.oprjoin::pg_catalog.oid::pg_catalog.text AS oprjoin_oid,
       pg_catalog.to_jsonb(o)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_operator AS o
WHERE o.oid = ANY($1::pg_catalog.oid[])
ORDER BY o.oid;
