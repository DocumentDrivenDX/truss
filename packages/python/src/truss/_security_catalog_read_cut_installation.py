# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original selected read-table lock issuer; no complete source/backend admission."""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from psycopg import sql
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_subject_installation import _text_rows


def verify_held_catalog_read_table_cut_with_cursor(cursor):
 tables=('object','catalog_subject_map','installation_archive','source_epoch_current','source_epoch_registry','policy_generation_guard')
 query="SELECT c.relname::pg_catalog.text,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.locktype OPERATOR(pg_catalog.=) 'relation' AND l.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND l.database OPERATOR(pg_catalog.=) (SELECT oid FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()) AND l.relation OPERATOR(pg_catalog.=) c.oid AND l.mode OPERATOR(pg_catalog.=) 'ShareLock' AND l.granted)::pg_catalog.text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND c.relname OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.text[]) ORDER BY c.relname"
 rows=_text_rows(cursor,query,(list(tables),),6)
 if rows!=[(name,'r','p','true') for name in sorted(tables)]:raise ValueError('Original held selected catalog read table cut required')


def verify_catalog_read_table_cut_issuer_with_cursor(cursor,*,owner_oid,caller_oid):
 """Exact original native issuer comparison; caller must hold its DDL/source cut."""
 if any(type(oid) is not int or not 1<=oid<=4294967295 for oid in (owner_oid,caller_oid)) or owner_oid==caller_oid:raise ValueError('Exact distinct catalog read table cut issuer identities required')
 source=files('truss').joinpath('_security_bootstrap','catalog-read-table-cut.sql').read_bytes()
 body=source.decode().split('AS $$',1)[1].split('$$;',1)[0]
 rows=_text_rows(cursor,"SELECT p.proowner::pg_catalog.text,l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,p.proretset::pg_catalog.text,p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,p.proparallel::pg_catalog.text,p.proleakproof::pg_catalog.text,p.prosupport::pg_catalog.oid::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,(p.prosqlbody IS NULL)::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'acquire_catalog_read_table_cut' AND p.pronargs OPERATOR(pg_catalog.=) 0",limit=1)
 if rows!=[(str(owner_oid),'plpgsql','f','0','','2278','false','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,'true')]:raise ValueError('Exact original catalog read table cut issuer definition required')
 owner=_text_rows(cursor,'SELECT rolsuper::pg_catalog.text FROM pg_catalog.pg_roles WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid',(owner_oid,),1)
 if owner!=[('true',)]:raise ValueError('Original privileged catalog read table cut issuer owner required')
 grants=_text_rows(cursor,"SELECT a.grantee::pg_catalog.text,a.grantor::pg_catalog.text,a.privilege_type::pg_catalog.text,a.is_grantable::pg_catalog.text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid OPERATOR(pg_catalog.=) 'truss.acquire_catalog_read_table_cut()'::pg_catalog.regprocedure ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable",limit=2)
 if grants!=sorted([(str(owner_oid),str(owner_oid),'EXECUTE','false'),(str(caller_oid),str(owner_oid),'EXECUTE','false')],key=lambda r:int(r[0])):raise ValueError('Exact private catalog read table cut issuer ACL required')


def acquire_issued_catalog_read_table_cut_with_cursor(cursor,*,owner_oid,caller_oid):
 """Verified fixed issuer; original owner/caller custody and held DDL cut required."""
 verify_catalog_read_table_cut_issuer_with_cursor(cursor,owner_oid=owner_oid,caller_oid=caller_oid)
 current=_text_rows(cursor,'SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) CURRENT_USER',limit=1)
 if current!=[(str(caller_oid),)]:raise ValueError('Original native catalog read table cut executor required')
 cursor.execute('SELECT truss.acquire_catalog_read_table_cut()',prepare=False,binary=False)
 if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=2278 or cursor.fetchmany(2)!=[('',)]:raise ValueError('Exact native catalog read table cut issuer VOID result required')
 verify_held_catalog_read_table_cut_with_cursor(cursor)
 verify_catalog_read_table_cut_issuer_with_cursor(cursor,owner_oid=owner_oid,caller_oid=caller_oid)


@dataclass(frozen=True,slots=True)
class PendingCatalogReadTableCutIssuer:
 installation_id:str
 owner_oid:int
 caller_oid:int
 source_sha256:str
 status:str='pending_commit'
 security_ready:bool=False


def bootstrap_catalog_read_table_cut_issuer_in_transaction(host,transaction,*,executor_role):
 """Fresh trusted administrator install; caller owns commit and DDL quiescence."""
 if type(host) is not PsycopgHost or type(executor_role) is not str or not executor_role or '\0' in executor_role or len(executor_role.encode())>63:
  return Error(ExecutionFailure('execution_obligation','Original bounded catalog read table cut executor required'))
 executor_role=str(executor_role)
 source=files('truss').joinpath('_security_bootstrap','catalog-read-table-cut.sql').read_bytes()
 source_sha=sha256(source).hexdigest()
 def install(cursor,observed):
  _pin_cursor(cursor)
  prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
  if len(prior)!=1:raise ValueError('Original catalog read table cut installer path required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  from ._current_query_protection import require_unprotected_configuration
  require_unprotected_configuration(cursor,allow_uninstalled=True)
  if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num')::pg_catalog.text,pg_catalog.current_setting('transaction_isolation')::pg_catalog.text,pg_catalog.current_setting('transaction_read_only')::pg_catalog.text",limit=1)!=[('180006','read committed','off')]:raise ValueError('Original supported catalog read table cut installation transaction required')
  target=_text_rows(cursor,'SELECT installation_id::pg_catalog.text,owner_oid::pg_catalog.text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',limit=1)
  if len(target)!=1:raise ValueError('Original catalog read table cut installation required')
  installation_administrator_with_cursor(cursor,int(target[0][1]))
  owner=_text_rows(cursor,"SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) CURRENT_USER AND rolsuper",limit=1)
  if len(owner)!=1:raise ValueError('Original privileged catalog read table cut installer required')
  owner_oid=int(owner[0][0])
  caller=_text_rows(cursor,"SELECT oid::pg_catalog.text,rolcanlogin::pg_catalog.text,rolsuper::pg_catalog.text,rolcreatedb::pg_catalog.text,rolcreaterole::pg_catalog.text,rolreplication::pg_catalog.text,rolbypassrls::pg_catalog.text,pg_catalog.pg_has_role(oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) %s",(owner_oid,executor_role),1)
  if len(caller)!=1 or caller[0][1:]!=('true','false','false','false','false','false','false'):raise ValueError('Original ordinary catalog read table cut executor required')
  caller_oid=int(caller[0][0])
  existing=_text_rows(cursor,"SELECT p.oid::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'acquire_catalog_read_table_cut'",limit=1)
  if existing:raise ValueError('Existing catalog read table cut issuer requires explicit migration')
  cursor.execute(source.decode(),prepare=False)
  cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_catalog_read_table_cut() TO {}').format(sql.Identifier(executor_role)),prepare=False)
  cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(executor_role)),prepare=False)
  verify_catalog_read_table_cut_issuer_with_cursor(cursor,owner_oid=owner_oid,caller_oid=caller_oid)
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
  return PendingCatalogReadTableCutIssuer(target[0][0],owner_oid,caller_oid,source_sha)
 return host._run_operation(transaction,install)
