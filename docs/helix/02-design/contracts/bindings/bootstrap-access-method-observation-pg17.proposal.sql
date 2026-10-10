-- Unexecuted PG17 access-method frontier; unique original class/subobject-zero oid[] <=256.
-- No namespace/name filter; complete closure and native meaning separately admitted.
SELECT o.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       o.oid::pg_catalog.text AS object_oid,
       o.amhandler::pg_catalog.oid::pg_catalog.text AS amhandler_oid,
       pg_catalog.to_jsonb(o)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_am AS o
WHERE o.oid = ANY($1::pg_catalog.oid[])
ORDER BY o.oid;
