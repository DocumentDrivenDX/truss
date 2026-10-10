-- Unexecuted default-privilege observation; $1 namespace oid, $2 original owner oid[] <=256.
-- Include all namespace entries and global creation defaults of reached owners.
SELECT a.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       a.oid::pg_catalog.text AS object_oid,
       a.defaclacl::pg_catalog.text AS defaclacl_native_text,
       pg_catalog.array_dims(a.defaclacl) AS defaclacl_native_dimensions,
       pg_catalog.to_jsonb(a)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_default_acl AS a
WHERE a.defaclnamespace = $1::pg_catalog.oid
   OR (a.defaclnamespace = 0 AND a.defaclrole = ANY ($2::pg_catalog.oid[]))
ORDER BY a.oid;
