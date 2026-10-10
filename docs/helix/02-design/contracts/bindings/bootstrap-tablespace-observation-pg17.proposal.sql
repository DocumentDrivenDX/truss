-- Unexecuted original shared pg_tablespace OID lookup; unique nonnull 1D array <=256.
-- No filesystem location function, mutation or credential/configuration discovery.
SELECT s.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       s.oid::pg_catalog.text AS object_oid,
       s.spcowner::pg_catalog.text AS owner_oid,
       s.spcacl::pg_catalog.text AS acl_native_text,
       pg_catalog.array_dims(s.spcacl) AS acl_native_dimensions,
       s.spcoptions::pg_catalog.text AS options_native_text,
       pg_catalog.array_dims(s.spcoptions) AS options_native_dimensions,
       pg_catalog.to_jsonb(s)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_tablespace AS s
WHERE s.oid = ANY($1::pg_catalog.oid[])
ORDER BY s.oid;
