-- Unexecuted PG17 declaration header. Options deliberately unselected, not NULL.
-- Original admitted unique nonnull 1D oid batch, lower bound 1, 1..256 items.
-- Host admits original field disclosure/cut/work bounds before sending this query.
SELECT c.tableoid::pg_catalog.text AS adjunct_catalog_class_oid,
       c.ftrelid::pg_catalog.text AS relation_oid,
       c.ftserver::pg_catalog.text AS server_oid
FROM pg_catalog.pg_foreign_table AS c
WHERE c.ftrelid = ANY($1::pg_catalog.oid[])
ORDER BY c.ftrelid;
