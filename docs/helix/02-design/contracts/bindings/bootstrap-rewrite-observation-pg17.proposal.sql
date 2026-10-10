-- Unexecuted PostgreSQL 17 raw namespace observation; $1 is admitted namespace OID.
-- Include internal/unexpected rows; no expected-name or enablement filter.
SELECT x.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       x.oid::pg_catalog.text AS object_oid,
       x.ev_class::pg_catalog.text AS relation_oid,
       pg_catalog.to_jsonb(x)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_rewrite AS x
WHERE EXISTS (SELECT 1 FROM pg_catalog.pg_class AS c
              WHERE c.oid = x.ev_class AND c.relnamespace = $1::pg_catalog.oid)
ORDER BY x.oid;
