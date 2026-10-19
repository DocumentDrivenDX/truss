# SPDX-License-Identifier: MIT OR Apache-2.0
"""Source-validated graph Subject registration and own-session metadata issuer.

Fresh trusted administrator/compiler/source and DDL/routine custody remain
premises. Caller owns settlement; this does not admit public security queries.
"""
from dataclasses import dataclass,replace
from hashlib import sha256
from importlib.resources import files
import json
from psycopg import sql
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_subject_installation import _text_rows
from ._security_catalog_assessment import capture_accepted_catalog
from ._security_relationship_source import PreparedRelationshipSecuritySource,snapshot_relationship_security_source
from ._security_graph_source import snapshot_graph_security_source,acquire_graph_source_catalog_cut
from ._owner_evidence_json import decode_owner_evidence_json

_DIGEST='0520931a9060692a99282b18d98b6f9becff7c00e735562a2ed7d1b69e83c0b8'

@dataclass(frozen=True,slots=True)
class PendingGraphSubjects:
 installation_id:str
 owner_oid:int
 profile_bytes:bytes
 bindings:tuple
 source_sha256:str=_DIGEST
 status:str='pending_commit'
 security_ready:bool=False


def _source():
 raw=files('truss').joinpath('_security_bootstrap','graph-subject.sql').read_bytes()
 if sha256(raw).hexdigest()!=_DIGEST:raise ValueError('Original graph Subject issuer source required')
 return raw


def _snapshot_subject_source(source):
 if type(source) is PreparedRelationshipSecuritySource:return snapshot_relationship_security_source(source)
 return snapshot_graph_security_source(source)


def _recipe(source):
 request=decode_owner_evidence_json(source.native_dependencies)
 ontology=decode_owner_evidence_json(request['ontologyJson'].encode())
 if ontology['subject']!={'documentId':'domain','moduleId':'m','elementId':'Staff'}:raise ValueError('Selected graph Staff Subject required')
 binding=decode_owner_evidence_json(request['bindingJson'].encode());correspondence=decode_owner_evidence_json(binding['correspondenceJson'].encode())
 entities=[e for e in correspondence['entities'] if e['logicalType']==ontology['subject']]
 if len(entities)!=1:raise ValueError('Original unique graph Staff binding required')
 entity=entities[0];pin=binding['physicalModule']['pin'];inventory=decode_owner_evidence_json(source.accepted_catalog_assessment)['inventory']
 def one(rows):
  if len(rows)!=1:raise ValueError('Original unique graph Subject catalog home required')
  return rows[0]
 record=one([r for r in inventory['types'] if r['retired_rev'] is None and (r['document_id'],r['module'],r['element'])==(pin['documentId'],'m','Staff')])
 if record['kind']!='record' or record['provisional'] is not False or entity['nativeType']!={'documentId':pin['documentId'],'moduleId':'m','elementId':'Staff','typeId':str(record['type_id'])}:raise ValueError('Original graph Staff Record correspondence required')
 prop=one([p for p in inventory['properties'] if p['retired_rev'] is None and p['type_id']==record['type_id'] and (p['definition_document_id'],p['declaration_module'],p['element'])==(pin['documentId'],'m','staffId')])
 key=one([k for k in inventory['keys'] if k['retired_rev'] is None and k['type_id']==record['type_id'] and k['key_id']=='pk'])
 if (any(type(v) is not int or not 1<=v<=2147483647 for v in (record['type_id'],prop['prop_id'])) or key['prop_ids']!=[prop['prop_id']]
     or (prop['home'],prop['scalar_type'],prop['cardinality'],prop['nullability'])!=('json','string','one','required')
     or entity['nativePropertyId']!=str(prop['prop_id']) or entity['logicalKeyId']!='pk' or entity['nativeKeyId']!='pk' or entity['logicalKeyField']!='staffId' or entity['nativeKeyField']!='staffId'):
  raise ValueError('Original required single-string graph Subject key required')
 revision=decode_owner_evidence_json(source.accepted_catalog_assessment)['revision']
 return pin,record['type_id'],prop['prop_id'],int(revision),request


