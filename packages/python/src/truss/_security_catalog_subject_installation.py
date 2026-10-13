"""Selected named catalog Subject construction; not protected caller admission.

Trusted direct installation administrator, original accepted source custody and
administrative quiescence required. Role and helper lifetime remain separate.
Caller owns commit; existing homes/routines require explicit migration.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from psycopg import sql
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _release,_pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_source_installation import _catalog_mapping_snapshot
from ._security_catalog_assessment import capture_accepted_catalog
from ._security_catalog_subject_helpers import verify_catalog_subject_helpers_with_cursor

_SOURCE_SHA256='2b0d63e005889278bd103696bf4fcd8db15112a5733dfba20f809309cc01ebb8'

@dataclass(frozen=True,slots=True)
class PendingCatalogSubjects:
 installation_id:str
 source_sha256:str
 bindings:tuple[tuple[int,str],...]
 status:str='pending_commit'
 security_ready:bool=False


def _text_rows(cursor,query,params=(),limit=256):
 cursor.execute(query,params,prepare=False,binary=False)
 if cursor.description is None or any(d.type_code!=25 for d in cursor.description):raise ValueError('Exact Subject installation TEXT descriptors required')
 rows=cursor.fetchmany(limit+1)
 if len(rows)>limit or any(any(type(v) is not str for v in row) for row in rows):raise ValueError('Bounded exact Subject installation rows required')
 return rows


def _staff_recipe(mapping):
 request=json.loads(mapping.original_request);ontology=json.loads(request['ontologyJson'])
 if ontology['subject']!={'documentId':'domain','moduleId':'m','elementId':'Staff'}:raise ValueError('Selected named Staff Subject required')
 entities=[e for e in ontology['entities'] if e['type']==ontology['subject']]
 if len(entities)!=1 or entities[0]['keyId']!='pk':raise ValueError('Selected ontology Staff key required')
 inventory=json.loads(mapping.accepted_catalog_assessment)['inventory']
 types=[r for r in inventory['types'] if (r['document_id'],r['module'],r['element'])==('domain','m','Staff') and r['retired_rev'] is None]
 if len(types)!=1 or types[0]['kind']!='record' or types[0]['provisional']:raise ValueError('Original active named Staff Record required')
 type_id=types[0]['type_id']
 props=[r for r in inventory['properties'] if r['type_id']==type_id and (r['definition_document_id'],r['declaration_module'],r['element'])==('domain','m','staffId') and r['retired_rev'] is None]
 if len(props)!=1 or (props[0]['home'],props[0]['scalar_type'],props[0]['cardinality'],props[0]['nullability'])!=('json','string','one','required'):raise ValueError('Original required string Staff key property required')
 keys=[r for r in inventory['keys'] if r['type_id']==type_id and r['key_id']=='pk' and r['retired_rev'] is None]
 prop_id=props[0]['prop_id']
 if len(keys)!=1 or keys[0]['prop_ids']!=[prop_id] or any(type(v) is not int or v<1 for v in (type_id,prop_id)):raise ValueError('Original single-field Staff key required')
 return type_id,str(prop_id)


def bootstrap_catalog_subjects_in_transaction(host,transaction,*,mapping,bindings):
 if type(host) is not PsycopgHost:return Error(ExecutionFailure('execution_obligation','Original Subject installation host required'))
 try:
  mapping=_catalog_mapping_snapshot(mapping)
  if (type(bindings) is not tuple or not 1<=len(bindings)<=256 or any(type(b) is not tuple or len(b)!=2 or any(type(v) is not str or not v or '\0' in v for v in b) or len(b[0].encode())>63 or len(b[1].encode())>4096 for b in bindings) or len({b[0] for b in bindings})!=len(bindings)):raise ValueError('Original bounded Subject role bindings required')
  bindings=tuple((role,key) for role,key in bindings)
  type_id,prop_id=_staff_recipe(mapping)
  source=files('truss').joinpath('_security_bootstrap','catalog-subject.sql').read_bytes()
  if sha256(source).hexdigest()!=_SOURCE_SHA256:raise ValueError('Original Subject helper source required')
 except (ValueError,TypeError,KeyError,UnicodeError):return Error(ExecutionFailure('execution_obligation','Original bounded named Subject installation required'))
 def install(cursor,observed):
  _pin_cursor(cursor);manifest,digest,_=_release()
  prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
  if len(prior)!=1:raise ValueError('Original Subject installation path required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num')::text,pg_catalog.current_setting('transaction_isolation')::text,pg_catalog.current_setting('transaction_read_only')::text",limit=1)!=[('180006','read committed','off')]:raise ValueError('Original supported Subject installation transaction required')
  cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR UPDATE NOWAIT',prepare=False)
  if len(cursor.fetchmany(2))!=1:raise ValueError('Original Subject installation head required')
  cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',prepare=False)
  installed=cursor.fetchmany(2)
  if len(installed)!=1:raise ValueError('Original Subject installation identity required')
  identity,owner=installed[0];actor=installation_administrator_with_cursor(cursor,owner)
  if _text_rows(cursor,'SELECT release_id::text,release_sha256::text FROM truss.runtime_current_installation()',limit=1)!=[(manifest['releaseId'],digest)]:raise ValueError('Original Subject installation release required')
  if capture_accepted_catalog(cursor,mapping.original_request)!=mapping.accepted_catalog_assessment:raise ValueError('Original Subject accepted catalog required')
  owner_names=_text_rows(cursor,'SELECT rolname::text FROM pg_catalog.pg_roles WHERE oid=%s',(owner,),1)
  if len(owner_names)!=1:raise ValueError('Original Subject installation owner required')
  if _text_rows(cursor,"SELECT c.relname::text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname='catalog_subject_map'",limit=1) or _text_rows(cursor,"SELECT p.proname::text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.proname IN ('catalog_subject_current','catalog_subject_context')",limit=2):raise ValueError('Existing Subject installation requires explicit migration')
  cursor.execute('LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT',prepare=False)
  principals=[]
  for role,key in bindings:
   rows=_text_rows(cursor,"SELECT oid::text,rolname::text,rolcanlogin::text,rolsuper::text,rolcreatedb::text,rolcreaterole::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s",(owner,role),1)
   if len(rows)!=1 or rows[0][1:]!=(role,'true','false','false','false','false','false','false'):raise ValueError('Original ordinary login Subject principal required')
   oid=int(rows[0][0]);principals.append((oid,key))
   staff=_text_rows(cursor,"SELECT id::text FROM ONLY truss.object WHERE type_id=%s AND root_id IS NULL AND jsonb_typeof(props->%s)='object' AND props->%s->>'kind'='string' AND jsonb_typeof(props->%s->'text')='string' AND (props->%s->>'text') COLLATE pg_catalog.\"C\"=%s COLLATE pg_catalog.\"C\"",(type_id,prop_id,prop_id,prop_id,prop_id,key),1)
   if len(staff)!=1:raise ValueError('Unique original stored Staff identity required')
  cursor.execute('CREATE TABLE truss.catalog_subject_map(role_oid pg_catalog.oid PRIMARY KEY,staff_key pg_catalog.text COLLATE pg_catalog."C" NOT NULL)',prepare=False)
  acl=_text_rows(cursor,"SELECT a.grantee::text FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE c.oid='truss.catalog_subject_map'::regclass",limit=64)
  if any(r[0]!=str(actor[0]) for r in acl):raise ValueError('Third-party Subject map defaults refused')
  cursor.execute(sql.SQL('ALTER TABLE truss.catalog_subject_map OWNER TO {}').format(sql.Identifier(owner_names[0][0])),prepare=False)
  for oid,key in principals:cursor.execute('INSERT INTO truss.catalog_subject_map VALUES(%s,%s)',(oid,key),prepare=False)
  cursor.execute(source.decode(),prepare=False)
  for name in ('catalog_subject_current','catalog_subject_context'):
   cursor.execute(sql.SQL('ALTER FUNCTION {}(pg_catalog.text) OWNER TO {}').format(sql.Identifier('truss',name),sql.Identifier(owner_names[0][0])),prepare=False)
   for role,key in bindings:cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {}(pg_catalog.text) TO {}').format(sql.Identifier('truss',name),sql.Identifier(role)),prepare=False)
  for role,key in bindings:cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(role)),prepare=False)
  verify_catalog_subject_helpers_with_cursor(cursor,source.decode(),expected_callers=tuple(oid for oid,key in principals))
  rows=_text_rows(cursor,'SELECT role_oid::text,staff_key::text FROM ONLY truss.catalog_subject_map ORDER BY role_oid',limit=256)
  if rows!=[(str(oid),key) for oid,key in sorted(principals)]:raise ValueError('Exact original Subject map readback required')
  home=_text_rows(cursor,"SELECT c.relowner::text,c.relkind::text,c.relpersistence::text,c.relrowsecurity::text,c.relforcerowsecurity::text,(NOT EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE a.grantee<>c.relowner OR a.grantor<>c.relowner))::text FROM pg_catalog.pg_class c WHERE c.oid='truss.catalog_subject_map'::regclass",limit=1)
  if home!=[(str(owner),'r','p','false','false','true')]:raise ValueError('Original private persistent Subject map required')
  reads=_text_rows(cursor,"SELECT pg_catalog.has_schema_privilege(%s,'truss','USAGE')::text,(NOT EXISTS(SELECT 1 FROM pg_catalog.unnest(%s::pg_catalog.text[]) table_name WHERE NOT pg_catalog.has_table_privilege(%s,table_name,'SELECT')))::text",(owner,['truss.object','truss.catalog_subject_map','truss.catalog_runtime_installation','truss.type_def','truss.prop_def'],owner),1)
  if reads!=[('true','true')]:raise ValueError('Original Subject helper owner read privileges required')
  if capture_accepted_catalog(cursor,mapping.original_request)!=mapping.accepted_catalog_assessment:raise ValueError('Subject accepted catalog changed during installation')
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
  if cursor.fetchmany(2)!=[(prior[0][0],)]:raise ValueError('Original Subject installation path restoration required')
  return PendingCatalogSubjects(identity,_SOURCE_SHA256,tuple(sorted(principals)))
 return host._run_operation(transaction,install)
