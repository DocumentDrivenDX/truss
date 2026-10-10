-- Unexecuted PG17 original pg_cast address frontier; unique nonnull 1D oid[] <=256.
-- No namespace/context/method filter; absence does not prove no conversion path.
SELECT o.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       o.oid::pg_catalog.text AS object_oid,
       pg_catalog.to_jsonb(o)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_cast AS o
WHERE o.oid = ANY($1::pg_catalog.oid[])
ORDER BY o.oid;
