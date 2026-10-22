# SPDX-License-Identifier: MIT OR Apache-2.0
"""One-time selected native epoch/barrier installation, not protected admission.

Trusted direct superuser installer, administrative quiescence and original
installation are premises. Native handler ownership stays with that excluded
administrator. Caller owns settlement; no grants, reuse, repair or migration.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _release,_pin_cursor
from ._installation_privileges import installation_administrator_with_cursor, require_empty_managed_grants_with_cursor
from ._psycopg_epoch_cut import _DDLBarrierComparison

_FUNCTIONS=(
 ('immutability.sql','runtime_immutable_source_epoch','','2279','false'),
 ('lock.sql','runtime_lock_source_epoch','25 25 25','2249','true'),
 ('issue.sql','runtime_issue_source_epoch','25 25 25 17 17','25','false'),
 ('fresh-lock.sql','runtime_lock_fresh_source_epoch','25 25 25','2249','true'),
 ('read-fence.sql','runtime_fence_selected_epoch_writes','','2279','false'),
 ('fenced-fresh-lock.sql','runtime_lock_fenced_fresh_source_epoch','25 25 25','2249','true'),
 ('routine-ddl-barrier.sql','runtime_fence_routine_ddl_writer','','3838','false'))
_EVENTS=(
 ('truss_routine_ddl_writer_barrier',['CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION','CREATE PROCEDURE','ALTER PROCEDURE','DROP PROCEDURE']),
 ('truss_schema_ddl_writer_barrier',['CREATE SCHEMA','ALTER SCHEMA','DROP SCHEMA']),
 ('truss_database_ddl_writer_barrier',None),
 ('truss_table_ddl_writer_barrier',['CREATE TABLE','ALTER TABLE','DROP TABLE']),
 ('truss_z_routine_ddl_writer_barrier',['ALTER ROUTINE']))

@dataclass(frozen=True,slots=True)
class PendingSourceEpochInfrastructure:
 installation_id:str
 source_manifest_sha256:str
 barrier:_DDLBarrierComparison
 status:str='pending_commit'
 security_ready:bool=False


def _sources():
 root=files('truss').joinpath('_security_source_epoch')
 raw=root.joinpath('manifest.json').read_bytes()
 manifest=json.loads(raw);sources=[]
 for name,digest in manifest['sources'].items():
  source=root.joinpath(name).read_bytes()
  if sha256(source).hexdigest()!=digest:raise ValueError('Original source epoch SQL bytes required')
  sources.append((name,source.decode('utf8')))
 return tuple(sources),sha256(raw).hexdigest()


def _text_rows(cursor,query,params=(),limit=16):
 cursor.execute(query,params,prepare=False,binary=False)
 if cursor.description is None or any(d.type_code!=25 for d in cursor.description):
  raise ValueError('Exact source epoch inventory TEXT descriptors required')
 rows=cursor.fetchmany(limit+1)
 if len(rows)>limit or any(any(type(v) is not str and v is not None for v in row) for row in rows):
  raise ValueError('Bounded exact source epoch inventory required')
 return rows


def _verify(cursor,sources,actor):
 bodies={name:source.split('AS $$',1)[1].split('$$;',1)[0] for name,source in sources if name in {s[0] for s in _FUNCTIONS}}
 oids={}
 for file,name,args,return_oid,returns_set in _FUNCTIONS:
  rows=_text_rows(cursor,"SELECT p.oid::text,p.proowner::text,l.lanname::text,p.prokind::text,p.proargtypes::text,p.prorettype::text,p.proretset::text,p.prosecdef::text,p.provolatile::text,p.proparallel::text,p.proisstrict::text,p.proleakproof::text,p.prosupport::oid::text,pg_catalog.to_jsonb(p.proconfig)::text,p.prosrc FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE n.nspname='truss' AND p.proname=%s",(name,),1)
  expected=(str(actor),'plpgsql','f',args,return_oid,returns_set,'false','v','u','false','false','0','["search_path=pg_catalog, pg_temp"]',bodies[file])
  if len(rows)!=1 or rows[0][1:]!=expected:raise ValueError('Exact installed source epoch routine required')
  oid=rows[0][0];oids[name]=oid
  acl=_text_rows(cursor,"SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid=%s::oid ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable",(oid,),2)
  if acl!=[(str(actor),str(actor),'EXECUTE','false')]:raise ValueError('Exact private source epoch routine ACL required')
 events=_text_rows(cursor,"SELECT evtname::text,evtevent::text,evtenabled::text,evtowner::text,evtfoid::text,pg_catalog.to_jsonb(evttags)::text FROM pg_catalog.pg_event_trigger WHERE evtname=ANY(%s) ORDER BY evtname",([name for name,tags in _EVENTS],),5)
 expected=sorted([(name,'ddl_command_start','A',str(actor),oids['runtime_fence_routine_ddl_writer'],None if tags is None else json.dumps(tags)) for name,tags in _EVENTS])
 if events!=expected:raise ValueError('Exact installed source epoch event hooks required')
 triggers=_text_rows(cursor,"SELECT c.relname::text,t.tgname::text,t.tgfoid::text,t.tgenabled::text,t.tgtype::text,t.tgnargs::text,encode(t.tgargs,'hex')::text,(t.tgqual IS NULL)::text,t.tgisinternal::text,t.tgconstraint::text,t.tgdeferrable::text,t.tginitdeferred::text FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname IN ('source_epoch_current','source_epoch_registry') AND NOT t.tgisinternal ORDER BY c.relname,t.tgname",limit=4)
 def hook(table,name,routine,event):return (table,name,oids[routine],'A',event,'0','','true','false','0','false','false')
 expected=sorted([
  hook('source_epoch_current','runtime_selected_epoch_write_fence','runtime_fence_selected_epoch_writes','62'),
  hook('source_epoch_registry','runtime_selected_epoch_write_fence','runtime_fence_selected_epoch_writes','62'),
  hook('source_epoch_registry','runtime_source_epoch_immutable','runtime_immutable_source_epoch','27'),
  hook('source_epoch_registry','runtime_source_epoch_no_truncate','runtime_immutable_source_epoch','34')])
 if triggers!=expected:raise ValueError('Exact installed source epoch table hooks required')
 return _DDLBarrierComparison(actor,int(oids['runtime_fence_routine_ddl_writer']),bodies['routine-ddl-barrier.sql'],include_alter_routine=True,include_schema_ddl=True,include_database_ddl=True)


def bootstrap_source_epoch_infrastructure_in_transaction(host,transaction,*,installation_identity):
 if type(host) is not PsycopgHost or type(installation_identity) is not bytes or not 1<=len(installation_identity)<=1024:
  return Error(ExecutionFailure('execution_obligation','Original bounded source epoch installation required'))
 # All original packaged source bytes are captured before host/native callbacks.
 try:sources,source_manifest_sha256=_sources()
 except ValueError:return Error(ExecutionFailure('execution_obligation','Original source epoch installation sources required'))
 def install(cursor,observed):
  _pin_cursor(cursor);manifest,digest,_=_release()
  require_empty_managed_grants_with_cursor(cursor,'Source epoch')
  paths=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
  if len(paths)!=1:raise ValueError('Original source epoch caller path required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  settings=_text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num')::text,pg_catalog.current_setting('transaction_isolation')::text,pg_catalog.current_setting('transaction_read_only')::text,pg_catalog.current_setting('event_triggers')::text",limit=1)
  if settings!=[('180006','read committed','off','on')]:raise ValueError('Supported read-write read-committed source epoch server required')
  cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR UPDATE NOWAIT',prepare=False)
  if len(cursor.fetchmany(2))!=1:raise ValueError('Original source epoch installation head required')
  cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',prepare=False)
  rows=cursor.fetchmany(2)
  if len(rows)!=1 or rows[0][0].encode('utf8')!=installation_identity:raise ValueError('Original source epoch installation identity required')
  actor=installation_administrator_with_cursor(cursor,rows[0][1])
  if not actor[2]:raise ValueError('Direct superuser source epoch installer required')
  if _text_rows(cursor,'SELECT release_id::text,release_sha256::text FROM truss.runtime_current_installation()',limit=1)!=[(manifest['releaseId'],digest)]:raise ValueError('Original source epoch installed release required')
  markers=_text_rows(cursor,'SELECT installation_id::text,layout_version::text,encode(bundle_sha256,\'hex\')::text FROM truss.installation_marker WHERE singleton_id=1 FOR UPDATE NOWAIT',limit=1)
  if markers!=[(rows[0][0],manifest['releaseId'],digest)]:raise ValueError('Original catalog source marker required')
  cursor.execute('LOCK TABLE truss.source_epoch_current,truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT',prepare=False)
  if _text_rows(cursor,'SELECT (SELECT count(*) FROM truss.source_epoch_current)::text,(SELECT count(*) FROM truss.source_epoch_registry)::text',limit=1)!=[('0','0')]:raise ValueError('Existing source epochs require explicit migration')
  if _text_rows(cursor,"SELECT p.proname::text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.proname=ANY(%s)",([s[1] for s in _FUNCTIONS],),7):raise ValueError('Existing source epoch routines require explicit migration')
  if _text_rows(cursor,'SELECT evtname::text FROM pg_catalog.pg_event_trigger WHERE evtname=ANY(%s)',([e[0] for e in _EVENTS],),5):raise ValueError('Existing source epoch hooks require explicit migration')
  for name,source in sources:cursor.execute(source,prepare=False)
  _pin_cursor(cursor);cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  barrier=_verify(cursor,sources,actor[0])
  if _text_rows(cursor,"SELECT pg_catalog.current_setting('event_triggers')::text",limit=1)!=[('on',)]:raise ValueError('Original source epoch hooks unavailable')
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(paths[0][0],),prepare=False)
  if cursor.fetchmany(2)!=[(paths[0][0],)]:raise ValueError('Original source epoch caller path restoration required')
  return PendingSourceEpochInfrastructure(rows[0][0],source_manifest_sha256,barrier)
 return host._run_operation(transaction,install)
