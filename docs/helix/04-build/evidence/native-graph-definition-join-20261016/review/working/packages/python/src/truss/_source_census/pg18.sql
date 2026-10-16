-- The deprecated pg16 filename aliases these18.6-only fixture bytes.
-- Private PostgreSQL18.6 source-catalog census; not authenticated admission.
-- Captures whole-database selected catalogs, including bodies absent from pg_depend.
-- OID-alias fields retain numeric identity beside their potentially ambiguous spelling.
-- Table contents/statistics, external executable custody, source writers and a
-- stable authority/data cut require separate qualification. No credential columns.
-- Each section retains at most8193 rows: overflow refuses, never a complete prefix.
-- The16MiB serialization ceiling does not bound native scan/aggregate work or heap.
WITH source_sections AS (
SELECT 'pg_namespace'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_namespace AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_class'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) - ARRAY['relpages','reltuples','relallvisible','relallfrozen','relfrozenxid','relminmxid']::pg_catalog.text[])::pg_catalog.text AS row_text FROM pg_catalog.pg_class AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_attribute'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_attribute AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_attrdef'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_attrdef AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_constraint'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_constraint AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_index'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_index AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_inherits'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_inherits AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_partitioned_table'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_partitioned_table AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_rewrite'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_rewrite AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_policy'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_policy AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_trigger'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_trigger AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_proc'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('prosupport',r.prosupport::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_proc AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_language'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_language AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_operator'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('oprcode',r.oprcode::pg_catalog.oid::pg_catalog.text,'oprrest',r.oprrest::pg_catalog.oid::pg_catalog.text,'oprjoin',r.oprjoin::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_operator AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_cast'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_cast AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_type'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('typinput',r.typinput::pg_catalog.oid::pg_catalog.text,'typoutput',r.typoutput::pg_catalog.oid::pg_catalog.text,'typreceive',r.typreceive::pg_catalog.oid::pg_catalog.text,'typsend',r.typsend::pg_catalog.oid::pg_catalog.text,'typmodin',r.typmodin::pg_catalog.oid::pg_catalog.text,'typmodout',r.typmodout::pg_catalog.oid::pg_catalog.text,'typanalyze',r.typanalyze::pg_catalog.oid::pg_catalog.text,'typsubscript',r.typsubscript::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_type AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_enum'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_enum AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_range'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('rngcanonical',r.rngcanonical::pg_catalog.oid::pg_catalog.text,'rngsubdiff',r.rngsubdiff::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_range AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_collation'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_collation AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_conversion'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('conproc',r.conproc::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_conversion AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_opclass'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_opclass AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_opfamily'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_opfamily AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_am'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('amhandler',r.amhandler::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_am AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_amop'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_amop AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_amproc'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('amproc',r.amproc::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_amproc AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_extension'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_extension AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_depend'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_depend AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_shdepend'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_shdepend AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_default_acl'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_default_acl AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_auth_members'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_auth_members AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_db_role_setting'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_db_role_setting AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_sequence'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_sequence AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_statistic_ext'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_statistic_ext AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_database'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_database AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_roles'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT pg_catalog.jsonb_build_object('oid',r.oid::pg_catalog.text,'name',r.rolname,'superuser',r.rolsuper,'inherit',r.rolinherit,'createRole',r.rolcreaterole,'createDb',r.rolcreatedb,'login',r.rolcanlogin,'replication',r.rolreplication,'bypass',r.rolbypassrls,'validUntil',r.rolvaliduntil::pg_catalog.text,'config',r.rolconfig)::pg_catalog.text AS row_text FROM pg_catalog.pg_roles AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'foreign_routes'::pg_catalog.text AS section, pg_catalog.jsonb_build_array(pg_catalog.jsonb_build_object('wrappers',(SELECT pg_catalog.count(*)::pg_catalog.text FROM pg_catalog.pg_foreign_data_wrapper),'servers',(SELECT pg_catalog.count(*)::pg_catalog.text FROM pg_catalog.pg_foreign_server),'tables',(SELECT pg_catalog.count(*)::pg_catalog.text FROM pg_catalog.pg_foreign_table),'userMappings',(SELECT pg_catalog.count(*)::pg_catalog.text FROM pg_catalog.pg_user_mapping))::pg_catalog.text) AS rows
UNION ALL
SELECT 'pg_aggregate'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('aggfnoid',r.aggfnoid::pg_catalog.oid::pg_catalog.text,'aggtransfn',r.aggtransfn::pg_catalog.oid::pg_catalog.text,'aggfinalfn',r.aggfinalfn::pg_catalog.oid::pg_catalog.text,'aggcombinefn',r.aggcombinefn::pg_catalog.oid::pg_catalog.text,'aggserialfn',r.aggserialfn::pg_catalog.oid::pg_catalog.text,'aggdeserialfn',r.aggdeserialfn::pg_catalog.oid::pg_catalog.text,'aggmtransfn',r.aggmtransfn::pg_catalog.oid::pg_catalog.text,'aggminvtransfn',r.aggminvtransfn::pg_catalog.oid::pg_catalog.text,'aggmfinalfn',r.aggmfinalfn::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_aggregate AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_parameter_acl'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_parameter_acl AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_event_trigger'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r))::pg_catalog.text AS row_text FROM pg_catalog.pg_event_trigger AS r LIMIT 8193) AS bounded_rows) AS rows
UNION ALL
SELECT 'pg_transform'::pg_catalog.text AS section, (SELECT pg_catalog.jsonb_agg(row_text ORDER BY row_text COLLATE pg_catalog."C") FROM (SELECT (pg_catalog.to_jsonb(r) OPERATOR(pg_catalog.||) pg_catalog.jsonb_build_object('nativeOidReferences',pg_catalog.jsonb_build_object('trffromsql',r.trffromsql::pg_catalog.oid::pg_catalog.text,'trftosql',r.trftosql::pg_catalog.oid::pg_catalog.text)))::pg_catalog.text AS row_text FROM pg_catalog.pg_transform AS r LIMIT 8193) AS bounded_rows) AS rows
), measured AS (
 SELECT section,COALESCE(rows,'[]'::pg_catalog.jsonb) AS rows,
 pg_catalog.jsonb_array_length(COALESCE(rows,'[]'::pg_catalog.jsonb)) AS count
 FROM source_sections
), candidate AS (
 SELECT pg_catalog.jsonb_build_object(
 'version','truss.security.query-source-census/0.1.0',
 'serverVersion',pg_catalog.current_setting('server_version_num'),
 'database',pg_catalog.current_database(),
 'sections',pg_catalog.jsonb_object_agg(section,rows ORDER BY section COLLATE pg_catalog."C"),
 'rowCount',pg_catalog.sum(count)::pg_catalog.text) AS image,
 pg_catalog.max(count) AS largest_section,pg_catalog.sum(count) AS total_rows
 FROM measured
)
SELECT CASE WHEN pg_catalog.current_setting('server_version_num') OPERATOR(pg_catalog.=) '180006'
 AND largest_section OPERATOR(pg_catalog.<=) 8192 AND total_rows OPERATOR(pg_catalog.<=) 100000
 AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_foreign_data_wrapper)
 AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_foreign_server)
 AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_foreign_table)
 AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_user_mapping)
 AND pg_catalog.octet_length(image::pg_catalog.text) OPERATOR(pg_catalog.<=) 16777216
 THEN image::pg_catalog.text ELSE NULL END AS census FROM candidate;
