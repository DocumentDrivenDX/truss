-- Unexecuted PG17 declaration header. Options deliberately unselected, not NULL.
-- Original admitted unique nonnull 1D oid batch, lower bound 1, 1..256 items.
-- Host admits original field disclosure/cut/work bounds before sending this query.
SELECT c.tableoid::pg_catalog.text AS catalog_class_oid,
       c.oid::pg_catalog.text AS server_oid,
       c.srvname::pg_catalog.text AS server_name,
       c.srvowner::pg_catalog.text AS owner_oid,
       c.srvfdw::pg_catalog.text AS wrapper_oid,
       c.srvtype::pg_catalog.text AS declared_server_type,
       c.srvversion::pg_catalog.text AS declared_server_version,
       c.srvacl::pg_catalog.text AS acl_native_text,
       pg_catalog.array_dims(c.srvacl) AS acl_native_dimensions
FROM pg_catalog.pg_foreign_server AS c
WHERE c.oid = ANY($1::pg_catalog.oid[])
ORDER BY c.oid;
