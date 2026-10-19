# SPDX-License-Identifier: MIT OR Apache-2.0
"""Ordinary graph epoch/archive read cut; not public compiler admission.

Original issuer/installer/routine/DDL/authentication custody are premises.
Comparisons are copied before host entry; native held cuts and readbacks, not
Python objects or checksums, establish the selected current-state observation.
"""
from dataclasses import dataclass,replace
from hashlib import sha256
from importlib.resources import files
from psycopg import sql
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_subject_installation import _text_rows
from ._security_graph_source import snapshot_graph_security_source,graph_source_archives
from ._security_catalog_assessment import capture_accepted_catalog
from ._psycopg_epoch_cut import _EpochComparison
from ._owner_evidence_json import decode_owner_evidence_json

_DIGEST='dd3ed9553c33a0a72274f24caf9f37ed5af1162832aaa25a4cc70929d3203d26'
_TABLES=('source_epoch_current','source_epoch_registry','installation_archive','policy_generation_guard')

@dataclass(frozen=True,slots=True)
class PendingGraphEpochReadCut:
 installation_id:str
 owner_oid:int
 caller_oid:int
 source_sha256:str
 status:str='pending_commit'
 security_ready:bool=False

@dataclass(frozen=True,slots=True)
class GraphEpochReadContext:
 source:object
 comparison:_EpochComparison
 issuer:PendingGraphEpochReadCut
 subject_source:bytes


def _source():
 raw=files('truss').joinpath('_security_bootstrap','graph-epoch-read-cut.sql').read_bytes()
 if sha256(raw).hexdigest()!=_DIGEST:raise ValueError('Original graph epoch cut source required')
 return raw


