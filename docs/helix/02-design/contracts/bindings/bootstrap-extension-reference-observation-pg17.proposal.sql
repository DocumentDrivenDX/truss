-- Unexecuted incoming extension-reference collection; $1 original extension oid[] <=256.
-- Keep all dependency kinds; membership classification is a separate native meaning.
SELECT d.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       pg_catalog.to_jsonb(d)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_depend AS d
WHERE d.refclassid = 'pg_catalog.pg_extension'::pg_catalog.regclass
  AND d.refobjid = ANY ($1::pg_catalog.oid[])
ORDER BY d.refobjid, d.classid, d.objid, d.objsubid, d.refobjsubid, d.deptype;
