-- Unexecuted PostgreSQL 17 raw observation; $1 is original admitted namespace OID.
-- No expected-name/kind filter; complete native cut/transport/resource qualification required.
SELECT r.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       r.rngtypid::pg_catalog.text AS range_type_oid,
       r.rngmultitypid::pg_catalog.text AS multirange_type_oid,
       r.rngcanonical::pg_catalog.oid::pg_catalog.text AS rngcanonical_oid,
       r.rngsubdiff::pg_catalog.oid::pg_catalog.text AS rngsubdiff_oid,
       pg_catalog.to_jsonb(r)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_range AS r
WHERE EXISTS (SELECT 1 FROM pg_catalog.pg_type AS t
              WHERE t.typnamespace = $1::pg_catalog.oid
                AND (t.oid = r.rngtypid OR t.oid = r.rngmultitypid))
ORDER BY r.rngtypid;