def _verify_issuer(cursor,issuer):
 raw=_source();body=raw.decode().split('AS $$',1)[1].split('$$;',1)[0]
 rows=_text_rows(cursor,"SELECT p.proowner::pg_catalog.text,l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,p.proretset::pg_catalog.text,p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,p.proparallel::pg_catalog.text,p.proleakproof::pg_catalog.text,p.prosupport::pg_catalog.oid::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,(p.prosqlbody IS NULL)::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'acquire_graph_epoch_read_cut'",limit=1)
 if rows!=[(str(issuer.owner_oid),'plpgsql','f','0','','2278','false','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,'true')]:raise ValueError('Exact original graph epoch cut definition required')
 acl=_text_rows(cursor,"SELECT a.grantee::pg_catalog.text,a.grantor::pg_catalog.text,a.privilege_type::pg_catalog.text,a.is_grantable::pg_catalog.text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid OPERATOR(pg_catalog.=) 'truss.acquire_graph_epoch_read_cut()'::pg_catalog.regprocedure ORDER BY a.grantee",limit=3)
 if acl!=sorted([(str(issuer.owner_oid),str(issuer.owner_oid),'EXECUTE','false'),(str(issuer.caller_oid),str(issuer.owner_oid),'EXECUTE','false')],key=lambda r:int(r[0])):raise ValueError('Exact private graph epoch cut ACL required')
 if _text_rows(cursor,"SELECT rolsuper::pg_catalog.text,pg_catalog.pg_has_role(%s::pg_catalog.oid,oid,'MEMBER')::pg_catalog.text FROM pg_catalog.pg_roles WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid",(issuer.caller_oid,issuer.owner_oid),1)!=[('true','false')]:raise ValueError('Original excluded privileged graph epoch cut owner required')


def _verify_homes(cursor,*,held):
 rows=_text_rows(cursor,"SELECT c.relname::pg_catalog.text,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,c.relrowsecurity::pg_catalog.text,c.relforcerowsecurity::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid OPERATOR(pg_catalog.=) c.oid OR i.inhparent OPERATOR(pg_catalog.=) c.oid)::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND l.locktype OPERATOR(pg_catalog.=) 'relation' AND l.database OPERATOR(pg_catalog.=) (SELECT oid FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()) AND l.relation OPERATOR(pg_catalog.=) c.oid AND l.mode OPERATOR(pg_catalog.=) 'ShareLock' AND l.granted)::pg_catalog.text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND c.relname OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.text[]) ORDER BY c.relname",(list(_TABLES),),4)
 if len(rows)!=4 or any(row[:6]!=(name,'r','p','false','false','false') or (held and row[6]!='true') for name,row in zip(sorted(_TABLES),rows)):
  raise ValueError('Original complete unfiltered graph epoch homes and cuts required')



def _verify_private_permissions(cursor,caller_oid):
 rows=_text_rows(cursor,"SELECT (NOT EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND c.relname OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.text[]) AND (c.relowner OPERATOR(pg_catalog.<>) (SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton) OR pg_catalog.pg_has_role(%s::pg_catalog.oid,c.relowner,'MEMBER') OR EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE a.grantor OPERATOR(pg_catalog.<>) c.relowner OR (a.grantee OPERATOR(pg_catalog.<>) c.relowner AND NOT (a.grantee OPERATOR(pg_catalog.=) %s::pg_catalog.oid AND a.privilege_type OPERATOR(pg_catalog.=) 'SELECT' AND NOT a.is_grantable))) OR EXISTS(SELECT 1 FROM pg_catalog.pg_attribute t CROSS JOIN LATERAL pg_catalog.aclexplode(t.attacl) a WHERE t.attrelid OPERATOR(pg_catalog.=) c.oid AND (a.grantor OPERATOR(pg_catalog.<>) c.relowner OR (a.grantee OPERATOR(pg_catalog.<>) c.relowner AND NOT (a.grantee OPERATOR(pg_catalog.=) %s::pg_catalog.oid AND a.privilege_type OPERATOR(pg_catalog.=) 'SELECT' AND NOT a.is_grantable)))) OR EXISTS(SELECT 1 FROM pg_catalog.unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']::pg_catalog.text[]) privilege WHERE pg_catalog.has_table_privilege(%s::pg_catalog.oid,c.oid,privilege)) OR pg_catalog.has_any_column_privilege(%s::pg_catalog.oid,c.oid,'INSERT') OR pg_catalog.has_any_column_privilege(%s::pg_catalog.oid,c.oid,'UPDATE'))))::pg_catalog.text",(list(_TABLES),caller_oid,caller_oid,caller_oid,caller_oid,caller_oid,caller_oid),1)
 if rows!=[('true',)]:raise ValueError('Original private read-only graph epoch homes required')

def bootstrap_graph_epoch_read_cut_in_transaction(host,transaction,*,executor_role):
 if type(host) is not PsycopgHost or type(executor_role) is not str or not 1<=len(executor_role.encode())<=63 or '\0' in executor_role:
  return Error(ExecutionFailure('execution_obligation','Original bounded graph epoch executor required'))
 try:raw=_source()
 except ValueError:return Error(ExecutionFailure('execution_obligation','Original graph epoch cut source required'))
 def install(cursor,observed):
  _pin_cursor(cursor)
  if observed[0][2:]!=('read_committed','read_write'):raise ValueError('Original fresh graph epoch installation transaction required')
  prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
  if len(prior)!=1:raise ValueError('Original graph epoch installer path required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  from ._current_query_protection import require_unprotected_configuration
  require_unprotected_configuration(cursor,allow_uninstalled=True)
  if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num')::pg_catalog.text",limit=1)!=[('180006',)]:raise ValueError('Original supported graph epoch installer required')
  target=_text_rows(cursor,'SELECT installation_id::pg_catalog.text,owner_oid::pg_catalog.text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',limit=1)
  if len(target)!=1:raise ValueError('Original graph epoch installation required')
  actor=installation_administrator_with_cursor(cursor,int(target[0][1]))
  if _text_rows(cursor,'SELECT rolsuper::pg_catalog.text FROM pg_catalog.pg_roles WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid',(actor[0],),1)!=[('true',)]:raise ValueError('Original privileged graph epoch installer required')
  _verify_homes(cursor,held=False)
  caller=_text_rows(cursor,"SELECT oid::pg_catalog.text,rolcanlogin::pg_catalog.text,rolsuper::pg_catalog.text,rolcreatedb::pg_catalog.text,rolcreaterole::pg_catalog.text,rolreplication::pg_catalog.text,rolbypassrls::pg_catalog.text,pg_catalog.pg_has_role(oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text,pg_catalog.pg_has_role(oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) %s",(actor[0],int(target[0][1]),executor_role),1)
  if len(caller)!=1 or caller[0][1:]!=('true','false','false','false','false','false','false','false'):raise ValueError('Original ordinary graph epoch private executor required')
  if _text_rows(cursor,"SELECT p.oid::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'acquire_graph_epoch_read_cut'",limit=1):raise ValueError('Existing graph epoch cut requires explicit migration')
  cursor.execute(raw.decode(),prepare=False)
  cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_graph_epoch_read_cut() TO {}').format(sql.Identifier(executor_role)),prepare=False)
  cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(executor_role)),prepare=False)
  for name in _TABLES:cursor.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(sql.Identifier('truss',name),sql.Identifier(executor_role)),prepare=False)
  result=PendingGraphEpochReadCut(target[0][0],actor[0],int(caller[0][0]),_DIGEST)
  _verify_issuer(cursor,result)
  _verify_private_permissions(cursor,result.caller_oid)
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
  if cursor.fetchmany(2)!=prior:raise ValueError('Original graph epoch installer path restoration required')
  return result
 return host._run_operation(transaction,install)


