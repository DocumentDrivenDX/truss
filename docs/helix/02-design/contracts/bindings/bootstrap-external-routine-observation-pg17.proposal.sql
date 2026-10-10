-- Unexecuted PostgreSQL 17 exact external-frontier lookup.
-- $1 is admitted nonnull one-dimensional unique oid[] of <=256 actual objects.
-- Input class and subobject=0 are checked against original frontier before this call.
-- No namespace filter; original external ownership remains explicit.
SELECT p.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       p.oid::pg_catalog.text AS object_oid,
       p.pronamespace::pg_catalog.text AS namespace_oid,
       p.prosupport::pg_catalog.oid::pg_catalog.text AS prosupport_oid,
       p.proallargtypes::pg_catalog.text AS proallargtypes_native_text,
       pg_catalog.array_dims(p.proallargtypes) AS proallargtypes_native_dimensions,
       p.proargmodes::pg_catalog.text AS proargmodes_native_text,
       pg_catalog.array_dims(p.proargmodes) AS proargmodes_native_dimensions,
       p.proargnames::pg_catalog.text AS proargnames_native_text,
       pg_catalog.array_dims(p.proargnames) AS proargnames_native_dimensions,
       p.protrftypes::pg_catalog.text AS protrftypes_native_text,
       pg_catalog.array_dims(p.protrftypes) AS protrftypes_native_dimensions,
       p.proconfig::pg_catalog.text AS proconfig_native_text,
       pg_catalog.array_dims(p.proconfig) AS proconfig_native_dimensions,
       p.proacl::pg_catalog.text AS proacl_native_text,
       pg_catalog.array_dims(p.proacl) AS proacl_native_dimensions,
       p.proargtypes::pg_catalog.text AS proargtypes_native_vector_text,
       pg_catalog.array_dims(p.proargtypes) AS proargtypes_native_vector_dimensions,
       pg_catalog.encode(pg_catalog.float4send(p.procost),'hex') AS cost_float4_send_hex,
       pg_catalog.encode(pg_catalog.float4send(p.prorows),'hex') AS rows_float4_send_hex,
       pg_catalog.to_jsonb(p)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_proc AS p
WHERE p.oid = ANY ($1::pg_catalog.oid[])
ORDER BY p.oid;
