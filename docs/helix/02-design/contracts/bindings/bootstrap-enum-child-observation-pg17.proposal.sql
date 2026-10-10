-- Unexecuted PG17 original admitted reference batch; unique nonnull 1D oid[] <=256.
-- Input is actual pg_enum child identity, never parent pg_type identity.
-- No namespace restriction; complete scope/cut/transport/resource admission required.
SELECT e.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       e.oid::pg_catalog.text AS object_oid,
       e.enumtypid::pg_catalog.text AS enum_type_oid,
       e.enumsortorder::pg_catalog.text AS sort_order_native_text,
       pg_catalog.encode(pg_catalog.float4send(e.enumsortorder),'hex') AS sort_order_float4_send_hex,
       pg_catalog.to_jsonb(e)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_enum AS e
WHERE e.oid = ANY($1::pg_catalog.oid[])
ORDER BY e.oid;