def verify_graph_subject_issuer_with_cursor(cursor,subjects):
 subjects=snapshot_graph_subjects(subjects)
 raw=_source();body=raw.decode().split('AS $$',1)[1].split('$$;',1)[0]
 rows=_text_rows(cursor,"SELECT p.oid::pg_catalog.text,p.proowner::pg_catalog.text,l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,p.proretset::pg_catalog.text,p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,p.proparallel::pg_catalog.text,p.proleakproof::pg_catalog.text,p.prosupport::pg_catalog.oid::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,(p.prosqlbody IS NULL)::pg_catalog.text,pg_catalog.to_jsonb(p.proargmodes)::pg_catalog.text,pg_catalog.to_jsonb(p.proallargtypes)::pg_catalog.text,pg_catalog.to_jsonb(p.proargnames)::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'graph_subject_current'",limit=1)
 expected=(str(subjects.owner_oid),'plpgsql','f','0','','2249','true','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,'true','["t", "t", "t", "t", "t"]','["25", "25", "25", "25", "25"]','["staff_key", "installation_id", "database_oid", "role_oid", "profile_sha256"]')
 if len(rows)!=1 or rows[0][1:]!=expected:raise ValueError('Exact original graph Subject issuer definition required')
 acl=_text_rows(cursor,"SELECT a.grantee::pg_catalog.text,a.grantor::pg_catalog.text,a.privilege_type::pg_catalog.text,a.is_grantable::pg_catalog.text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid ORDER BY a.grantee",(int(rows[0][0]),),257)
 expected=sorted([(str(subjects.owner_oid),str(subjects.owner_oid),'EXECUTE','false')]+[(str(oid),str(subjects.owner_oid),'EXECUTE','false') for oid,key in subjects.bindings],key=lambda r:int(r[0]))
 if acl!=expected:raise ValueError('Exact registered graph Subject issuer ACL required')
 return int(rows[0][0])


def bootstrap_graph_subjects_in_transaction(host,transaction,*,source,bindings):
 if type(host) is not PsycopgHost:return Error(ExecutionFailure('execution_obligation','Original graph Subject installation host required'))
 try:
  source=_snapshot_subject_source(source);pin,type_id,property_id,revision,request=_recipe(source);raw=_source()
  if type(bindings) is not tuple or not 1<=len(bindings)<=256 or any(type(b) is not tuple or len(b)!=2 or any(type(v) is not str or not v or '\0' in v for v in b) or len(b[0].encode())>63 or len(b[1].encode())>4096 for b in bindings) or len({b[0] for b in bindings})!=len(bindings):raise ValueError('Original bounded graph Subject bindings required')
  bindings=tuple((role,key) for role,key in bindings)
 except (ValueError,TypeError,KeyError,AttributeError,UnicodeError):return Error(ExecutionFailure('execution_obligation','Original bounded graph Subject source required'))
 def install(cursor,observed):
  _pin_cursor(cursor)
  prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
  if len(prior)!=1 or observed[0][2:]!=('read_committed','read_write'):raise ValueError('Original fresh graph Subject installation required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  from ._current_query_protection import require_unprotected_configuration
  require_unprotected_configuration(cursor,allow_uninstalled=True)
  if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num')::pg_catalog.text",limit=1)!=[('180006',)]:raise ValueError('Original supported graph Subject server required')
  target=_text_rows(cursor,'SELECT installation_id::pg_catalog.text,owner_oid::pg_catalog.text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',limit=1)
  if len(target)!=1:raise ValueError('Original graph Subject installation identity required')
  owner=int(target[0][1]);installation_administrator_with_cursor(cursor,owner)
  acquire_graph_source_catalog_cut(cursor)
  if capture_accepted_catalog(cursor,source.original_request,existing_source_cut=True)!=source.accepted_catalog_assessment:raise ValueError('Original graph Subject accepted source required')
  if _text_rows(cursor,"SELECT c.relname::pg_catalog.text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND c.relname OPERATOR(pg_catalog.=) ANY(ARRAY['catalog_subject_map','catalog_graph_subject_profile']::pg_catalog.text[])",limit=2) or _text_rows(cursor,"SELECT p.oid::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'graph_subject_current'",limit=1):raise ValueError('Existing graph Subject registration requires explicit migration')
  cursor.execute('LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT',prepare=False)
  shape=_text_rows(cursor,"SELECT c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,c.relrowsecurity::pg_catalog.text,c.relforcerowsecurity::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid OPERATOR(pg_catalog.=) c.oid OR i.inhparent OPERATOR(pg_catalog.=) c.oid)::pg_catalog.text FROM pg_catalog.pg_class c WHERE c.oid OPERATOR(pg_catalog.=) 'truss.object'::pg_catalog.regclass",limit=1)
  if shape!=[('r','p','false','false','false')]:raise ValueError('Original unfiltered graph Subject population required')
  principals=[]
  for role,key in bindings:
   principal=_text_rows(cursor,"SELECT oid::pg_catalog.text,rolcanlogin::pg_catalog.text,rolsuper::pg_catalog.text,rolcreatedb::pg_catalog.text,rolcreaterole::pg_catalog.text,rolreplication::pg_catalog.text,rolbypassrls::pg_catalog.text,pg_catalog.pg_has_role(oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) %s",(owner,role),1)
   if len(principal)!=1 or principal[0][1:]!=('true','false','false','false','false','false','false'):raise ValueError('Original ordinary graph Subject principal required')
   matches=_text_rows(cursor,"SELECT id::pg_catalog.text FROM ONLY truss.object WHERE type_id OPERATOR(pg_catalog.=) %s AND root_id IS NULL AND pg_catalog.jsonb_typeof(props OPERATOR(pg_catalog.->) %s) OPERATOR(pg_catalog.=) 'object' AND (props OPERATOR(pg_catalog.->) %s) OPERATOR(pg_catalog.->>) 'kind' OPERATOR(pg_catalog.=) 'string' AND pg_catalog.jsonb_typeof((props OPERATOR(pg_catalog.->) %s) OPERATOR(pg_catalog.->) 'text') OPERATOR(pg_catalog.=) 'string' AND ((props OPERATOR(pg_catalog.->) %s) OPERATOR(pg_catalog.->>) 'text') COLLATE pg_catalog.\"C\" OPERATOR(pg_catalog.=) %s COLLATE pg_catalog.\"C\"",(type_id,str(property_id),str(property_id),str(property_id),str(property_id),key),2)
   if len(matches)!=1:raise ValueError('Unique original stored graph Staff identity required')
   principals.append((int(principal[0][0]),key))
  profile=derive_graph_subject_profile(source)
  cursor.execute('CREATE TABLE truss.catalog_subject_map(role_oid pg_catalog.oid PRIMARY KEY,staff_key pg_catalog.text COLLATE pg_catalog."C" NOT NULL);CREATE TABLE truss.catalog_graph_subject_profile(singleton pg_catalog.int2 PRIMARY KEY CHECK(singleton=1),installation_id pg_catalog.uuid NOT NULL,native_revision pg_catalog.int4 NOT NULL,type_id pg_catalog.int4 NOT NULL,property_id pg_catalog.int4 NOT NULL,document_id pg_catalog.text NOT NULL,document_revision pg_catalog.text NOT NULL,document_sha256 pg_catalog.text NOT NULL,module_id pg_catalog.text NOT NULL,profile_bytes pg_catalog.bytea NOT NULL CHECK(octet_length(profile_bytes) BETWEEN 1 AND 65536))',prepare=False)
  owner_name=_text_rows(cursor,'SELECT rolname::pg_catalog.text FROM pg_catalog.pg_roles WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid',(owner,),1)
  if len(owner_name)!=1:raise ValueError('Original graph Subject owner required')
  for table in ('catalog_subject_map','catalog_graph_subject_profile'):
   cursor.execute(sql.SQL('ALTER TABLE {} OWNER TO {}').format(sql.Identifier('truss',table),sql.Identifier(owner_name[0][0])),prepare=False)
   acl=_text_rows(cursor,"SELECT a.grantee::pg_catalog.text,a.grantor::pg_catalog.text FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE c.oid OPERATOR(pg_catalog.=) %s::pg_catalog.regclass",('truss.'+table,),64)
   if any(row!=(str(owner),str(owner)) for row in acl):raise ValueError('Original private graph Subject home defaults required')
  for oid,key in principals:cursor.execute('INSERT INTO truss.catalog_subject_map VALUES(%s,%s)',(oid,key),prepare=False)
  cursor.execute('INSERT INTO truss.catalog_graph_subject_profile VALUES(1,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(target[0][0],revision,type_id,property_id,pin['documentId'],pin['revision'],pin['sha256'],'m',profile),prepare=False)
  cursor.execute(raw.decode(),prepare=False)
  cursor.execute(sql.SQL('ALTER FUNCTION truss.graph_subject_current() OWNER TO {}').format(sql.Identifier(owner_name[0][0])),prepare=False)
  for role,key in bindings:
   cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {};GRANT EXECUTE ON FUNCTION truss.graph_subject_current() TO {}').format(sql.Identifier(role),sql.Identifier(role)),prepare=False)
  profile_rows=_text_rows(cursor,"SELECT singleton::pg_catalog.text,installation_id::pg_catalog.text,native_revision::pg_catalog.text,type_id::pg_catalog.text,property_id::pg_catalog.text,document_id::pg_catalog.text,document_revision::pg_catalog.text,document_sha256::pg_catalog.text,module_id::pg_catalog.text,pg_catalog.encode(profile_bytes,'hex') FROM ONLY truss.catalog_graph_subject_profile",limit=1)
  if profile_rows!=[('1',target[0][0],str(revision),str(type_id),str(property_id),pin['documentId'],pin['revision'],pin['sha256'],'m',profile.hex())]:raise ValueError('Exact graph Subject profile readback required')
  dependencies=['truss.'+n for n in ('catalog_graph_subject_profile','catalog_subject_map','object','schema_head','schema_doc','type_def','prop_def','key_def','catalog_runtime_installation')]
  reads=_text_rows(cursor,"SELECT pg_catalog.has_schema_privilege(%s::pg_catalog.oid,'truss','USAGE')::pg_catalog.text,(NOT EXISTS(SELECT 1 FROM pg_catalog.unnest(%s::pg_catalog.text[]) table_name WHERE NOT pg_catalog.has_table_privilege(%s::pg_catalog.oid,table_name,'SELECT')))::pg_catalog.text",(owner,dependencies,owner),1)
  if reads!=[('true','true')]:raise ValueError('Original graph Subject owner read privileges required')
  locks=_text_rows(cursor,"SELECT (NOT EXISTS(SELECT 1 FROM pg_catalog.unnest(%s::pg_catalog.text[]) table_name WHERE NOT (pg_catalog.has_table_privilege(%s::pg_catalog.oid,table_name,'MAINTAIN') OR pg_catalog.has_table_privilege(%s::pg_catalog.oid,table_name,'UPDATE') OR pg_catalog.has_table_privilege(%s::pg_catalog.oid,table_name,'DELETE') OR pg_catalog.has_table_privilege(%s::pg_catalog.oid,table_name,'TRUNCATE'))))::pg_catalog.text",(dependencies,owner,owner,owner,owner),1)
  if locks!=[('true',)]:raise ValueError('Original graph Subject owner SHARE privileges required')
  subjects=PendingGraphSubjects(target[0][0],owner,profile,tuple(sorted(principals)))
  verify_graph_subject_issuer_with_cursor(cursor,subjects)
  if _text_rows(cursor,'SELECT role_oid::pg_catalog.text,staff_key::pg_catalog.text FROM ONLY truss.catalog_subject_map ORDER BY role_oid',limit=256)!=[(str(oid),key) for oid,key in subjects.bindings]:raise ValueError('Exact registered graph Subject map readback required')
  if capture_accepted_catalog(cursor,source.original_request,existing_source_cut=True)!=source.accepted_catalog_assessment:raise ValueError('Graph Subject source changed during registration')
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
  if cursor.fetchmany(2)!=prior:raise ValueError('Original graph Subject installer path restoration required')
  return subjects
 return host._run_operation(transaction,install)


def snapshot_graph_subjects(subjects):
 if (type(subjects) is not PendingGraphSubjects or type(subjects.installation_id) is not str or not 1<=len(subjects.installation_id.encode())<=1024
     or type(subjects.owner_oid) is not int or not 1<=subjects.owner_oid<=4294967295
     or type(subjects.profile_bytes) is not bytes or not 1<=len(subjects.profile_bytes)<=65536
     or subjects.source_sha256!=_DIGEST or subjects.status!='pending_commit' or subjects.security_ready is not False
     or type(subjects.bindings) is not tuple or not 1<=len(subjects.bindings)<=256
     or any(type(b) is not tuple or len(b)!=2 or type(b[0]) is not int or not 1<=b[0]<=4294967295 or b[0]==subjects.owner_oid or type(b[1]) is not str or not 1<=len(b[1].encode())<=4096 or '\0' in b[1] for b in subjects.bindings)
     or tuple(sorted(subjects.bindings))!=subjects.bindings or len({b[0] for b in subjects.bindings})!=len(subjects.bindings)):
  raise ValueError('Original bounded graph Subject registration comparisons required')
 return replace(subjects,bindings=tuple((oid,key) for oid,key in subjects.bindings))


def verify_registered_graph_subjects_with_cursor(cursor,subjects,*,caller_pid,source):
 """Profile cut belongs to the reserved real caller; role/map cuts are separate."""
 subjects=snapshot_graph_subjects(subjects)
 if type(caller_pid) is not int or not 1<=caller_pid<=2147483647:raise ValueError('Original graph Subject caller backend required')
 issuer=verify_graph_subject_issuer_with_cursor(cursor,subjects)
 verify_subject_home_write_denial(cursor,subjects.bindings,include_profile=True)
 homes=_text_rows(cursor,"SELECT c.relowner::pg_catalog.text,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,c.relrowsecurity::pg_catalog.text,c.relforcerowsecurity::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid OPERATOR(pg_catalog.=) c.oid OR i.inhparent OPERATOR(pg_catalog.=) c.oid)::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.pid OPERATOR(pg_catalog.=) %s AND l.locktype OPERATOR(pg_catalog.=) 'relation' AND l.database OPERATOR(pg_catalog.=) (SELECT oid FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()) AND l.relation OPERATOR(pg_catalog.=) c.oid AND l.mode OPERATOR(pg_catalog.=) 'ShareLock' AND l.granted)::pg_catalog.text FROM pg_catalog.pg_class c WHERE c.oid OPERATOR(pg_catalog.=) 'truss.catalog_graph_subject_profile'::pg_catalog.regclass",(caller_pid,),1)
 if homes!=[(str(subjects.owner_oid),'r','p','false','false','false','true')]:raise ValueError('Original held graph Subject profile required')
 source=_snapshot_subject_source(source)
 pin,type_id,property_id,revision,request=_recipe(source)
 if subjects.profile_bytes!=derive_graph_subject_profile(source):raise ValueError('Original selected registered graph Subject source required')
 rows=_text_rows(cursor,"SELECT singleton::pg_catalog.text,installation_id::pg_catalog.text,native_revision::pg_catalog.text,type_id::pg_catalog.text,property_id::pg_catalog.text,document_id::pg_catalog.text,document_revision::pg_catalog.text,document_sha256::pg_catalog.text,module_id::pg_catalog.text,pg_catalog.encode(profile_bytes,'hex') FROM ONLY truss.catalog_graph_subject_profile",limit=1)
 if rows!=[('1',subjects.installation_id,str(revision),str(type_id),str(property_id),pin['documentId'],pin['revision'],pin['sha256'],'m',subjects.profile_bytes.hex())]:raise ValueError('Original current registered graph Subject profile required')
 if _text_rows(cursor,'SELECT installation_id::pg_catalog.text,owner_oid::pg_catalog.text FROM truss.catalog_runtime_installation WHERE singleton',limit=1)!=[(subjects.installation_id,str(subjects.owner_oid))]:raise ValueError('Original registered graph Subject installation required')
 return issuer


def read_own_graph_subject_with_cursor(cursor,subjects,identity):
 """Native own-session projection only; caller/peer authentication is separate."""
 subjects=snapshot_graph_subjects(subjects)
 verify_graph_subject_issuer_with_cursor(cursor,subjects)
 rows=_text_rows(cursor,'SELECT * FROM truss.graph_subject_current()',limit=2)
 keys=[key for oid,key in subjects.bindings if str(oid)==identity[1]]
 if len(keys)!=1 or rows!=[(keys[0],subjects.installation_id,identity[0],identity[1],sha256(subjects.profile_bytes).hexdigest())]:raise ValueError('Original own-session graph Subject correspondence required')
 return keys[0]


def derive_graph_subject_profile(source):
 source=_snapshot_subject_source(source)
 pin,type_id,property_id,revision,request=_recipe(source)
 return json.dumps({'version':'truss.registered-relationship-subject/0.1-candidate' if type(source) is PreparedRelationshipSecuritySource else 'truss.registered-graph-subject/0.1-candidate','physicalRequestSha256':sha256(source.original_request).hexdigest(),'acceptedCatalogSha256':sha256(source.accepted_catalog_assessment).hexdigest(),'graphBindingSha256':sha256(request['bindingJson'].encode()).hexdigest(),'ontologySha256':sha256(request['ontologyJson'].encode()).hexdigest(),'policySha256':sha256(request['policyJson'].encode()).hexdigest(),'physicalPin':pin,'nativeTypeId':str(type_id),'nativePropertyId':str(property_id)},sort_keys=True,separators=(',',':')).encode()


def verify_subject_home_write_denial(cursor,bindings,*,include_profile=False):
 if type(include_profile) is not bool:raise ValueError('Exact Subject home scope required')
 homes=['truss.catalog_subject_map']+(['truss.catalog_graph_subject_profile'] if include_profile else [])
 roles=[oid for oid,key in bindings]
 rows=_text_rows(cursor,"SELECT (NOT EXISTS(SELECT 1 FROM pg_catalog.unnest(%s::pg_catalog.oid[]) actor CROSS JOIN pg_catalog.unnest(%s::pg_catalog.text[]) home WHERE EXISTS(SELECT 1 FROM pg_catalog.unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']::pg_catalog.text[]) privilege WHERE pg_catalog.has_table_privilege(actor,home,privilege)) OR pg_catalog.has_any_column_privilege(actor,home,'INSERT') OR pg_catalog.has_any_column_privilege(actor,home,'UPDATE') OR pg_catalog.has_any_column_privilege(actor,home,'REFERENCES')))::pg_catalog.text",(roles,homes),1)
 if rows!=[('true',)]:raise ValueError('Unmediated registered Subject writes refused')
