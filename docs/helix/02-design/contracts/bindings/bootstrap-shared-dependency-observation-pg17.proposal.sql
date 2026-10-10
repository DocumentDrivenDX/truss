-- Raw PG17 outgoing shared dependencies for admitted exact dependent addresses.
-- $1 database oid[], $2 catalog oid[], $3 object oid[], $4 subobject int4[].
-- Validate aligned nonnull one-dimensional arrays/no nulls before execution.
-- Admit only observed current database addresses or explicit shared-object dbid 0.
WITH frontier AS (
  SELECT f.dbid, f.classid, f.objid, f.objsubid
  FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                  pg_catalog.unnest($2::pg_catalog.oid[]),
                  pg_catalog.unnest($3::pg_catalog.oid[]),
                  pg_catalog.unnest($4::pg_catalog.int4[]))
       AS f(dbid, classid, objid, objsubid)
)
SELECT d.dbid::text AS dependent_database_oid,
       d.classid::text AS dependent_class_oid,
       d.objid::text AS dependent_object_oid,
       d.objsubid::text AS dependent_subobject,
       d.refclassid::text AS referenced_shared_class_oid,
       d.refobjid::text AS referenced_shared_object_oid,
       d.deptype::text AS dependency_kind,
       pg_catalog.to_jsonb(d)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_shdepend AS d
WHERE EXISTS (
  SELECT 1 FROM frontier AS f
  WHERE f.dbid = d.dbid AND f.classid = d.classid
    AND f.objid = d.objid AND f.objsubid = d.objsubid
)
ORDER BY d.dbid, d.classid, d.objid, d.objsubid,
         d.refclassid, d.refobjid, d.deptype;
-- Shared referenced identities have no fabricated referenced column ordinal.
-- No incoming all-database role-use scan or policy inference from missing edges.
