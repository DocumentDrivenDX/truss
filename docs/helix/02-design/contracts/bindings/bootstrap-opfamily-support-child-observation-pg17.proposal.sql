-- Unexecuted PG17 family-member inventory; original unique nonnull 1D member oid[] <=256.
-- Resolve specific original member rows; their actual family schedules complete sibling collection.
-- Input cardinality does not bound member rows or materialization; shared budgets apply.
SELECT o.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       o.oid::pg_catalog.text AS object_oid,
       o.amprocfamily::pg_catalog.text AS family_oid,
       o.amproc::pg_catalog.oid::pg_catalog.text AS support_routine_oid,
       pg_catalog.to_jsonb(o)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_amproc AS o
WHERE o.oid = ANY($1::pg_catalog.oid[])
ORDER BY o.oid;
