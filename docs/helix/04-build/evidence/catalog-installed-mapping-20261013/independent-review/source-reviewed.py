"""Original catalog source-marker installation; not protected-profile admission.

Trusted direct installation administrator and installation quiescence required.
Caller owns settlement. No repair, reuse, authority issuance or security readiness.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from ._security_mapping import PreparedSecurityMapping
from ._security_catalog_mapping import map_catalog_dependencies
from ._security_catalog_assessment import capture_accepted_catalog
from ._installation_privileges import installation_administrator_with_cursor
from .catalog_runtime import _release,_pin_cursor

@dataclass(frozen=True,slots=True)
class PendingCatalogSourceMarker:
 installation_id: str
 release_sha256: str
 inventory_sha256: str
 target_incarnation: bytes
 status: str='pending_commit'
 security_ready: bool=False


def _catalog_mapping_snapshot(mapping):
 if type(mapping) is not PreparedSecurityMapping:
  raise ValueError('Original catalog mapping archive required')
 request,response,assessment,dependencies=(mapping.original_request,mapping.original_response,
     mapping.accepted_catalog_assessment,mapping.native_dependencies)
 for raw,limit in ((request,4000000),(response,16777216),(assessment,1048576),(dependencies,16777216)):
  if type(raw) is not bytes or not 1<=len(raw)<=limit:
   raise ValueError('Exact bounded catalog mapping archive required')
 return PreparedSecurityMapping(request,response,assessment,dependencies)


def _catalog_source_archives(mapping,release):
 request,response,assessment,dependencies=(mapping.original_request,mapping.original_response,
     mapping.accepted_catalog_assessment,mapping.native_dependencies)
 if map_catalog_dependencies(assessment,response,request)!=dependencies:
  raise ValueError('Original native dependency archive correspondence required')
 return [('bundle','catalog:original-release-manifest',release),
         ('expected_inventory','catalog:original-accepted-assessment',assessment),
         ('installed_inventory','catalog:recaptured-accepted-assessment',assessment),
         ('input','catalog:original-mapping-request',request),
         ('input','catalog:original-compiler-handoff',response),
         ('input','catalog:original-native-dependencies',dependencies)]


def verify_catalog_source_archive_with_cursor(cursor,mapping,installation):
 """Exact installed source comparison under a held cut, not issuer authentication."""
 mapping=_catalog_mapping_snapshot(mapping)
 release=files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()
 archives=_catalog_source_archives(mapping,release)
 cursor.execute('LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT',prepare=False)
 cursor.execute('SELECT artifact_role,artifact_identity,artifact_bytes,artifact_sha256,artifact_identity_sha256,installation_id FROM ONLY truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog."C"',prepare=False)
 if (cursor.description is None or tuple(d.name for d in cursor.description)!=('artifact_role','artifact_identity','artifact_bytes','artifact_sha256','artifact_identity_sha256','installation_id')
     or tuple(d.type_code for d in cursor.description)!=(25,25,17,17,17,25)):
  raise ValueError('Exact catalog source archive descriptors required')
 expected=sorted([(role,name,raw,sha256(raw).digest(),sha256(name.encode()).digest(),installation) for role,name,raw in archives],key=lambda row:row[1])
 rows=cursor.fetchmany(len(expected)+1)
 if (any(tuple(type(v) for v in row)!=(str,str,bytes,bytes,bytes,str) for row in rows) or rows!=expected):
  raise ValueError('Original installed catalog mapping archive required')


def bootstrap_catalog_source_marker_in_transaction(host,transaction,mapping):
 if type(host) is not PsycopgHost or type(mapping) is not PreparedSecurityMapping:
  return Error(ExecutionFailure('execution_obligation','Original catalog source installation required'))
 try:mapping=_catalog_mapping_snapshot(mapping)
 except ValueError:
  return Error(ExecutionFailure('execution_obligation','Exact bounded catalog mapping archive required'))
 request=mapping.original_request;assessment=mapping.accepted_catalog_assessment
 if type(request) is not bytes or type(assessment) is not bytes or not 1<=len(request)<=4000000 or not 1<=len(assessment)<=1048576:
  return Error(ExecutionFailure('execution_obligation','Exact bounded original catalog sources required'))
 def install(cursor,observed):
  _pin_cursor(cursor);manifest,digest,_=_release()
  cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
  paths=cursor.fetchmany(2)
  if len(paths)!=1 or type(paths[0][0]) is not str:raise ValueError('Original installer search path required')
  original_path=paths[0][0]
  cursor.execute("SELECT pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only'),pg_catalog.current_setting('server_version_num')",prepare=False)
  if cursor.fetchmany(2)!=[('read committed','off',manifest['postgresVersion'])]:raise ValueError('Original read-write read-committed catalog server required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  if cursor.fetchmany(2)!=[('pg_catalog, pg_temp',)]:raise ValueError('Pinned installer search path required')
  release=files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()
  if sha256(release).hexdigest()!=digest:raise ValueError('Original catalog release bytes required')
  cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR UPDATE',prepare=False)
  if len(cursor.fetchmany(2))!=1:raise ValueError('Original catalog installation head required')
  cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE',prepare=False)
  rows=cursor.fetchmany(2)
  if len(rows)!=1:raise ValueError('Unique original catalog installation required')
  identity,owner=rows[0];installation_administrator_with_cursor(cursor,owner)
  if capture_accepted_catalog(cursor,request)!=assessment:raise ValueError('Original accepted catalog source correspondence required')
  cursor.execute("SELECT (SELECT count(*) FROM truss.installation_marker),(SELECT count(*) FROM truss.installation_archive),(SELECT count(*) FROM truss.source_epoch_registry),(SELECT count(*) FROM truss.source_epoch_current)",prepare=False)
  if cursor.fetchmany(2)!=[(0,0,0,0)]:raise ValueError('Existing catalog source installation requires migration; no repair')
  cursor.execute("SELECT d.oid::text,d.datname::text,n.oid::text,clock_timestamp()::text FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n WHERE d.datname=current_database() AND n.nspname='truss'",prepare=False)
  target=cursor.fetchmany(2)
  if len(target)!=1 or any(type(v) is not str for v in target[0]):raise ValueError('Original catalog namespace observation required')
  db_oid,db_name,schema_oid,clock=target[0]
  incarnation=json.dumps({'interfaceVersion':'truss-catalog-source-target/0.1.0','databaseOid':db_oid,'schemaOid':schema_oid},sort_keys=True,separators=(',',':')).encode()
  inventory_digest=sha256(assessment).hexdigest()
  cursor.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0',%s,%s,%s,'truss-accepted-catalog/0.1.0',%s,%s,'truss',%s::timestamptz,%s)",(identity,manifest['releaseId'],bytes.fromhex(digest),bytes.fromhex(inventory_digest),json.dumps({'databaseOid':db_oid,'databaseName':db_name},sort_keys=True,separators=(',',':')),clock,clock),prepare=False)
  archives=_catalog_source_archives(mapping,release)
  for role,name,raw in archives:
   cursor.execute('INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES(%s,%s,%s,%s,%s)',(identity,role,name,raw,sha256(name.encode()).digest()),prepare=False)
  cursor.execute("SELECT marker_interface_version,installation_id,layout_version,bundle_sha256,inventory_profile,inventory_sha256,database_identity,schema_name,installed_at_text,(installed_at=installed_at_text::timestamptz)::text FROM truss.installation_marker WHERE singleton_id=1",prepare=False)
  expected_marker=('truss-bootstrap-marker/0.1.0',identity,manifest['releaseId'],bytes.fromhex(digest),'truss-accepted-catalog/0.1.0',bytes.fromhex(inventory_digest),json.dumps({'databaseOid':db_oid,'databaseName':db_name},sort_keys=True,separators=(',',':')),'truss',clock,'true')
  if cursor.fetchmany(2)!=[expected_marker]:raise ValueError('Exact original catalog source marker readback required')
  cursor.execute('SELECT artifact_role,artifact_identity,artifact_bytes,artifact_sha256,artifact_identity_sha256,installation_id FROM truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog."C"',prepare=False)
  expected_archives=sorted([(role,name,raw,sha256(raw).digest(),sha256(name.encode()).digest(),identity) for role,name,raw in archives],key=lambda row:row[1])
  if cursor.fetchmany(len(expected_archives)+1)!=expected_archives:raise ValueError('Exact original catalog source archive readback required')
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
  if cursor.fetchmany(2)!=[(original_path,)]:raise ValueError('Original installer search path restoration required')
  return PendingCatalogSourceMarker(identity,digest,inventory_digest,incarnation)
 return host._run_operation(transaction,install)
