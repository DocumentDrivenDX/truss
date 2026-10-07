-- Unexecuted PG17 option collector; source parsing is not permission to execute.
-- Host must admit exact field/object/principal/sink/lifetime disclosure first.
-- Potential secret content; no whole-row JSON and no callback/foreign access.
SELECT c.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       c.ftrelid::pg_catalog.text AS original_object_oid,
       c.ftoptions::pg_catalog.text AS options_native_text,
       pg_catalog.array_dims(c.ftoptions) AS options_native_dimensions
FROM pg_catalog.pg_foreign_table AS c
WHERE c.ftrelid = ANY($1::pg_catalog.oid[])
ORDER BY c.ftrelid;