def snapshot_graph_epoch_read_context(context):
 if type(context) is not GraphEpochReadContext or type(context.comparison) is not _EpochComparison or type(context.issuer) is not PendingGraphEpochReadCut:raise ValueError('Original graph epoch comparison context required')
 source=snapshot_graph_security_source(context.source);comparison=replace(context.comparison);issuer=replace(context.issuer)
 if (any(type(v) is not str or not 1<=len(v.encode())<=bound or '\0' in v for v,bound in ((comparison.installation,1024),(comparison.epoch,256),(comparison.incarnation,1024)))
     or type(comparison.profile) is not bytes or not 1<=len(comparison.profile)<=65536
     or type(comparison.evidence) is not bytes or comparison.evidence!=source.accepted_catalog_assessment
     or type(issuer.installation_id) is not str or issuer.installation_id!=comparison.installation
     or any(type(v) is not int or not 1<=v<=4294967295 for v in (issuer.owner_oid,issuer.caller_oid)) or issuer.owner_oid==issuer.caller_oid
     or issuer.source_sha256!=_DIGEST or issuer.status!='pending_commit' or issuer.security_ready is not False
     or type(context.subject_source) is not bytes or not 1<=len(context.subject_source)<=65536
     or type(source.native_guard) is not tuple or len(source.native_guard)!=3
     or any(type(v) is not bytes or not 1<=len(v)<=32768 for v in source.native_guard[:2])
     or source.native_guard[0]!=comparison.installation.encode()
     or type(source.native_guard[2]) is not int or not 1<=source.native_guard[2]<=9223372036854775807):raise ValueError('Exact bounded graph epoch read comparisons required')
 profile=decode_owner_evidence_json(comparison.profile)
 expected={'interfaceVersion':'truss-owned-graph-source-profile/0.1-candidate','requestSha256':sha256(source.original_request).hexdigest(),'acceptedCatalogSha256':sha256(source.accepted_catalog_assessment).hexdigest(),'compilerRequestSha256':sha256(source.native_dependencies).hexdigest(),'compilerOutputSha256':sha256(source.original_response).hexdigest(),'subjectHelperSha256':sha256(context.subject_source).hexdigest()}
 if source.guarded_response is not None:
  from ._security_guarded_source import capture_guarded_source_comparison
  expected['sourceContextSha256']=capture_guarded_source_comparison(source.native_dependencies,source.guarded_response).source_sha256
 if any(profile.get(k)!=v for k,v in expected.items()):raise ValueError('Original graph epoch profile source correspondence required')
 return GraphEpochReadContext(source,comparison,issuer,bytes(context.subject_source))


