-- Unexecuted PG17 declaration header. Options deliberately unselected, not NULL.
-- Original admitted unique nonnull 1D oid batch, lower bound 1, 1..256 items.
-- Host admits original field disclosure/cut/work bounds before sending this query.
SELECT c.tableoid::pg_catalog.text AS catalog_class_oid,
       c.oid::pg_catalog.text AS wrapper_oid,
       c.fdwname::pg_catalog.text AS wrapper_name,
       c.fdwowner::pg_catalog.text AS owner_oid,
       c.fdwhandler::pg_catalog.text AS handler_oid,
       c.fdwvalidator::pg_catalog.text AS validator_oid,
       c.fdwacl::pg_catalog.text AS acl_native_text,
       pg_catalog.array_dims(c.fdwacl) AS acl_native_dimensions
FROM pg_catalog.pg_foreign_data_wrapper AS c
WHERE c.oid = ANY($1::pg_catalog.oid[])
ORDER BY c.oid;
