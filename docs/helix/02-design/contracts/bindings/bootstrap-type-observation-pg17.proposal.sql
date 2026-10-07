-- Unexecuted PostgreSQL 17 raw observation; $1 is original admitted namespace OID.
-- No expected-name/kind filter; complete native cut/transport/resource qualification required.
SELECT t.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       t.oid::pg_catalog.text AS object_oid,
       t.typnamespace::pg_catalog.text AS namespace_oid,
       t.typsubscript::pg_catalog.oid::pg_catalog.text AS typsubscript_oid,
       t.typinput::pg_catalog.oid::pg_catalog.text AS typinput_oid,
       t.typoutput::pg_catalog.oid::pg_catalog.text AS typoutput_oid,
       t.typreceive::pg_catalog.oid::pg_catalog.text AS typreceive_oid,
       t.typsend::pg_catalog.oid::pg_catalog.text AS typsend_oid,
       t.typmodin::pg_catalog.oid::pg_catalog.text AS typmodin_oid,
       t.typmodout::pg_catalog.oid::pg_catalog.text AS typmodout_oid,
       t.typanalyze::pg_catalog.oid::pg_catalog.text AS typanalyze_oid,
       t.typacl::pg_catalog.text AS typacl_native_text,
       pg_catalog.array_dims(t.typacl) AS typacl_native_dimensions,
       pg_catalog.to_jsonb(t)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_type AS t
WHERE t.typnamespace = $1::pg_catalog.oid
ORDER BY t.oid;
