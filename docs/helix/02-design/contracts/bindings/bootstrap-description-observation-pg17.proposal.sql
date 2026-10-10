-- Unexecuted object-scoped comment lookup; equal-length original class/object oid[] <=256.
-- Inputs are unique nonnull one-dimensional pairs; includes all subobject comments.
-- This object scope is distinct from exact subobject dependency-frontier matching.
WITH objects AS (
 SELECT f.classid, f.objid
 FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                 pg_catalog.unnest($2::pg_catalog.oid[])) AS f(classid,objid)
)
SELECT d.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       pg_catalog.to_jsonb(d)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_description AS d
WHERE EXISTS (SELECT 1 FROM objects AS f WHERE f.classid = d.classoid AND f.objid = d.objoid)
ORDER BY d.classoid, d.objoid, d.objsubid;
