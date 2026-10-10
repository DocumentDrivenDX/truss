-- Unexecuted extension seed/lookup; $1 namespace oid, $2 admitted extension oid[] <=256.
SELECT e.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       e.oid::pg_catalog.text AS object_oid,
       e.extconfig::pg_catalog.text AS extconfig_native_text,
       pg_catalog.array_dims(e.extconfig) AS extconfig_native_dimensions,
       e.extcondition::pg_catalog.text AS extcondition_native_text,
       pg_catalog.array_dims(e.extcondition) AS extcondition_native_dimensions,
       pg_catalog.to_jsonb(e)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_extension AS e
WHERE e.extnamespace = $1::pg_catalog.oid OR e.oid = ANY ($2::pg_catalog.oid[])
ORDER BY e.oid;
