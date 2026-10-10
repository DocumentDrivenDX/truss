-- Unexecuted PG17 original admitted reference batch; unique nonnull 1D oid[] <=256.
-- Range/enum input is actual pg_type identity; collation input actual pg_collation.
-- No namespace restriction; complete scope/cut/transport/resource admission required.
SELECT r.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       r.rngtypid::pg_catalog.text AS range_type_oid,
       r.rngmultitypid::pg_catalog.text AS multirange_type_oid,
       r.rngcanonical::pg_catalog.oid::pg_catalog.text AS rngcanonical_oid,
       r.rngsubdiff::pg_catalog.oid::pg_catalog.text AS rngsubdiff_oid,
       pg_catalog.to_jsonb(r)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_range AS r
WHERE r.rngtypid = ANY($1::pg_catalog.oid[])
   OR r.rngmultitypid = ANY($1::pg_catalog.oid[])
ORDER BY r.rngtypid;
