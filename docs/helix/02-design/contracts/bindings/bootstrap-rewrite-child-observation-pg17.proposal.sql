-- Unexecuted PG17 original admitted specific child batch; unique nonnull 1D oid[] <=256.
-- Resolve exact original child rows, then collect complete original parent fanout.
-- Actual parent/cut/full coverage/transport/resource interpretation remains required.
SELECT x.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       x.oid::pg_catalog.text AS object_oid,
       x.ev_class::pg_catalog.text AS relation_oid,
       pg_catalog.to_jsonb(x)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_rewrite AS x
WHERE x.oid = ANY($1::pg_catalog.oid[])
ORDER BY x.oid;
