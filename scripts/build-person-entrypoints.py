#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
from pathlib import Path
import json,hashlib,argparse
p=argparse.ArgumentParser(description='Generate guarded invocation declarations from qualified native metadata')
p.add_argument('--declarations',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]/'packages/python/src/truss/_catalog_runtime'
source=json.loads(a.declarations.read_text())
modes={
'accepted_document':'catalog','catalog_revision':'read','catalog_report':'registrar','catalog_view_basis':'registrar','catalog_accept_with_keys':'registrar',
'reader_catalog':'catalog','reader_catalog_if_changed':'catalog','registrar_status':'catalog','person_runtime_status':'status',
'query_binding':'read','query_binding_if_changed':'read','query_scope':'read',
'query_objects':'read','query_edges':'read','query_page_objects':'read',
'query_export_objects':'read','query_export_edges':'read','query_export_page_objects':'read',
'query_selected_objects':'read','query_seek_objects':'read',
'query_object_attribution':'read','query_object_times':'read','query_object_load_id':'read',
'reached':'read','group_context':'read','group_type_reference':'read','group_relationship_reference':'read','prepare_group':'read',
'get_object':'read','get_edge':'read','lookup_string_key':'read','page_objects':'read','page_edges':'read','traverse_objects':'read','preview_group_conditions':'read',
'recover_group_request':'write','apply_group':'write','apply_group_prepared':'write','writer_schema_basis':'write',
'import_context':'read','batched_import_context':'write','build_import_records':'write','process_import_chunk':'write','validate_batched_import_report':'write',
'import_key_selection':'write','import_identity_key_selection':'write','import_object_identity':'write','import_edge_identity':'write','import_record_source':'write','import_report_record_authority':'write','lookup_import_source':'read',
'page_import_load_audit':'audit','page_mutation_group_audit':'audit','read_import_load_chunk':'audit'}
selected=[f for f in source['functions'] if f['name'] in modes]
assert {f['name'] for f in selected}==set(modes),set(modes)-{f['name'] for f in selected}
statement_sources={
 'query_objects','query_edges','query_page_objects','query_export_objects','query_export_edges','query_export_page_objects',
 'query_selected_objects','query_seek_objects','query_object_attribution','query_object_times','query_object_load_id'}
helper='''-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Denial-capable public invocations; private grants remain mandatory.
CREATE FUNCTION truss.require_person_invocation(original_function regprocedure,admission_kind text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE actor oid;enrolled boolean;installation truss.catalog_runtime_installation%ROWTYPE;original_owner oid;original_execute boolean;
BEGIN
 SELECT oid INTO STRICT actor FROM pg_roles WHERE rolname=session_user;
 IF admission_kind NOT IN ('read','write','catalog','registrar','audit','status') OR admission_kind IS NULL THEN
  RAISE EXCEPTION 'selected invocation family required' USING ERRCODE='22023';END IF;
 WITH RECURSIVE memberships(role_oid) AS (
  SELECT actor UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
 SELECT
  (admission_kind IN ('read','catalog','status') AND EXISTS(
    SELECT 1 FROM truss.module_access m JOIN memberships p
     ON p.role_oid IN (to_regrole(m.reader_role)::oid,to_regrole(m.writer_role)::oid)))
  OR (admission_kind='write' AND EXISTS(
    SELECT 1 FROM truss.module_access m JOIN memberships p ON p.role_oid=to_regrole(m.writer_role)::oid))
  OR (admission_kind IN ('catalog','registrar','status') AND EXISTS(
    SELECT 1 FROM truss.catalog_runtime_installation i JOIN memberships p ON p.role_oid=i.registrar_oid WHERE i.singleton))
  OR (admission_kind IN ('audit','status') AND EXISTS(
    SELECT 1 FROM truss.runtime_import_audit_access a JOIN memberships p ON p.role_oid=a.auditor_oid))
 INTO enrolled;
 -- No installation identity, role name, head or result is released on this path.
 IF enrolled IS DISTINCT FROM true THEN
  RAISE EXCEPTION 'current person invocation admission required' USING ERRCODE='P1403';END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation WHERE singleton;
 -- Replan this fixed catalog observation. A retained SPI plan after a contained
 -- source error otherwise reused an obsolete EXECUTE verdict on PostgreSQL18.6.
 -- Only these two typed OIDs vary; no caller SQL or identifier is interpolated.
 EXECUTE 'SELECT p.proowner,pg_catalog.has_function_privilege($1,p.oid,''EXECUTE'') FROM pg_catalog.pg_proc p WHERE p.oid=$2'
 INTO STRICT original_owner,original_execute USING actor,original_function::oid;
 IF original_owner IS DISTINCT FROM installation.owner_oid
  OR (SELECT oid FROM pg_roles WHERE rolname=current_user) IS DISTINCT FROM installation.owner_oid THEN
  RAISE EXCEPTION 'original installed invocation owner required' USING ERRCODE='55000';END IF;
 IF original_execute IS DISTINCT FROM true THEN
  RAISE EXCEPTION 'original invocation EXECUTE grant required' USING ERRCODE='42501';END IF;
 PERFORM truss.runtime_person(false);
END;
$$;
REVOKE ALL ON FUNCTION truss.require_person_invocation(regprocedure,text) FROM PUBLIC;

'''
parts=[helper];entries=[]
for f in selected:
 names=f['names'] or []
 assert len(names)>=f['inputCount'],f
 assert not f['modes'] or all(m in ('i','o','t') for m in f['modes']),f
 args=','.join('"'+n.replace('"','""')+'"' for n in names[:f['inputCount']])
 mode=modes[f['name']];name='person_'+f['name'];sig=f['signature'];stmt='RETURN QUERY SELECT * FROM' if f['set'] else 'PERFORM' if f['result']=='void' else 'RETURN'
 volatility='STABLE' if f['name'] in statement_sources else 'VOLATILE'
 if volatility=='STABLE':assert f['volatility']=='s',f
 suffix='\n RETURN;' if f['result']=='void' else ''
 parts.append(f'''CREATE FUNCTION truss.{name}({f['arguments']}) RETURNS {f['result']}
LANGUAGE plpgsql {volatility} SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('{sig}'::regprocedure,'{mode}');
 {stmt} truss.{f['name']}({args});{suffix}
END;
$$;
REVOKE ALL ON FUNCTION truss.{name}({f['arguments']}) FROM PUBLIC;

''')
 entries.append({'name':f['name'],'publicName':name,'signature':sig,'arguments':f['arguments'],'mode':mode,'result':f['result'],'set':f['set'],'volatility':'s' if volatility=='STABLE' else 'v'})
(root/'person-entrypoints.sql').write_text(''.join(parts))
(root/'person-entrypoints.json').write_text(json.dumps({'interfaceVersion':'truss-person-invocations/0.2','scope':'Declared person-family admission plus fresh original caller EXECUTE; statement-snapshot data/facts; no private helper or administrative grant','functions':entries},indent=2)+'\n')
print('Generated',len(entries),'native person invocation declarations from exact PostgreSQL metadata')
