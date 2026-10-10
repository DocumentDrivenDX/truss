-- Unexecuted original transform address lookup; unique nonnull 1D oid[] <=256.
SELECT t.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       t.oid::pg_catalog.text AS object_oid,
       t.trftype::pg_catalog.text AS type_oid,
       t.trflang::pg_catalog.text AS language_oid,
       t.trffromsql::pg_catalog.oid::pg_catalog.text AS from_sql_routine_oid,
       t.trftosql::pg_catalog.oid::pg_catalog.text AS to_sql_routine_oid,
       pg_catalog.to_jsonb(t)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_transform AS t
WHERE t.oid = ANY($1::pg_catalog.oid[])
ORDER BY t.oid;
