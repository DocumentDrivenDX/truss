-- Unexecuted restricted option source; not permission to read sensitive content.
-- $1 is an admitted unique nonnull nonzero mapping-oid[] batch, 1D/lower1/1..256.
-- Exact field/object/principal/sink/lifetime authority precedes materialization.
SELECT c.tableoid::pg_catalog.text AS catalog_class_oid,
       c.oid::pg_catalog.text AS mapping_oid,
       c.umoptions::pg_catalog.text AS options_native_text,
       pg_catalog.array_dims(c.umoptions) AS options_native_dimensions
FROM pg_catalog.pg_user_mapping AS c
WHERE c.oid = ANY($1::pg_catalog.oid[])
ORDER BY c.oid;