def verify_held_graph_epoch_read(cursor,context):
 context=snapshot_graph_epoch_read_context(context);source=context.source;expected=context.comparison
 _verify_homes(cursor,held=True);_verify_issuer(cursor,context.issuer)
 actor=_text_rows(cursor,"SELECT r.oid::pg_catalog.text,r.rolcanlogin::pg_catalog.text,r.rolsuper::pg_catalog.text,r.rolcreatedb::pg_catalog.text,r.rolcreaterole::pg_catalog.text,r.rolreplication::pg_catalog.text,r.rolbypassrls::pg_catalog.text,(SESSION_USER OPERATOR(pg_catalog.=) CURRENT_USER)::pg_catalog.text FROM pg_catalog.pg_roles r WHERE r.rolname OPERATOR(pg_catalog.=) CURRENT_USER",limit=1)
 if actor!=[(str(context.issuer.caller_oid),'true','false','false','false','false','false','true')]:raise ValueError('Original ordinary graph epoch executor required')
 _verify_private_permissions(cursor,context.issuer.caller_oid)
 rows=_text_rows(cursor,"SELECT c.installation_id::pg_catalog.text,c.source_epoch::pg_catalog.text,r.target_incarnation::pg_catalog.text,pg_catalog.encode(r.profile_bytes,'hex'),pg_catalog.encode(r.evidence_bytes,'hex'),pg_catalog.encode(r.evidence_sha256,'hex') FROM ONLY truss.source_epoch_current c JOIN ONLY truss.source_epoch_registry r ON r.installation_id OPERATOR(pg_catalog.=) c.installation_id AND r.source_epoch OPERATOR(pg_catalog.=) c.source_epoch WHERE c.singleton_id OPERATOR(pg_catalog.=) 1",limit=1)
 if rows!=[(expected.installation,expected.epoch,expected.incarnation,expected.profile.hex(),expected.evidence.hex(),sha256(expected.evidence).hexdigest())]:raise ValueError('Original current graph source epoch required')
 release=files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()
 archives=graph_source_archives(source,release)
 rows=_text_rows(cursor,"SELECT artifact_role::pg_catalog.text,artifact_identity::pg_catalog.text,pg_catalog.encode(artifact_bytes,'hex'),pg_catalog.encode(artifact_sha256,'hex'),pg_catalog.encode(artifact_identity_sha256,'hex'),installation_id::pg_catalog.text FROM ONLY truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog.\"C\"",limit=len(archives))
 if rows!=sorted([(role,name,raw.hex(),sha256(raw).hexdigest(),sha256(name.encode()).hexdigest(),expected.installation) for role,name,raw in archives],key=lambda r:r[1]):raise ValueError('Original current graph source archive required')
 guard=source.native_guard
 if _text_rows(cursor,"SELECT pg_catalog.encode(installation_identity_bytes,'hex'),pg_catalog.encode(policy_profile_bytes,'hex'),generation::pg_catalog.text FROM ONLY truss.policy_generation_guard WHERE singleton OPERATOR(pg_catalog.=) 1",limit=1)!=[(guard[0].hex(),guard[1].hex(),str(guard[2]))]:raise ValueError('Original current graph authority guard required')
 if capture_accepted_catalog(cursor,source.original_request,existing_source_cut=True)!=source.accepted_catalog_assessment:raise ValueError('Original current graph accepted source required')


def acquire_graph_epoch_read(cursor,context):
 context=snapshot_graph_epoch_read_context(context)
 _verify_issuer(cursor,context.issuer)
 cursor.execute('SELECT truss.acquire_graph_epoch_read_cut()',prepare=False,binary=False)
 if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=2278 or cursor.fetchmany(2)!=[('',)]:raise ValueError('Exact graph epoch cut VOID result required')
 verify_held_graph_epoch_read(cursor,context)
