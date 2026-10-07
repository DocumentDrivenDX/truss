-- Unexecuted PostgreSQL 17 raw observation; $1 is original admitted namespace OID.
-- No expected-name/kind filter; complete native cut/transport/resource qualification required.
SELECT e.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       e.oid::pg_catalog.text AS object_oid,
       e.enumtypid::pg_catalog.text AS enum_type_oid,
       pg_catalog.encode(pg_catalog.float4send(e.enumsortorder),'hex') AS sort_order_float4_send_hex,
       pg_catalog.to_jsonb(e)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_enum AS e
WHERE EXISTS (SELECT 1 FROM pg_catalog.pg_type AS t
              WHERE t.typnamespace = $1::pg_catalog.oid AND t.oid = e.enumtypid)
ORDER BY e.oid;
