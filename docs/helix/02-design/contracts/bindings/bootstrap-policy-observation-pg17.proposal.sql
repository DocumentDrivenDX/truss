-- Unexecuted PostgreSQL 17 raw namespace observation; $1 is admitted namespace OID.
-- Include internal/unexpected rows; no expected-name or enablement filter.
SELECT x.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       x.oid::pg_catalog.text AS object_oid,
       x.polrelid::pg_catalog.text AS relation_oid,
       x.polqual::pg_catalog.text AS using_native_tree,
       x.polwithcheck::pg_catalog.text AS check_native_tree,
       CASE WHEN x.polqual IS NULL THEN NULL::pg_catalog.text
            ELSE pg_catalog.pg_get_expr(x.polqual,x.polrelid,false) END AS using_deparsed_sql,
       CASE WHEN x.polwithcheck IS NULL THEN NULL::pg_catalog.text
            ELSE pg_catalog.pg_get_expr(x.polwithcheck,x.polrelid,false) END AS check_deparsed_sql,
       x.polroles::pg_catalog.text AS polroles_native_text,
       pg_catalog.array_dims(x.polroles) AS polroles_native_dimensions,
       pg_catalog.to_jsonb(x)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_policy AS x
WHERE EXISTS (SELECT 1 FROM pg_catalog.pg_class AS c
              WHERE c.oid = x.polrelid AND c.relnamespace = $1::pg_catalog.oid)
ORDER BY x.oid;
