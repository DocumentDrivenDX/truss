"""Original catalog-source factory issuance, not complete protected admission.

Direct trusted administrator, genuine source/installer custody and administrative
quiescence remain premises. Caller owns commit. Source epochs describe metadata;
current data authority generation remains a separate checked read prerequisite.
"""
from dataclasses import dataclass,replace
from hashlib import sha256
import json
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor,_release
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_source_installation import (PendingCatalogSourceMarker,
    _catalog_mapping_snapshot,verify_catalog_source_archive_with_cursor)
from ._security_catalog_assessment import capture_accepted_catalog
from ._security_source_epoch_installation import (PendingSourceEpochInfrastructure,
    _sources,_verify,_MANIFEST_SHA256,_text_rows)
from ._security_catalog_source_binding import derive_catalog_source_epoch_profile
from ._psycopg_epoch_cut import _EpochComparison,_DDLBarrierComparison
from ._psycopg_fact_cut import _prepare_fenced_fact_cut,_FactRelationComparison,_FactColumnComparison

@dataclass(frozen=True,slots=True)
class PendingCatalogSourceEpoch:
 comparison:_EpochComparison
 barrier:_DDLBarrierComparison
 status:str='pending_commit'
 security_ready:bool=False


def issue_initial_catalog_source_epoch_in_transaction(host,transaction,*,mapping,marker,infrastructure,fact_relations,subject_source):
 if type(host) is not PsycopgHost or type(marker) is not PendingCatalogSourceMarker or type(infrastructure) is not PendingSourceEpochInfrastructure:
  return Error(ExecutionFailure('execution_obligation','Original catalog source factory inputs required'))
 try:
  guard=mapping.native_guard;mapping=_catalog_mapping_snapshot(mapping)
  marker=replace(marker);infrastructure=replace(infrastructure,barrier=replace(infrastructure.barrier))
  if (type(guard) is not tuple or len(guard)!=3 or any(type(v) is not bytes or not 1<=len(v)<=32768 for v in guard[:2])
      or type(guard[2]) is not int or not 1<=guard[2]<=9223372036854775807
      or type(marker.installation_id) is not str or not 1<=len(marker.installation_id.encode())<=1024
      or marker.status!='pending_commit' or marker.security_ready is not False
      or infrastructure.status!='pending_commit' or infrastructure.security_ready is not False
      or infrastructure.installation_id!=marker.installation_id
      or infrastructure.source_manifest_sha256!=_MANIFEST_SHA256
      or type(marker.target_incarnation) is not bytes or not 1<=len(marker.target_incarnation)<=1024
      or type(fact_relations) is not tuple or not 1<=len(fact_relations)<=32
      or any(type(r) is not _FactRelationComparison or type(r.columns) is not tuple or len(r.columns)>1600 or any(type(c) is not _FactColumnComparison for c in r.columns) for r in fact_relations)):
   raise ValueError('Original bounded catalog source factory comparison required')
  fact_relations=tuple(replace(r,columns=tuple(replace(c) for c in r.columns)) for r in fact_relations)
  profile=derive_catalog_source_epoch_profile(mapping,fact_relations,infrastructure.barrier,subject_source=subject_source)
  sources=_sources()
 except (ValueError,TypeError,AttributeError):
  return Error(ExecutionFailure('execution_obligation','Original bounded catalog source factory comparison required'))
 def issue(cursor,observed):
  _pin_cursor(cursor);manifest,digest,_=_release()
  prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
  if len(prior)!=1 or type(prior[0][0]) is not str:raise ValueError('Original source factory caller path required')
  cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
  if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num')::text,pg_catalog.current_setting('transaction_isolation')::text,pg_catalog.current_setting('transaction_read_only')::text,pg_catalog.current_setting('event_triggers')::text",limit=1)!=[('180006','read committed','off','on')]:raise ValueError('Original supported source factory transaction required')
  cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',prepare=False)
  installed=cursor.fetchmany(2)
  if len(installed)!=1 or installed[0][0]!=marker.installation_id:raise ValueError('Original source factory installation required')
  actor=installation_administrator_with_cursor(cursor,installed[0][1])
  if actor[0]!=infrastructure.barrier.owner_oid:raise ValueError('Original source factory handler owner required')
  if _text_rows(cursor,'SELECT release_id::text,release_sha256::text FROM truss.runtime_current_installation()',limit=1)!=[(manifest['releaseId'],digest)]:raise ValueError('Original source factory release required')
  if marker.release_sha256!=digest or marker.inventory_sha256!=sha256(mapping.accepted_catalog_assessment).hexdigest():raise ValueError('Original source factory marker sources required')
  verify_catalog_source_archive_with_cursor(cursor,mapping,marker.installation_id)
  if capture_accepted_catalog(cursor,mapping.original_request)!=mapping.accepted_catalog_assessment:raise ValueError('Original source factory current catalog required')
  def current_guard():
   cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1 FOR SHARE NOWAIT',prepare=False)
   if cursor.description is None or tuple(d.name for d in cursor.description)!=('installation_identity_bytes','policy_profile_bytes','generation') or tuple(d.type_code for d in cursor.description)!=(17,17,20):raise ValueError('Exact source factory native guard descriptors required')
   rows=cursor.fetchmany(2)
   if len(rows)!=1 or tuple(type(v) for v in rows[0])!=(bytes,bytes,int) or rows!=[guard] or guard[0]!=marker.installation_id.encode():raise ValueError('Original source factory current guard required')
  current_guard()
  barrier=_verify(cursor,sources,actor[0])
  if barrier!=infrastructure.barrier:raise ValueError('Original source factory barrier required')
  target=_text_rows(cursor,"SELECT d.oid::text,n.oid::text,d.datname::text FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n WHERE d.datname=current_database() AND n.nspname='truss'",limit=1)
  if len(target)!=1:raise ValueError('Original source factory target required')
  incarnation=json.dumps({'interfaceVersion':'truss-catalog-source-target/0.1.0','databaseOid':target[0][0],'schemaOid':target[0][1]},sort_keys=True,separators=(',',':')).encode()
  if incarnation!=marker.target_incarnation:raise ValueError('Original source factory incarnation required')
  database_identity=json.dumps({'databaseOid':target[0][0],'databaseName':target[0][2]},sort_keys=True,separators=(',',':'))
  if _text_rows(cursor,"SELECT installation_id::text,layout_version::text,encode(bundle_sha256,'hex')::text,inventory_profile::text,encode(inventory_sha256,'hex')::text,schema_name::text,database_identity::text FROM truss.installation_marker WHERE singleton_id=1 FOR UPDATE NOWAIT",limit=1)!=[(marker.installation_id,manifest['releaseId'],digest,'truss-accepted-catalog/0.1.0',marker.inventory_sha256,'truss',database_identity)]:raise ValueError('Original source factory native marker required')
  cursor.execute('LOCK TABLE truss.source_epoch_current,truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT',prepare=False)
  if _text_rows(cursor,'SELECT (SELECT count(*) FROM truss.source_epoch_current)::text,(SELECT count(*) FROM truss.source_epoch_registry)::text',limit=1)!=[('0','0')]:raise ValueError('Existing source factory epoch requires explicit transition')
  def produce(c):
   c.execute('SELECT truss.runtime_issue_source_epoch(%s,NULL,%s,%s,%s)',(marker.installation_id,incarnation.decode(),profile,mapping.accepted_catalog_assessment),prepare=False,binary=False)
   if c.description is None or len(c.description)!=1 or c.description[0].type_code!=25:raise ValueError('Exact issued source epoch descriptor required')
   rows=c.fetchmany(2)
   if len(rows)!=1 or type(rows[0][0]) is not str or not 1<=len(rows[0][0])<=256:raise ValueError('Original issued source epoch required')
   epoch=rows[0][0]
   current=_text_rows(c,'SELECT c.installation_id::text,c.source_epoch::text,r.target_incarnation::text,encode(r.profile_bytes,\'hex\')::text,encode(r.evidence_bytes,\'hex\')::text,r.predecessor_epoch::text,r.transition_reason::text FROM truss.source_epoch_current c JOIN truss.source_epoch_registry r ON r.installation_id=c.installation_id AND r.source_epoch=c.source_epoch WHERE c.singleton_id=1',limit=1)
   if current!=[(marker.installation_id,epoch,incarnation.decode(),profile.hex(),mapping.accepted_catalog_assessment.hex(),None,'initial')]:raise ValueError('Exact original source factory epoch readback required')
   current_guard()
   if _verify(c,sources,actor[0])!=barrier:raise ValueError('Original source factory infrastructure changed')
   verify_catalog_source_archive_with_cursor(c,mapping,marker.installation_id)
   if capture_accepted_catalog(c,mapping.original_request)!=mapping.accepted_catalog_assessment:raise ValueError('Original source factory catalog changed')
   return epoch
  epoch=_prepare_fenced_fact_cut(fact_relations,produce)(cursor)
  cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
  if cursor.fetchmany(2)!=[(prior[0][0],)]:raise ValueError('Original source factory path restoration required')
  return PendingCatalogSourceEpoch(_EpochComparison(marker.installation_id,epoch,incarnation.decode(),profile,mapping.accepted_catalog_assessment),barrier)
 return host._run_operation(transaction,issue)
