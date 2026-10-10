-- Unexecuted PG17 current connection database observation, not trusted deployment identity.
SELECT d.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       d.oid::pg_catalog.text AS database_oid,
       d.datname::pg_catalog.text AS database_name,
       d.datdba::pg_catalog.text AS owner_oid,
       d.datacl IS NULL AS original_acl_is_null,
       d.datacl::pg_catalog.text AS original_acl_native_text,
       pg_catalog.array_dims(d.datacl) AS original_acl_native_dimensions,
       pg_catalog.to_jsonb(d)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_database AS d
WHERE d.datname = pg_catalog.current_database()
ORDER BY d.oid;
