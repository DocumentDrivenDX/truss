"""Public catalog runtime over caller-owned psycopg transactions.

The selected runtime provides accepted scalar catalogs, graph groups and reads,
imports, retained history, receipts, feeds and additive candidate upgrades.
Ordinary-person catalog calls require READ COMMITTED, so authorization reads
observe committed membership changes. Higher isolation returns a refusal.
"""
from __future__ import annotations
from ._catalog_source_reference import REFERENCE08_PROFILE,RECURSIVE08_PROFILE,SOURCE_REFERENCE_FORMAT,compact_catalog_sources
from dataclasses import dataclass, replace
from hashlib import sha256
from importlib.resources import files
import json
import re
import base64
from uuid import uuid4
from threading import RLock
from functools import wraps
from typing import Literal, overload, TypeVar, Mapping
from .catalog_results import (CatalogRegistration, CatalogUnchanged, CatalogAcceptanceRefused, CatalogCompatibilityViolation, CatalogRelationshipCompatibilityViolation, CatalogKeyCompatibilityViolation, CatalogReport)
from .capabilities import (CapabilityAvailable, NativeCatalogCapability,
    NativeDirectReadCapability, NativeImportCapability, NativeFeedCapability, NativeHistoryCapability, NativeCompiledExecutionCapability)
from .history import (HistoryEntity,HistoryCursor,RetainedHistoryEvent,HistoryPage,
    HistoricalRecord,HistoricalDeleted,HistoryUnavailable)
from .import_source import ImportSourceFound,ImportSourceAbsent,ImportSourceUnavailable
from .feed import FeedAckReceipt,FeedReceiptAcknowledged,FeedAckReconciled,FeedPage,FeedConsumer,FeedAcknowledged,FeedUnavailable
from .reader_catalog import ReaderCatalog, AcceptedDocument, CatalogRefused, CatalogInvalid, CatalogUnavailable
from .assembly_contracts import AssemblyDisposed, CapabilityUnavailable
from .catalog_view import CatalogViewRequest, CatalogViewAvailable, CatalogViewUnavailable, CatalogDefinitionReference
from .imports import ImportInput,ImportExecutionResult,ObjectImportRecord,EdgeImportRecord
from .import_runtime import ImportRuntimeContext
from .groups import AuthoredValue
from .contracts import MapValue, TextValue, BooleanValue
from .receipt_visibility import ReceiptIncluded,ReceiptVisibilityUnavailable
from .edge_read import ScalarEdge,EdgeFound,EdgeNotFound,EdgePage,EdgePageCursor
from .traversal import TraversalHop, TraversalComplete, TraversalLimited
from .contracts import TypedIdentity
from .object_read import ScalarObject, ObjectFound, ObjectNotFound, ObjectReadInvalid, ObjectReadUnavailable, ObjectPage, ObjectPageCursor
from ._group_runtime import GroupRuntimeContext, NativeGroupCapability, GroupCapabilityAvailable
from .contracts import CapabilitySelection, TypedIdentity, ProfilePin
from .groups import GroupSemanticInput, GroupRequestSelection, GroupApplicationResult, OrderKey
from decimal import Decimal
from .query import QueryRows,QueryRefused,QueryUnavailable,QueryPage,QueryPageCursor
from .execution import Ok, Error, ExecutionFailure, Outcome, TransactionHandle
from .psycopg_host import PsycopgHost
from .preparation import CatalogDocument, PreparedAcceptance, prepare_acceptance, prepare_core08_acceptance, _require_original_preparation
from ._catalog_support import DECIMAL207_PROFILE,DECIMAL208_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,evaluate_catalog_support, CORE08_PROFILE, RETAINED_METADATA_PROFILE, SCALAR_PROFILE, NAMED_SCALAR_PROFILE, NAMED_RELATIONSHIP_PROFILE
from ._catalog_report_semantics import compose_original_catalog_report_semantics, canonical_numeric_free


@dataclass(frozen=True,slots=True)
class CatalogRuntimeConfiguration:
    assembly_id: str = 'catalog'
    schema: str = 'truss'

@dataclass(frozen=True,slots=True)
class PendingCatalogInstallation:
    installation_id: str
    owner_role: str
    registrar_role: str
    release_id: str
    status: str = 'pending_commit'

@dataclass(frozen=True,slots=True)
class PendingRuntimeUpgrade:
    installation_id: str
    previous_release_id: str
    release_id: str
    outcome: Literal['upgraded','unchanged']
    status: Literal['pending_commit']='pending_commit'

@dataclass(frozen=True,slots=True)
class CatalogRuntimeStatus:
    installed: bool
    installation_id: str | None = None
    revision: int | None = None
    capabilities: tuple[str,...] = ()
    release_id: str | None = None
    release_sha256: str | None = None
    layout_profile: ProfilePin | None = None

@dataclass(frozen=True,slots=True)
class ModuleAccessGrant:
    document_id: str
    module_id: str
    reader_role: str
    writer_role: str

    def __post_init__(self) -> None:
        for value in (self.document_id,self.module_id,self.reader_role,self.writer_role):
            if type(value) is not str or not value or '\0' in value or len(value.encode('utf-8'))>4096:
                raise ValueError('Exact nonempty module grant identities required')
        if self.reader_role==self.writer_role:raise ValueError('Reader and writer roles must differ')
        if any(len(role.encode('utf-8'))>63 for role in (self.reader_role,self.writer_role)):
            raise ValueError('Native role names must fit 63 UTF-8 bytes')


@dataclass(frozen=True,slots=True)
class PendingModuleAccessConfiguration:
    grants: tuple[ModuleAccessGrant,...]
    status: str = 'pending_commit'


def _pin_cursor(cursor):
    from psycopg.types.string import (TextLoader, ByteaLoader, StrDumperUnknown,
        StrBinaryDumper, BytesDumper, BytesBinaryDumper)
    from psycopg.types.bool import BoolLoader
    from psycopg.types.numeric import IntLoader, IntDumper, IntBinaryDumper
    for oid in (18,19,25):cursor.adapters.register_loader(oid,TextLoader)
    for oid in (20,21,23,26):cursor.adapters.register_loader(oid,IntLoader)
    cursor.adapters.register_loader(16,BoolLoader);cursor.adapters.register_loader(17,ByteaLoader)
    for kind,dumper in ((str,StrBinaryDumper),(str,StrDumperUnknown),(bytes,BytesDumper),
                        (bytes,BytesBinaryDumper),(int,IntBinaryDumper),(int,IntDumper)):
        cursor.adapters.register_dumper(kind,dumper)


def _release():
    root=files('truss').joinpath('_catalog_runtime')
    original=root.joinpath('manifest.json').read_bytes()
    manifest=json.loads(original)
    sources=[]
    for name in ('layout.sql','lineage.sql','plan.sql','runtime.sql','migrations.sql','barrier.sql','view.sql','scalars.sql','containers.sql','read.sql','key-derivation.sql','keys.sql','groups.sql','reader.sql','key-read.sql','pages.sql','evolution.sql','operations.sql','ownership.sql','catalog-rebind-storage.sql','catalog-rebind.sql','catalog-key-backfill-storage.sql','catalog-key-backfill.sql','preconditions.sql','imports.sql','feed.sql','history.sql','query.sql','entity-query.sql','entity-times.sql','entity-load.sql','feed-receipts.sql','traversal.sql'):
        raw=root.joinpath(name).read_bytes()
        if sha256(raw).hexdigest()!=manifest['files'][name]:raise ValueError('Catalog release source changed')
        source=raw.decode('utf-8')
        if name in ('catalog-rebind.sql','catalog-key-backfill.sql'):source='-- Planned basis'+source.split('-- Planned basis',1)[1]
        sources.append(source)
    profiles=root.joinpath('group-profiles.json').read_bytes()
    if sha256(profiles).hexdigest()!=manifest['files']['group-profiles.json']:raise ValueError('Selected group profiles required')
    for entry in json.loads(profiles)['profiles']+json.loads(profiles).get('retainedProfiles',[]):
        if sha256(entry['definition'].encode('utf8')).hexdigest()!=entry['pin']['sha256']:raise ValueError('Original profile definition required')
    public_profiles=root.joinpath('capability-profiles.json').read_bytes()
    if sha256(public_profiles).hexdigest()!=manifest['files']['capability-profiles.json']:raise ValueError('Selected public capability profiles required')
    for entry in json.loads(public_profiles)['profiles']+json.loads(public_profiles).get('retainedProfiles',[]):
        if sha256(entry['definition'].encode('utf8')).hexdigest()!=entry['pin']['sha256']:raise ValueError('Original public capability definition required')
        if 'policyPin' in entry and sha256(entry['policyDefinition'].encode('utf8')).hexdigest()!=entry['policyPin']['sha256']:raise ValueError('Original public capability policy required')
    for name in ('preparation-baseline.json','upgrade-source-023.json','upgrade-source-024.json','upgrade-source-025.json','upgrade-source-026.json','upgrade-source-027.json','upgrade-source-028.json','upgrade-source-029.json','upgrade-source-030.json','upgrade-source-031.json','upgrade-source-032.json','upgrade-source-033.json','upgrade-source-034.json','upgrade-source-035.json','upgrade-source-036.json','upgrade-source-037.json','upgrade-source-038.json','upgrade-source-039.json','upgrade-source-040.json','upgrade-source-041.json','upgrade-source-042.json','upgrade-source-043.json','upgrade-source-044.json','upgrade-source-045.json','upgrade-source-046.json','upgrade-source-047.json','upgrade-source-048.json','upgrade-source-049.json','upgrade-source-050.json','upgrade-source-051.json','upgrade-source-052.json','upgrade-source-053.json','upgrade-source-054.json','upgrade-source-055.json','upgrade-source-056.json','upgrade-source-057.json','upgrade-source-058.json','upgrade-source-059.json','upgrade-source-060.json','upgrade-source-061.json','upgrade-source-062.json','upgrade-source-063.json','upgrade-source-064.json','upgrade-source-065.json','upgrade-source-066.json','owned-transition-upgrade.sql'):
        if sha256(root.joinpath(name).read_bytes()).hexdigest()!=manifest['files'][name]:raise ValueError('Original migration/preparation baseline required')
    return manifest,sha256(original).hexdigest(),tuple(sources)


def _configuration(source_version="0.7.0"):
    manifest,_,_=_release()
    from .catalog_preparation import _configuration as preparation_configuration
    return preparation_configuration(source_version,manifest)


def _active_operation(method):
    @wraps(method)
    def guarded(self,*args,**kwargs):
        with self._lock:
            if self._disposed:
                return Error(ExecutionFailure('execution_obligation','Assembly disposed'))
            return method(self,*args,**kwargs)
    return guarded


def _object_result(raw,manifest,digest):
    basis=json.loads(bytes(raw))
    if basis.get('profile')!='truss-python-scalar-object/0.4':
        raise ValueError('Exact selected object read profile required')
    if basis['releaseId']!=manifest['releaseId'] or basis['releaseSha256']!=digest:
        raise ValueError('Exact selected installed runtime required')
    def logical(value):
        if type(value) is dict:
            from .contracts import TextValue,NullValue,BooleanValue,SequenceValue,MapValue,MapEntry
            def exact(cell):
                if cell['kind']=='null':return NullValue()
                if cell['kind']=='boolean':return BooleanValue(value=cell['value'])
                if cell['kind']=='sequence':return SequenceValue(items=tuple(exact(child) for child in cell['items']))
                if cell['kind']=='map':return MapValue(entries=tuple(MapEntry(key=entry['key'],value=exact(entry['value'])) for entry in cell['entries']))
                return TextValue(kind=cell['kind'],text=cell['text'])
            if value['kind']=='sequence':return SequenceValue(items=tuple(exact(cell) for cell in value['items']))
            if value['kind']=='map':return MapValue(entries=tuple(MapEntry(key=entry['key'],value=exact(entry['value'])) for entry in value['entries']))
            return TextValue(kind=value['kind'],text=value['text'])
        return value
    return ObjectFound(object=ScalarObject(document_id=basis['documentId'],module_id=basis['moduleId'],
        record_id=basis['recordId'],id=int(basis['id']),type_id=int(basis['typeId']),definition_pin=basis['definitionPin'],version=int(basis['version']),
        catalog_revision=int(basis['catalogRevision']),record_revision=int(basis['recordRevision']),
        created_at=basis['createdAt'],updated_at=basis['updatedAt'],
        values=tuple((v[0],logical(v[1])) for v in basis['values']),retained=tuple((v[0],logical(v[1])) for v in basis['retained'])))


def _edge_result(value):
    from ._group_runtime import _identity
    from .contracts import TextValue
    def logical(cell):
        if cell['kind']=='null':return None
        if cell['kind']=='boolean':return cell['value']
        if cell['kind']=='string':return cell['text']
        return TextValue(kind=cell['kind'],text=cell['text'])
    return ScalarEdge(identity=_identity(value['identity']),source=_identity(value['source']),target=_identity(value['target']),
        version=int(value['recordVersion']),catalog_revision=int(value['executedCatalogRevision']),record_revision=int(value['catalogRevision']),created_at=value['createdAt'],updated_at=value['updatedAt'],
        order_key=value['orderKey'].get('text'),retained=tuple((v['name'],logical(v['value'])) for v in value['retained']))


def _catalog_failure(result, local_code=None):
    # Annotate contained catalog failures only; transaction authority and retry
    # outcomes remain unchanged. Codes never depend on diagnostic prose.
    if not isinstance(result,Error):return result
    failure=result.error
    code=None
    if failure.code=='execution_obligation':
        code={'42501':'unauthorized','22023':'invalid_input','P1001':'request_conflict',
              '0A000':'unsupported_profile','25006':'unsupported_profile','54000':'resource',
              '55P03':'observation','42P01':'installation','42883':'installation','3F000':'installation'}.get(failure.sql_state)
    if local_code is not None and failure.code=='invalid_transaction' and failure.sql_state is None:
        code=local_code
    return result if code is None else Error(replace(failure,catalog_code=code))


_SelectedFamily=TypeVar('_SelectedFamily',Literal['catalog'],Literal['direct_read'],Literal['import'],Literal['feed'],Literal['history'],Literal['weft_execution'])


class CatalogReferenceAssembly:
    """Actual installation/catalog provider. Settlement stays with the caller."""
    def __init__(self,configuration: CatalogRuntimeConfiguration,host: PsycopgHost) -> None:
        if type(configuration) is not CatalogRuntimeConfiguration or type(host) is not PsycopgHost:
            raise ValueError('Catalog configuration and adopted psycopg host required')
        if configuration.schema!='truss' or type(configuration.assembly_id) is not str or not 1<=len(configuration.assembly_id)<=256:
            raise ValueError('Supported catalog configuration required')
        self.configuration=configuration;self._host=host;self._disposed=False;self._lock=RLock();self._group_documents=()
    @overload
    def catalog(self) -> CatalogReferenceAssembly: ...
    @overload
    def catalog(self,selection: CapabilitySelection[Literal['catalog']]) -> CapabilityAvailable[NativeCatalogCapability] | CapabilityUnavailable: ...
    def catalog(self,selection: CapabilitySelection[Literal['catalog']] | None=None) -> CatalogReferenceAssembly | CapabilityAvailable[NativeCatalogCapability] | CapabilityUnavailable:
        if selection is None:return self
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.catalog_selection:return CapabilityUnavailable(reason='selection')
            return CapabilityAvailable(capability=NativeCatalogCapability(selection=self.catalog_selection,_assembly=self))

    def _native_selection(self,family: _SelectedFamily) -> CapabilitySelection[_SelectedFamily]:
        """Inert exact packaged selection; per-call native admission is separate."""
        from .contracts import ProfilePin
        group=self.group_selection
        entries=json.loads(files('truss').joinpath('_catalog_runtime','capability-profiles.json').read_bytes())['profiles']
        entry=next(item for item in entries if item['name']==family)
        return CapabilitySelection(family=family,capability_profile=ProfilePin(**entry['pin']),
            layout_profile=group.layout_profile,adapter_profile=group.adapter_profile,
            value_profile=group.value_profile,policy_profile=ProfilePin(**entry['policyPin']) if 'policyPin' in entry else group.policy_profile)

    @property
    def catalog_selection(self) -> CapabilitySelection[Literal['catalog']]:
        return self._native_selection('catalog')

    @property
    def direct_read_selection(self) -> CapabilitySelection[Literal['direct_read']]:
        return self._native_selection('direct_read')

    @property
    def import_selection(self) -> CapabilitySelection[Literal['import']]:
        return self._native_selection('import')

    @property
    def feed_selection(self) -> CapabilitySelection[Literal['feed']]:
        return self._native_selection('feed')

    def direct_reads(self,selection: CapabilitySelection[Literal['direct_read']]) -> CapabilityAvailable[NativeDirectReadCapability] | CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.direct_read_selection:return CapabilityUnavailable(reason='selection')
            return CapabilityAvailable(capability=NativeDirectReadCapability(selection=self.direct_read_selection,_assembly=self))

    def imports(self,selection: CapabilitySelection[Literal['import']],*,documents: tuple[CatalogDocument,...],bun_executable: str='bun') -> CapabilityAvailable[NativeImportCapability] | CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.import_selection:return CapabilityUnavailable(reason='selection')
            try:
                valid=type(documents) is tuple and 1<=len(documents)<=512 and all(type(d) is CatalogDocument and type(d.content) is bytes and 1<=len(d.content)<=4194304
                    and type(d.document_id) is str and type(d.document_revision) is str and all(1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (d.document_id,d.document_revision))
                    and (d.artifact_identity is None or type(d.artifact_identity) is str and 1<=len(d.artifact_identity.encode('utf8'))<=4096 and '\0' not in d.artifact_identity) for d in documents)
                valid=valid and len({d.document_id for d in documents})==len(documents) and sum(len(d.content) for d in documents)<=4194304
                valid=valid and type(bun_executable) is str and 1<=len(bun_executable.encode('utf8'))<=4096 and '\0' not in bun_executable
            except (UnicodeError,TypeError):valid=False
            if not valid:return CapabilityUnavailable(reason='selection')
            return CapabilityAvailable(capability=NativeImportCapability(selection=self.import_selection,_assembly=self,_documents=documents,_bun_executable=bun_executable))

    def feed(self,selection: CapabilitySelection[Literal['feed']]) -> CapabilityAvailable[NativeFeedCapability] | CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.feed_selection:return CapabilityUnavailable(reason='selection')
            return CapabilityAvailable(capability=NativeFeedCapability(selection=self.feed_selection,_assembly=self))

    @property
    def history_selection(self) -> CapabilitySelection[Literal['history']]:
        return self._native_selection('history')

    def history(self,selection: CapabilitySelection[Literal['history']]) -> CapabilityAvailable[NativeHistoryCapability] | CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.history_selection:return CapabilityUnavailable(reason='selection')
            return CapabilityAvailable(capability=NativeHistoryCapability(selection=self.history_selection,_assembly=self))

    @property
    def compiled_selection(self) -> CapabilitySelection[Literal['weft_execution']]:
        return self._native_selection('weft_execution')

    def compiled_execution(self,selection: CapabilitySelection[Literal['weft_execution']]) -> CapabilityAvailable[NativeCompiledExecutionCapability] | CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.compiled_selection:return CapabilityUnavailable(reason='selection')
            from ._query_runtime import compiler
            if compiler() is None:return CapabilityUnavailable(reason='profile')
            return CapabilityAvailable(capability=NativeCompiledExecutionCapability(selection=self.compiled_selection,_assembly=self))

    @_active_operation
    def query_in_transaction(self,transaction: TransactionHandle,*,sql: str,document_ids: tuple[str,...],parameters: Mapping[str,str|int|bool|Decimal|TextValue] | None=None,
                             maximum_rows: int=1000,maximum_scan_rows: int=10000,maximum_bytes: int=1048576,
                             read_profile: Literal['entity-page','related-entity-page','count-summary','complete-entity'] | None=None) -> Outcome[QueryRows | QueryRefused | QueryUnavailable]:
        from ._query_runtime import run_query
        manifest,digest,_=_release()
        return run_query(self._host,transaction,sql=sql,document_ids=document_ids,parameters={} if parameters is None else parameters,
            maximum_rows=maximum_rows,maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes,manifest=manifest,digest=digest,pin_cursor=_pin_cursor,read_profile=read_profile)

    @_active_operation
    def query_page_in_transaction(self,transaction: TransactionHandle,*,sql: str,document_ids: tuple[str,...],parameters: Mapping[str,str|int|bool|Decimal|TextValue] | None=None,
                                  limit: int=100,cursor: QueryPageCursor | None=None,maximum_scan_rows: int=10000,maximum_bytes: int=1048576) -> Outcome[QueryPage | QueryRefused | QueryUnavailable]:
        from ._query_runtime import run_query
        manifest,digest,_=_release()
        return run_query(self._host,transaction,sql=sql,document_ids=document_ids,parameters={} if parameters is None else parameters,
            maximum_rows=limit+1 if type(limit) is int else 0,maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes,
            manifest=manifest,digest=digest,pin_cursor=_pin_cursor,read_profile=None,page_size=limit,page_cursor=cursor)

    def mutations(self,selection: CapabilitySelection[Literal['mutation']]) -> CapabilityUnavailable:
        with self._lock:return CapabilityUnavailable(reason='disposed' if self._disposed else 'selection')
    def dispose(self) -> AssemblyDisposed:
        with self._lock:
            self._disposed=True
            return AssemblyDisposed()
    def _available(self):
        if self._disposed:raise ValueError('Assembly disposed')
    def prepare_catalog(self,documents: tuple[CatalogDocument,...],*,bun_executable: str='bun',source_version:str='0.7.0') -> PreparedAcceptance:
        with self._lock:
            self._available()
            from .catalog_preparation import prepare_catalog
            return prepare_catalog(documents,source_version=source_version,bun_executable=bun_executable)
    @_active_operation
    def install_in_transaction(self,transaction: TransactionHandle,*,owner_role: str | None=None,registrar_role: str | None=None) -> Outcome[PendingCatalogInstallation]:
        self._available()
        from psycopg import sql
        from ._installation_privileges import InstallationRoles, _name, protect_installation_with_cursor
        manifest,digest,sources=_release()
        suffix=uuid4().hex[:16]
        roles=InstallationRoles(owner_role or 'truss_owner_'+suffix,registrar_role or 'truss_registrar_'+suffix)
        if not _name(roles.owner) or not _name(roles.client) or roles.owner==roles.client:
            return Error(ExecutionFailure('execution_obligation','Distinct valid installation roles required'))
        def install(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
            original_path=cursor.fetchone()[0]
            cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
            cursor.execute("SELECT pg_catalog.current_setting('server_version_num')",prepare=False)
            if cursor.fetchone()[0]!=manifest['postgresVersion']:raise ValueError('Supported PostgreSQL release required')
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')",prepare=False)
            if cursor.fetchone()[0]:raise ValueError('Existing namespace requires a supported migration')
            for source in sources:cursor.execute(source,prepare=False)
            privileges=protect_installation_with_cursor(cursor,roles)
            cursor.execute('''INSERT INTO truss.catalog_runtime_installation(singleton,installation_id,release_id,release_sha256,layout_profile,preparation_configuration,owner_oid,registrar_oid,genesis_at)
                SELECT true,pg_catalog.gen_random_uuid(),%s,%s,%s::pg_catalog.jsonb,%s::pg_catalog.jsonb,%s,%s,accepted_at
                FROM truss.schema_rev WHERE rev=0 RETURNING installation_id::pg_catalog.text''',
                (manifest['releaseId'],digest,json.dumps(manifest['layoutProfile']),json.dumps(_configuration()),privileges.owner_oid,privileges.client_oid),prepare=False)
            identity=cursor.fetchone()[0]
            for signature in ('catalog_accept(bytea,bytea,bytea,bytea,bytea,text)','catalog_accept_preview(bytea,bytea,bytea,bytea,bytea,text)','catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean)','catalog_report(int)','catalog_status()','catalog_view_basis(int,int,int)'):
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(roles.client)),prepare=False)
            cursor.execute("COMMENT ON SCHEMA truss IS 'Truss runtime 0.56 candidate: catalog, scalar graph, provenance, history, feed and additive upgrades'",prepare=False)
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
            return PendingCatalogInstallation(identity,roles.owner,roles.client,manifest['releaseId'])
        return self._host._run_operation(transaction,install)
    @_active_operation
    def upgrade_in_transaction(self,transaction: TransactionHandle) -> Outcome[PendingRuntimeUpgrade]:
        """Upgrade retained .23 through .52 to .53/layout1.0; caller settles it.

        Requires a direct trusted installation administrator and quiescence.
        Native NOWAIT fencing refuses active consumers without internal retries.
        Genesis, accepted identities, data, receipts and checkpoints are retained.
        """
        from psycopg import sql
        manifest,digest,sources=_release()
        bundled=files('truss').joinpath('_catalog_runtime')
        previous_raw=bundled.joinpath('upgrade-source-023.json').read_bytes()
        previous=json.loads(previous_raw);previous_digest=sha256(previous_raw).hexdigest()
        previous_024_raw=bundled.joinpath('upgrade-source-024.json').read_bytes()
        previous_024=json.loads(previous_024_raw)
        previous_025_raw=bundled.joinpath('upgrade-source-025.json').read_bytes()
        previous_025=json.loads(previous_025_raw)
        previous_026_raw=bundled.joinpath('upgrade-source-026.json').read_bytes()
        previous_026=json.loads(previous_026_raw)
        previous_027_raw=bundled.joinpath('upgrade-source-027.json').read_bytes()
        previous_027=json.loads(previous_027_raw)
        previous_028_raw=bundled.joinpath('upgrade-source-028.json').read_bytes()
        previous_028=json.loads(previous_028_raw)
        previous_029_raw=bundled.joinpath('upgrade-source-029.json').read_bytes()
        previous_029=json.loads(previous_029_raw)
        previous_030_raw=bundled.joinpath('upgrade-source-030.json').read_bytes()
        previous_030=json.loads(previous_030_raw)
        supported={(previous['releaseId'],previous_digest),(previous_024['releaseId'],sha256(previous_024_raw).hexdigest()),(previous_025['releaseId'],sha256(previous_025_raw).hexdigest()),(previous_026['releaseId'],sha256(previous_026_raw).hexdigest()),(previous_027['releaseId'],sha256(previous_027_raw).hexdigest()),(previous_028['releaseId'],sha256(previous_028_raw).hexdigest()),(previous_029['releaseId'],sha256(previous_029_raw).hexdigest()),(previous_030['releaseId'],sha256(previous_030_raw).hexdigest())}
        previous_031_raw=bundled.joinpath('upgrade-source-031.json').read_bytes()
        previous_031=json.loads(previous_031_raw)
        supported.add((previous_031['releaseId'],sha256(previous_031_raw).hexdigest()))
        previous_032_raw=bundled.joinpath('upgrade-source-032.json').read_bytes()
        previous_032=json.loads(previous_032_raw)
        supported.add((previous_032['releaseId'],sha256(previous_032_raw).hexdigest()))
        previous_033_raw=bundled.joinpath('upgrade-source-033.json').read_bytes()
        previous_033=json.loads(previous_033_raw)
        previous_034_raw=bundled.joinpath('upgrade-source-034.json').read_bytes()
        previous_034=json.loads(previous_034_raw)
        supported.add((previous_033['releaseId'],sha256(previous_033_raw).hexdigest()))
        supported.add((previous_034['releaseId'],sha256(previous_034_raw).hexdigest()))
        previous_035_raw=bundled.joinpath('upgrade-source-035.json').read_bytes()
        previous_035=json.loads(previous_035_raw)
        supported.add((previous_035['releaseId'],sha256(previous_035_raw).hexdigest()))
        previous_036_raw=bundled.joinpath('upgrade-source-036.json').read_bytes()
        previous_036=json.loads(previous_036_raw)
        supported.add((previous_036['releaseId'],sha256(previous_036_raw).hexdigest()))
        previous_037_raw=bundled.joinpath('upgrade-source-037.json').read_bytes()
        previous_037=json.loads(previous_037_raw)
        supported.add((previous_037['releaseId'],sha256(previous_037_raw).hexdigest()))
        previous_038_raw=bundled.joinpath('upgrade-source-038.json').read_bytes()
        previous_038=json.loads(previous_038_raw)
        supported.add((previous_038['releaseId'],sha256(previous_038_raw).hexdigest()))
        previous_039_raw=bundled.joinpath('upgrade-source-039.json').read_bytes()
        previous_039=json.loads(previous_039_raw)
        supported.add((previous_039['releaseId'],sha256(previous_039_raw).hexdigest()))
        previous_040_raw=bundled.joinpath('upgrade-source-040.json').read_bytes()
        previous_040=json.loads(previous_040_raw)
        supported.add((previous_040['releaseId'],sha256(previous_040_raw).hexdigest()))
        previous_041_raw=bundled.joinpath('upgrade-source-041.json').read_bytes()
        previous_041=json.loads(previous_041_raw)
        supported.add((previous_041['releaseId'],sha256(previous_041_raw).hexdigest()))
        previous_042_raw=bundled.joinpath('upgrade-source-042.json').read_bytes()
        previous_042=json.loads(previous_042_raw)
        supported.add((previous_042['releaseId'],sha256(previous_042_raw).hexdigest()))
        previous_043_raw=bundled.joinpath('upgrade-source-043.json').read_bytes()
        previous_043=json.loads(previous_043_raw)
        supported.add((previous_043['releaseId'],sha256(previous_043_raw).hexdigest()))
        previous_044_raw=bundled.joinpath('upgrade-source-044.json').read_bytes()
        previous_044=json.loads(previous_044_raw)
        supported.add((previous_044['releaseId'],sha256(previous_044_raw).hexdigest()))
        previous_045_raw=bundled.joinpath('upgrade-source-045.json').read_bytes()
        previous_045=json.loads(previous_045_raw)
        supported.add((previous_045['releaseId'],sha256(previous_045_raw).hexdigest()))
        previous_046_raw=bundled.joinpath('upgrade-source-046.json').read_bytes()
        previous_046=json.loads(previous_046_raw)
        supported.add((previous_046['releaseId'],sha256(previous_046_raw).hexdigest()))
        previous_047_raw=bundled.joinpath('upgrade-source-047.json').read_bytes()
        previous_047=json.loads(previous_047_raw)
        supported.add((previous_047['releaseId'],sha256(previous_047_raw).hexdigest()))
        previous_048_raw=bundled.joinpath('upgrade-source-048.json').read_bytes()
        previous_048=json.loads(previous_048_raw)
        supported.add((previous_048['releaseId'],sha256(previous_048_raw).hexdigest()))
        previous_049_raw=bundled.joinpath('upgrade-source-049.json').read_bytes()
        previous_049=json.loads(previous_049_raw)
        supported.add((previous_049['releaseId'],sha256(previous_049_raw).hexdigest()))
        previous_050_raw=bundled.joinpath('upgrade-source-050.json').read_bytes()
        previous_050=json.loads(previous_050_raw)
        supported.add((previous_050['releaseId'],sha256(previous_050_raw).hexdigest()))
        previous_051_raw=bundled.joinpath('upgrade-source-051.json').read_bytes()
        previous_051=json.loads(previous_051_raw)
        supported.add((previous_051['releaseId'],sha256(previous_051_raw).hexdigest()))
        previous_052_raw=bundled.joinpath('upgrade-source-052.json').read_bytes()
        previous_052=json.loads(previous_052_raw)
        supported.add((previous_052['releaseId'],sha256(previous_052_raw).hexdigest()))
        previous_053_raw=bundled.joinpath('upgrade-source-053.json').read_bytes()
        previous_053=json.loads(previous_053_raw)
        supported.add((previous_053['releaseId'],sha256(previous_053_raw).hexdigest()))
        previous_054_raw=bundled.joinpath('upgrade-source-054.json').read_bytes()
        previous_054=json.loads(previous_054_raw)
        supported.add((previous_054['releaseId'],sha256(previous_054_raw).hexdigest()))
        previous_055_raw=bundled.joinpath('upgrade-source-055.json').read_bytes()
        previous_055=json.loads(previous_055_raw)
        supported.add((previous_055['releaseId'],sha256(previous_055_raw).hexdigest()))
        previous_056_raw=bundled.joinpath('upgrade-source-056.json').read_bytes()
        previous_056=json.loads(previous_056_raw)
        supported.add((previous_056['releaseId'],sha256(previous_056_raw).hexdigest()))
        previous_057_raw=bundled.joinpath('upgrade-source-057.json').read_bytes()
        previous_057=json.loads(previous_057_raw)
        supported.add((previous_057['releaseId'],sha256(previous_057_raw).hexdigest()))
        previous_058_raw=bundled.joinpath('upgrade-source-058.json').read_bytes()
        previous_058=json.loads(previous_058_raw)
        supported.add((previous_058['releaseId'],sha256(previous_058_raw).hexdigest()))
        previous_059_raw=bundled.joinpath('upgrade-source-059.json').read_bytes()
        previous_059=json.loads(previous_059_raw)
        supported.add((previous_059['releaseId'],sha256(previous_059_raw).hexdigest()))
        previous_060_raw=bundled.joinpath('upgrade-source-060.json').read_bytes()
        previous_060=json.loads(previous_060_raw)
        supported.add((previous_060['releaseId'],sha256(previous_060_raw).hexdigest()))
        previous_061_raw=bundled.joinpath('upgrade-source-061.json').read_bytes()
        previous_061=json.loads(previous_061_raw)
        supported.add((previous_061['releaseId'],sha256(previous_061_raw).hexdigest()))
        previous_062_raw=bundled.joinpath('upgrade-source-062.json').read_bytes()
        previous_062=json.loads(previous_062_raw)
        supported.add((previous_062['releaseId'],sha256(previous_062_raw).hexdigest()))
        previous_063_raw=bundled.joinpath('upgrade-source-063.json').read_bytes()
        previous_063=json.loads(previous_063_raw)
        supported.add((previous_063['releaseId'],sha256(previous_063_raw).hexdigest()))
        previous_064_raw=bundled.joinpath('upgrade-source-064.json').read_bytes()
        previous_064=json.loads(previous_064_raw)
        supported.add((previous_064['releaseId'],sha256(previous_064_raw).hexdigest()))
        previous_065_raw=bundled.joinpath('upgrade-source-065.json').read_bytes()
        previous_065=json.loads(previous_065_raw)
        supported.add((previous_065['releaseId'],sha256(previous_065_raw).hexdigest()))
        previous_066_raw=bundled.joinpath('upgrade-source-066.json').read_bytes()
        previous_066=json.loads(previous_066_raw)
        supported.add((previous_066['releaseId'],sha256(previous_066_raw).hexdigest()))
        replacements=[]
        for source in sources:
            replacements.extend(re.findall(r"CREATE FUNCTION\s+truss\.\w+[\s\S]*?\bAS\s+(?:\$\$[\s\S]*?\$\$|'(?:[^']|'')*')\s*;",source))
        if len(replacements)!=163:raise ValueError('Exact additive runtime routine inventory required')
        signatures=[]
        for statement in replacements:
            header=re.match(r'CREATE FUNCTION\s+(truss\.\w+)\(([\s\S]*?)\)\s+RETURNS\b',statement)
            if header is None:raise ValueError('Original routine header required')
            name,arguments=header.groups();types=[]
            arguments=re.sub(r"DEFAULT convert_to\('[^']*','[^']*'\)",'DEFAULT NULL',arguments)
            for argument in arguments.split(',') if arguments.strip() else ():
                parameter=re.fullmatch(r'\s*\w+\s+([\w.]+(?:\[\])?)(?:\s+DEFAULT\s+[^,]+)?\s*',argument)
                if parameter is None:raise ValueError('Owned additive routine argument profile required')
                types.append(parameter.group(1))
            signature=name+'('+','.join(types)+')'
            if name not in ('truss.umf_key_uleb128','truss.umf_key_coefficient','truss.encode_umf_scalar_key_tuple','truss.umf_key_field_values_valid','truss.derive_catalog_key_tuple','truss.runtime_endpoint_ownership','truss.catalog_scalar_violations_with_sources','truss.catalog_item_meaning','truss.valid_item_chain','truss.runtime_item_chain_readable','truss.catalog_accept_with_keys','truss.catalog_accept_preview','truss.catalog_key_backfill_candidates','truss.catalog_key_backfill_verify','truss.catalog_key_backfill_violations','truss.catalog_key_backfill_apply','truss.catalog_key_backfill_transition_reader','truss.catalog_key_backfill_report_reader','truss.catalog_rebind_profile','truss.catalog_rebind_transition_reader','truss.catalog_rebind_definition','truss.catalog_rebind_history','truss.catalog_rebind_objects','truss.catalog_rebind_violations','truss.catalog_rebind_report_reader','truss.catalog_rebind_history_group','truss.runtime_capture_feed_configuration','truss.catalog_check_source_correspondence','truss.runtime_object_values_readable','truss.valid_property_definition','truss.valid_flat_cell','truss.canonical_flat_cell','truss.valid_property_value','truss.logical_flat_cell','truss.catalog_item_definition','truss.render_scalar_object','truss.traverse_objects','truss.umf_key_values','truss.verify_umf_scalar_key_tuple','truss.valid_scalar_property','truss.runtime_current_installation','truss.query_binding','truss.query_scope','truss.query_objects','truss.query_numeric_value','truss.query_timestamp_instant_key','truss.query_edges','truss.query_page_objects','truss.feed_reached','truss.query_object_attribution','truss.query_complete_related_keys','truss.query_object_times','truss.query_object_load_id','truss.feed_ack_receipt_binding','truss.acknowledge_feed_with_receipt','truss.reconcile_feed_ack'):signatures.append(signature)
        def upgrade(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False);original_path=cursor.fetchone()[0]
            cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
            from ._installation_privileges import installation_administrator_with_cursor
            installation_administrator_with_cursor(cursor)
            cursor.execute("SELECT current_setting('server_version_num')",prepare=False)
            if cursor.fetchone()[0]!=manifest['postgresVersion']:raise ValueError('Exact supported PostgreSQL version required')
            cursor.execute('LOCK TABLE truss.catalog_runtime_installation IN ACCESS EXCLUSIVE MODE NOWAIT',prepare=False)
            cursor.execute('SELECT i.*,r.rolname FROM truss.catalog_runtime_installation i JOIN pg_roles r ON r.oid=i.owner_oid',prepare=False)
            row=cursor.fetchone()
            if row is None:raise ValueError('Original installation required')
            # Explicit named projection keeps the immutable composite shape independent.
            cursor.execute('SELECT installation_id::text,release_id,release_sha256,layout_profile,preparation_configuration,owner_oid,registrar_oid FROM truss.catalog_runtime_installation',prepare=False)
            identity,genesis_release,genesis_digest,layout,configuration,owner_oid,registrar_oid=cursor.fetchone()
            owner_role=row[-1]
            installation_administrator_with_cursor(cursor,owner_oid)
            cursor.execute("SELECT nspowner FROM pg_namespace WHERE nspname='truss'",prepare=False)
            if cursor.fetchone()!=(owner_oid,):raise ValueError('Original namespace owner required')
            for role_oid in (owner_oid,registrar_oid):
                cursor.execute("SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit FROM pg_roles WHERE oid=%s",(role_oid,),prepare=False)
                if cursor.fetchone()!=(False,False,False,False,False,False,False):raise ValueError('Original protected role attributes required')
            cursor.execute("SELECT to_regclass('truss.runtime_release') IS NOT NULL",prepare=False)
            has_ledger=cursor.fetchone()[0]
            active_release,active_digest=genesis_release,genesis_digest
            if has_ledger:
                cursor.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()',prepare=False)
                active_release,active_digest=cursor.fetchone()
            if (active_release,active_digest)==(manifest['releaseId'],digest):
                cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
                if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
                return PendingRuntimeUpgrade(identity,active_release,manifest['releaseId'],'unchanged')
            source_configurations=[_configuration(),_configuration('0.8.0'),{**_configuration(),'supportProfile':dict(DECIMAL207_PROFILE)},{**_configuration(),'supportProfile':dict(REFERENCE08_PROFILE)},{**_configuration(),'supportProfile':dict(RECURSIVE08_PROFILE)},{**_configuration(),'supportProfile':dict(DECIMAL208_PROFILE)},{**_configuration(),'supportProfile':dict(CONTAINER07_PROFILE)},{**_configuration(),'supportProfile':dict(CONTAINER08_PROFILE)},{**_configuration(),'supportProfile':dict(FACET07_PROFILE)},{**_configuration(),'supportProfile':dict(FACET08_PROFILE)},{**_configuration(),'supportProfile':dict(RETAINED_METADATA_PROFILE)},{**_configuration(),'supportProfile':dict(NAMED_RELATIONSHIP_PROFILE)},json.loads(bundled.joinpath('preparation-baseline.json').read_bytes())]
            if active_release in ('truss-catalog-runtime/0.26-candidate','truss-catalog-runtime/0.27-candidate'):
                previous_named=json.loads(bundled.joinpath('preparation-baseline.json').read_bytes())
                previous_named['supportProfile']=dict(NAMED_SCALAR_PROFILE)
                source_configurations.append(previous_named)
            source_configurations.extend({**entry,'layoutProfile':previous_051['layoutProfile']} for entry in tuple(source_configurations))
            if (active_release,active_digest) not in supported or layout not in (previous_051['layoutProfile'],manifest['layoutProfile']) or configuration not in source_configurations:
                raise ValueError('Exact supported .23/.24/.25/.26/.27/.28/.29/.30/.31/.32/.33/.34 installation and preparation required')
            # Exact populated layout0.16 ->1.0 conversion; transactional DDL rolls back with this upgrade.
            active_layout=layout
            if has_ledger:
                cursor.execute('SELECT layout_profile FROM truss.runtime_current_installation()',prepare=False)
                active_layout=cursor.fetchone()[0]
            if active_layout==previous_051['layoutProfile']:
                cursor.execute('LOCK TABLE truss.edge IN ACCESS EXCLUSIVE MODE NOWAIT',prepare=False)
                cursor.execute("SELECT pg_get_indexdef(i.indexrelid),c.relowner,i.indisvalid,i.indisready FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indexrelid='truss.edge_out'::regclass",prepare=False)
                expected_index='CREATE UNIQUE INDEX edge_out ON truss.edge USING btree (source_id, rel_type_id, target_id) INCLUDE (target_type)'
                if cursor.fetchone()!=(expected_index,owner_oid,True,True):raise ValueError('Exact original endpoint uniqueness index required')
                cursor.execute('DROP INDEX truss.edge_out',prepare=False)
                cursor.execute('CREATE INDEX edge_out ON truss.edge USING btree (source_id,rel_type_id,target_id) INCLUDE(target_type)',prepare=False)
                cursor.execute("SELECT pg_get_indexdef(i.indexrelid),c.relowner,i.indisvalid,i.indisready FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indexrelid='truss.edge_out'::regclass",prepare=False)
                if cursor.fetchone()!=(expected_index.replace('CREATE UNIQUE INDEX','CREATE INDEX'),owner_oid,True,True):raise ValueError('Exact parallel endpoint lookup index required')
            elif active_layout!=manifest['layoutProfile']:
                raise ValueError('Supported active layout required')
            if active_release in ('truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.umf_key_values(jsonb)','truss.verify_umf_scalar_key_tuple(bytea,jsonb,jsonb)'))
            if active_release in ('truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.render_scalar_object(truss.object,truss.type_def,truss.prop_def[],boolean,text,int,int,text,text)','truss.traverse_objects(jsonb,jsonb,int,int,int,text,text)'))
            if active_release in ('truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.runtime_object_values_readable(int)','truss.valid_property_definition(truss.prop_def)','truss.valid_flat_cell(jsonb)','truss.canonical_flat_cell(jsonb)','truss.valid_property_value(jsonb,truss.prop_def)','truss.logical_flat_cell(jsonb)','truss.catalog_item_definition(text,text,int,int,jsonb)'))
            if active_release in ('truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.query_timestamp_instant_key(text,text)')
            if active_release in ('truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.catalog_rebind_definition(text,int,int,jsonb)','truss.catalog_rebind_history(jsonb,jsonb,jsonb)','truss.catalog_rebind_objects(truss.catalog_registration_request,jsonb)','truss.catalog_rebind_violations(jsonb,int)','truss.catalog_rebind_transition_reader(truss.runtime_catalog_rebind_transition,jsonb)','truss.catalog_rebind_report_reader(uuid,jsonb)','truss.catalog_rebind_history_group(jsonb,xid8,bigint)'))
            if active_release in ('truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.catalog_rebind_profile(jsonb)')
            if active_release in ('truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.catalog_key_backfill_candidates(jsonb,int)','truss.catalog_key_backfill_verify(jsonb,int,bytea)','truss.catalog_key_backfill_violations(jsonb)','truss.catalog_key_backfill_apply(truss.catalog_registration_request,jsonb)','truss.catalog_key_backfill_transition_reader(truss.runtime_catalog_key_backfill,jsonb)','truss.catalog_key_backfill_report_reader(uuid,jsonb)','truss.catalog_accept_preview(bytea,bytea,bytea,bytea,bytea,text)','truss.catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean)'))
            if has_ledger:signatures.append('truss.runtime_current_installation()')
            if active_release in ('truss-catalog-runtime/0.26-candidate','truss-catalog-runtime/0.27-candidate','truss-catalog-runtime/0.28-candidate','truss-catalog-runtime/0.29-candidate','truss-catalog-runtime/0.30-candidate','truss-catalog-runtime/0.31-candidate','truss-catalog-runtime/0.32-candidate','truss-catalog-runtime/0.33-candidate','truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.query_binding(jsonb,int,int,int,text,text)','truss.query_scope(jsonb)','truss.query_objects(jsonb,int)'))
            if active_release in ('truss-catalog-runtime/0.27-candidate','truss-catalog-runtime/0.28-candidate','truss-catalog-runtime/0.29-candidate','truss-catalog-runtime/0.30-candidate','truss-catalog-runtime/0.31-candidate','truss-catalog-runtime/0.32-candidate','truss-catalog-runtime/0.33-candidate','truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.query_numeric_value(text,text)')
            if active_release in ('truss-catalog-runtime/0.28-candidate','truss-catalog-runtime/0.29-candidate','truss-catalog-runtime/0.30-candidate','truss-catalog-runtime/0.31-candidate','truss-catalog-runtime/0.32-candidate','truss-catalog-runtime/0.33-candidate','truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.query_edges(jsonb,int)')
            if active_release in ('truss-catalog-runtime/0.29-candidate','truss-catalog-runtime/0.30-candidate','truss-catalog-runtime/0.31-candidate','truss-catalog-runtime/0.32-candidate','truss-catalog-runtime/0.33-candidate','truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.query_page_objects(jsonb,int,text)')
            if active_release in ('truss-catalog-runtime/0.30-candidate','truss-catalog-runtime/0.31-candidate','truss-catalog-runtime/0.32-candidate','truss-catalog-runtime/0.33-candidate','truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.feed_reached(text,bytea,int,text,text)')
            if active_release in ('truss-catalog-runtime/0.33-candidate','truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.query_object_attribution(jsonb,int,bigint)','truss.query_complete_related_keys(jsonb,int,int)'))
            if active_release in ('truss-catalog-runtime/0.34-candidate','truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.query_object_times(jsonb,int,bigint)')
            if active_release in ('truss-catalog-runtime/0.35-candidate','truss-catalog-runtime/0.36-candidate','truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.query_object_load_id(jsonb,int,bigint)')
            if active_release in ('truss-catalog-runtime/0.37-candidate','truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):signatures.append('truss.valid_scalar_property(jsonb,text,boolean,jsonb)')
            if active_release in ('truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.feed_ack_receipt_binding(text,bytea,bytea,text,text,text,text,bytea,text,text)','truss.acknowledge_feed_with_receipt(text,bytea,bytea,text,text,text,text,bytea,text,text)','truss.reconcile_feed_ack(text,bytea,bytea,text,text,text,text,bytea,text,text)'))
            if active_release in ('truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.runtime_capture_feed_configuration()','truss.catalog_check_source_correspondence(bytea,bytea,bytea)'))
            if active_release in ('truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.extend(('truss.catalog_scalar_violations_with_sources(bytea,bytea)','truss.catalog_item_meaning(jsonb)','truss.valid_item_chain(jsonb)','truss.runtime_item_chain_readable(jsonb)'))
            if active_release in ('truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                signatures.append('truss.runtime_endpoint_ownership(jsonb,int)')
            original_routines=[]
            for signature in signatures:
                cursor.execute('SELECT oid,proowner,proacl FROM pg_proc WHERE oid=to_regprocedure(%s)',(signature,),prepare=False)
                routine=cursor.fetchone()
                if routine is None or routine[1]!=owner_oid:raise ValueError('Exact original routine signature and owner required')
                original_routines.append(routine)
            if not has_ledger:cursor.execute(bundled.joinpath('migrations.sql').read_text(),prepare=False)
            # New query entry points are additive; old routine OIDs/ACLs stay fixed.
            # This exact owned release has dollar/quoted function bodies; replay no other
            # DDL, triggers or data statements from its fresh-install sources.
            if active_release not in ('truss-catalog-runtime/0.38-candidate','truss-catalog-runtime/0.39-candidate','truss-catalog-runtime/0.40-candidate','truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                cursor.execute(bundled.joinpath('feed-receipts.sql').read_text().split('CREATE FUNCTION',1)[0],prepare=False)

            feed_source=bundled.joinpath('feed.sql').read_text()
            capture_setup=feed_source.split('-- Parallel-layout transaction configuration capture; historical intervals are never backfilled.',1)[1].split('-- End parallel-layout transaction configuration capture.',1)[0]
            cursor.execute("SELECT to_regclass('truss.runtime_feed_transaction_configuration')",prepare=False)
            capture_exists=cursor.fetchone()[0] is not None
            if active_release in ('truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                if not capture_exists:raise ValueError('Retained feed configuration table required')
            else:
                if capture_exists:raise ValueError('Unexpected predecessor feed configuration table')
                cursor.execute(capture_setup,prepare=False)
            cursor.execute(sql.SQL('ALTER TABLE truss.runtime_feed_transaction_configuration OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON TABLE truss.runtime_feed_transaction_configuration FROM PUBLIC',prepare=False)
            cursor.execute('REVOKE ALL ON TYPE truss.runtime_feed_transaction_configuration FROM PUBLIC',prepare=False)
            cursor.execute("SELECT to_regclass('truss.runtime_catalog_rebind_transition')",prepare=False)
            existing_rebind=cursor.fetchone()[0]
            if active_release in ('truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                if existing_rebind is None:raise ValueError('Original registration transition storage required')
            else:
                if existing_rebind is not None:raise ValueError('New registration transition storage must be absent')
                cursor.execute(bundled.joinpath('catalog-rebind-storage.sql').read_text(),prepare=False)
            cursor.execute(sql.SQL('ALTER TABLE truss.runtime_catalog_rebind_transition OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON TABLE truss.runtime_catalog_rebind_transition FROM PUBLIC',prepare=False)
            cursor.execute('REVOKE ALL ON TYPE truss.runtime_catalog_rebind_transition FROM PUBLIC',prepare=False)
            cursor.execute("SELECT to_regclass('truss.runtime_catalog_key_backfill')",prepare=False)
            existing_key_backfill=cursor.fetchone()[0]
            if active_release in ('truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                if existing_key_backfill is None:raise ValueError('Original key backfill storage required')
            else:
                if existing_key_backfill is not None:raise ValueError('New key backfill storage must be absent')
                cursor.execute(bundled.joinpath('catalog-key-backfill-storage.sql').read_text(),prepare=False)
            cursor.execute(sql.SQL('ALTER TABLE truss.runtime_catalog_key_backfill OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON TABLE truss.runtime_catalog_key_backfill FROM PUBLIC',prepare=False)
            cursor.execute('REVOKE ALL ON TYPE truss.runtime_catalog_key_backfill FROM PUBLIC',prepare=False)
            from ._ownership_migration import upgrade_transition_storage,verify_transition_storage
            if active_release in ('truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                verify_transition_storage(cursor,owner_oid)
            else:
                upgrade_transition_storage(cursor,bundled.joinpath('owned-transition-upgrade.sql').read_text(),owner_oid)
            for statement in replacements:
                cursor.execute(statement.replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1),prepare=False)
            cursor.execute(sql.SQL('ALTER FUNCTION truss.runtime_endpoint_ownership(jsonb,int) OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON FUNCTION truss.runtime_endpoint_ownership(jsonb,int) FROM PUBLIC',prepare=False)
            for signature in ('catalog_key_backfill_candidates(jsonb,int)','catalog_key_backfill_verify(jsonb,int,bytea)','catalog_key_backfill_violations(jsonb)','catalog_key_backfill_apply(truss.catalog_registration_request,jsonb)','catalog_key_backfill_transition_reader(truss.runtime_catalog_key_backfill,jsonb)','catalog_key_backfill_report_reader(uuid,jsonb)','catalog_accept_preview(bytea,bytea,bytea,bytea,bytea,text)','catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean)'):
                cursor.execute(sql.SQL('ALTER FUNCTION truss.{} OWNER TO {}').format(sql.SQL(signature),sql.Identifier(owner_role)),prepare=False)
                cursor.execute(sql.SQL('REVOKE ALL ON FUNCTION truss.{} FROM PUBLIC').format(sql.SQL(signature)),prepare=False)
            cursor.execute('SELECT rolname FROM pg_roles WHERE oid=%s',(registrar_oid,),prepare=False)
            registrar_role=cursor.fetchone()[0]
            for signature in ('catalog_accept_preview(bytea,bytea,bytea,bytea,bytea,text)','catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean)'):
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(registrar_role)),prepare=False)
            cursor.execute("SELECT EXISTS(SELECT 1 FROM (SELECT relacl acl,relowner owner,'r'::\"char\" kind FROM pg_class WHERE oid='truss.runtime_catalog_key_backfill'::regclass UNION ALL SELECT typacl,typowner,'T'::\"char\" FROM pg_type WHERE oid='truss.runtime_catalog_key_backfill'::regtype) objects CROSS JOIN LATERAL aclexplode(coalesce(objects.acl,acldefault(objects.kind,objects.owner))) a WHERE objects.owner<>%s OR a.grantee<>objects.owner)",(owner_oid,),prepare=False)
            if cursor.fetchone()[0]:raise ValueError('Owner-only original key backfill storage required')
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE n.nspname='truss' AND (p.proname LIKE 'catalog_key_backfill_%%' OR p.proname IN ('catalog_accept_preview','catalog_accept_with_keys')) AND (p.proowner<>%s OR a.grantee<>p.proowner AND (p.proname NOT IN ('catalog_accept_preview','catalog_accept_with_keys') OR a.grantee<>%s OR a.privilege_type<>'EXECUTE' OR a.is_grantable)))",(owner_oid,registrar_oid),prepare=False)
            if cursor.fetchone()[0]:raise ValueError('Original key helper and registrar facade privileges required')
            for signature in ('catalog_rebind_profile(jsonb)','catalog_rebind_transition_reader(truss.runtime_catalog_rebind_transition,jsonb)','catalog_rebind_definition(text,int,int,jsonb)','catalog_rebind_history(jsonb,jsonb,jsonb)','catalog_rebind_objects(truss.catalog_registration_request,jsonb)','catalog_rebind_violations(jsonb,int)','catalog_rebind_report_reader(uuid,jsonb)','catalog_rebind_history_group(jsonb,xid8,bigint)'):
                cursor.execute(sql.SQL('ALTER FUNCTION truss.{} OWNER TO {}').format(sql.SQL(signature),sql.Identifier(owner_role)),prepare=False)
                cursor.execute(sql.SQL('REVOKE ALL ON FUNCTION truss.{} FROM PUBLIC').format(sql.SQL(signature)),prepare=False)
            if active_release not in ('truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):
                cursor.execute('CREATE CONSTRAINT TRIGGER runtime_catalog_rebind_commit AFTER INSERT ON truss.runtime_catalog_rebind_transition DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check()',prepare=False)
            cursor.execute('ALTER TABLE truss.runtime_catalog_rebind_transition ENABLE ALWAYS TRIGGER runtime_catalog_rebind_commit',prepare=False)
            cursor.execute('ALTER TABLE truss.runtime_catalog_rebind_transition ENABLE ALWAYS TRIGGER runtime_catalog_rebind_immutable',prepare=False)

            for signature in ('catalog_scalar_violations_with_sources(bytea,bytea)','catalog_item_meaning(jsonb)','valid_item_chain(jsonb)','runtime_item_chain_readable(jsonb)','runtime_object_values_readable(int)','valid_property_definition(truss.prop_def)','valid_flat_cell(jsonb)','canonical_flat_cell(jsonb)','valid_property_value(jsonb,truss.prop_def)','logical_flat_cell(jsonb)','catalog_item_definition(text,text,int,int,jsonb)','render_scalar_object(truss.object,truss.type_def,truss.prop_def[],boolean,text,int,int,text,text)','traverse_objects(jsonb,jsonb,int,int,int,text,text)','umf_key_values(jsonb)','verify_umf_scalar_key_tuple(bytea,jsonb,jsonb)','umf_key_uleb128(bigint)','umf_key_coefficient(text,int,int)','encode_umf_scalar_key_tuple(jsonb,jsonb)','umf_key_field_values_valid(jsonb,jsonb,text)','derive_catalog_key_tuple(int,smallint,jsonb,jsonb)'):
                cursor.execute(sql.SQL('ALTER FUNCTION truss.{} OWNER TO {}').format(sql.SQL(signature),sql.Identifier(owner_role)),prepare=False)
                cursor.execute(sql.SQL('REVOKE ALL ON FUNCTION truss.{} FROM PUBLIC').format(sql.SQL(signature)),prepare=False)
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE p.oid='truss.traverse_objects(jsonb,jsonb,int,int,int,text,text)'::regprocedure AND a.grantee<>p.proowner)",prepare=False)
            if cursor.fetchone()[0] and active_release not in ('truss-catalog-runtime/0.41-candidate','truss-catalog-runtime/0.42-candidate','truss-catalog-runtime/0.43-candidate','truss-catalog-runtime/0.44-candidate','truss-catalog-runtime/0.45-candidate','truss-catalog-runtime/0.46-candidate','truss-catalog-runtime/0.47-candidate','truss-catalog-runtime/0.48-candidate','truss-catalog-runtime/0.49-candidate','truss-catalog-runtime/0.50-candidate','truss-catalog-runtime/0.51-candidate','truss-catalog-runtime/0.52-candidate','truss-catalog-runtime/0.53-candidate','truss-catalog-runtime/0.54-candidate','truss-catalog-runtime/0.55-candidate','truss-catalog-runtime/0.56-candidate','truss-catalog-runtime/0.57-candidate','truss-catalog-runtime/0.58-candidate','truss-catalog-runtime/0.59-candidate','truss-catalog-runtime/0.60-candidate','truss-catalog-runtime/0.61-candidate','truss-catalog-runtime/0.62-candidate','truss-catalog-runtime/0.63-candidate','truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate','truss-catalog-runtime/0.66-candidate'):raise ValueError('New traversal facade must begin owner-only')
            cursor.execute('SELECT DISTINCT reader_role FROM truss.module_access UNION SELECT writer_role FROM truss.module_access',prepare=False)
            for (role,) in cursor.fetchall():
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.traverse_objects(jsonb,jsonb,int,int,int,text,text) TO {}').format(sql.Identifier(role)),prepare=False)
            cursor.execute('SELECT oid,proowner,proacl FROM pg_proc WHERE oid=ANY(%s::oid[]) ORDER BY oid',([r[0] for r in original_routines],),prepare=False)
            if cursor.fetchall()!=sorted(original_routines,key=lambda r:r[0]):raise ValueError('Original routine identity, owner and ACL preservation required')
            for name in ('runtime_release','runtime_release_generation'):
                cursor.execute(sql.SQL('ALTER {} truss.{} OWNER TO {}').format(sql.SQL('TABLE' if name=='runtime_release' else 'SEQUENCE'),sql.Identifier(name),sql.Identifier(owner_role)),prepare=False)
                cursor.execute(sql.SQL('REVOKE ALL ON {} truss.{} FROM PUBLIC').format(sql.SQL('TABLE' if name=='runtime_release' else 'SEQUENCE'),sql.Identifier(name)),prepare=False)
            cursor.execute(sql.SQL('ALTER TABLE truss.runtime_feed_ack_receipt OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON TABLE truss.runtime_feed_ack_receipt FROM PUBLIC',prepare=False)
            cursor.execute('REVOKE ALL ON TYPE truss.runtime_feed_ack_receipt FROM PUBLIC',prepare=False)
            for routine in ('feed_ack_receipt_binding','acknowledge_feed_with_receipt','reconcile_feed_ack'):
                signature=routine+'(text,bytea,bytea,text,text,text,text,bytea,text,text)'
                cursor.execute(sql.SQL('ALTER FUNCTION truss.{} OWNER TO {}').format(sql.SQL(signature),sql.Identifier(owner_role)),prepare=False)
                cursor.execute(sql.SQL('REVOKE ALL ON FUNCTION truss.{} FROM PUBLIC').format(sql.SQL(signature)),prepare=False)
                if routine!='feed_ack_receipt_binding':
                    cursor.execute('SELECT DISTINCT r.rolname FROM truss.runtime_feed_consumer c JOIN pg_roles r ON r.oid=c.reader_oid',prepare=False)
                    for feed_role, in cursor.fetchall():
                        cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(feed_role)),prepare=False)
            cursor.execute("""SELECT EXISTS(SELECT 1 FROM (
                SELECT relacl AS acl,relowner AS owner,'r'::"char" AS kind FROM pg_class WHERE oid='truss.runtime_feed_ack_receipt'::regclass
                UNION ALL SELECT typacl,typowner,'T'::"char" FROM pg_type WHERE oid='truss.runtime_feed_ack_receipt'::regtype
                UNION ALL SELECT proacl,proowner,'f'::"char" FROM pg_proc WHERE oid='truss.feed_ack_receipt_binding(text,bytea,bytea,text,text,text,text,bytea,text,text)'::regprocedure
                UNION ALL SELECT proacl,proowner,'f'::"char" FROM pg_proc WHERE oid IN ('truss.catalog_scalar_violations_with_sources(bytea,bytea)'::regprocedure,'truss.catalog_item_meaning(jsonb)'::regprocedure,'truss.valid_item_chain(jsonb)'::regprocedure,'truss.runtime_item_chain_readable(jsonb)'::regprocedure,'truss.runtime_object_values_readable(int)'::regprocedure,'truss.valid_property_definition(truss.prop_def)'::regprocedure,'truss.valid_flat_cell(jsonb)'::regprocedure,'truss.canonical_flat_cell(jsonb)'::regprocedure,'truss.valid_property_value(jsonb,truss.prop_def)'::regprocedure,'truss.logical_flat_cell(jsonb)'::regprocedure,'truss.catalog_item_definition(text,text,int,int,jsonb)'::regprocedure,'truss.render_scalar_object(truss.object,truss.type_def,truss.prop_def[],boolean,text,int,int,text,text)'::regprocedure,'truss.umf_key_values(jsonb)'::regprocedure,'truss.verify_umf_scalar_key_tuple(bytea,jsonb,jsonb)'::regprocedure)
                ) objects CROSS JOIN LATERAL aclexplode(coalesce(acl,acldefault(kind,owner))) a
                WHERE objects.owner<>%s OR a.grantee<>objects.owner)""",(owner_oid,),prepare=False)
            if cursor.fetchone()[0]:raise ValueError('Owner-only ACK receipt and typed-key helper privileges required')
            cursor.execute("""SELECT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
                WHERE p.oid IN ('truss.acknowledge_feed_with_receipt(text,bytea,bytea,text,text,text,text,bytea,text,text)'::regprocedure,
                    'truss.reconcile_feed_ack(text,bytea,bytea,text,text,text,text,bytea,text,text)'::regprocedure)
                AND (p.proowner<>%s OR a.grantee<>p.proowner AND
                    (a.privilege_type<>'EXECUTE' OR a.is_grantable OR NOT EXISTS(SELECT 1 FROM truss.runtime_feed_consumer c WHERE c.reader_oid=a.grantee))))""",(owner_oid,),prepare=False)
            if cursor.fetchone()[0]:raise ValueError('Only enrolled ordinary feed roles may execute ACK receipt facades')
            cursor.execute(sql.SQL('ALTER FUNCTION truss.valid_scalar_property(jsonb,text,boolean,jsonb) OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON FUNCTION truss.valid_scalar_property(jsonb,text,boolean,jsonb) FROM PUBLIC',prepare=False)
            cursor.execute(sql.SQL('ALTER FUNCTION truss.runtime_capture_feed_configuration() OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON FUNCTION truss.runtime_capture_feed_configuration() FROM PUBLIC',prepare=False)
            cursor.execute(sql.SQL('ALTER FUNCTION truss.catalog_check_source_correspondence(bytea,bytea,bytea) OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON FUNCTION truss.catalog_check_source_correspondence(bytea,bytea,bytea) FROM PUBLIC',prepare=False)
            cursor.execute(sql.SQL('ALTER FUNCTION truss.runtime_current_installation() OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON FUNCTION truss.runtime_current_installation() FROM PUBLIC',prepare=False)
            for signature in ('query_binding(jsonb,int,int,int,text,text)','query_scope(jsonb)','query_objects(jsonb,int)','query_numeric_value(text,text)','query_timestamp_instant_key(text,text)','query_edges(jsonb,int)','query_page_objects(jsonb,int,text)','query_object_attribution(jsonb,int,bigint)','query_complete_related_keys(jsonb,int,int)','query_object_times(jsonb,int,bigint)','query_object_load_id(jsonb,int,bigint)'):
                cursor.execute(sql.SQL('ALTER FUNCTION truss.{} OWNER TO {}').format(sql.SQL(signature),sql.Identifier(owner_role)),prepare=False)
                cursor.execute(sql.SQL('REVOKE ALL ON FUNCTION truss.{} FROM PUBLIC').format(sql.SQL(signature)),prepare=False)
                cursor.execute('SELECT reader_role,writer_role FROM truss.module_access',prepare=False)
                roles=sorted({role for row in cursor.fetchall() for role in row})
                for role in roles:
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(role)),prepare=False)
            cursor.execute(sql.SQL('ALTER FUNCTION truss.feed_reached(text,bytea,int,text,text) OWNER TO {}').format(sql.Identifier(owner_role)),prepare=False)
            cursor.execute('REVOKE ALL ON FUNCTION truss.feed_reached(text,bytea,int,text,text) FROM PUBLIC',prepare=False)
            cursor.execute('SELECT DISTINCT r.rolname FROM truss.runtime_feed_consumer c JOIN pg_roles r ON r.oid=c.reader_oid',prepare=False)
            for feed_role, in cursor.fetchall():
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.feed_reached(text,bytea,int,text,text) TO {}').format(sql.Identifier(feed_role)),prepare=False)
            cursor.execute('REVOKE ALL ON TYPE truss.runtime_release FROM PUBLIC',prepare=False)
            cursor.execute("""SELECT EXISTS(SELECT 1 FROM (
                SELECT relacl AS acl,relowner AS owner,'r'::"char" AS kind FROM pg_class WHERE oid='truss.runtime_feed_transaction_configuration'::regclass
                UNION ALL SELECT relacl,relowner,'r'::"char" FROM pg_class WHERE oid='truss.runtime_catalog_rebind_transition'::regclass
                UNION ALL SELECT typacl,typowner,'T'::"char" FROM pg_type WHERE oid='truss.runtime_catalog_rebind_transition'::regtype
                UNION ALL SELECT proacl,proowner,'f'::"char" FROM pg_proc WHERE pronamespace='truss'::regnamespace AND proname LIKE 'catalog_rebind_%%'
                UNION ALL SELECT typacl,typowner,'T'::"char" FROM pg_type WHERE oid='truss.runtime_feed_transaction_configuration'::regtype
                UNION ALL SELECT relacl,relowner,'r'::"char" FROM pg_class WHERE oid='truss.runtime_release'::regclass
                UNION ALL SELECT relacl,relowner,'s'::"char" FROM pg_class WHERE oid='truss.runtime_release_generation'::regclass
                UNION ALL SELECT typacl,typowner,'T'::"char" FROM pg_type WHERE oid='truss.runtime_release'::regtype
                UNION ALL SELECT proacl,proowner,'f'::"char" FROM pg_proc WHERE oid IN ('truss.runtime_endpoint_ownership(jsonb,int)'::regprocedure,'truss.runtime_capture_feed_configuration()'::regprocedure,'truss.catalog_check_source_correspondence(bytea,bytea,bytea)'::regprocedure,'truss.runtime_current_installation()'::regprocedure,'truss.valid_scalar_property(jsonb,text,boolean,jsonb)'::regprocedure)
                ) objects CROSS JOIN LATERAL aclexplode(coalesce(acl,acldefault(kind,owner))) a
                WHERE objects.owner<>%s OR a.grantee<>%s)""",(owner_oid,owner_oid),prepare=False)
            if cursor.fetchone()[0]:raise ValueError('Private owned migration objects required')
            cursor.execute('INSERT INTO truss.runtime_release(previous_release_id,previous_release_sha256,release_id,release_sha256,manifest_bytes,actor_oid) VALUES(%s,%s,%s,%s,%s,(SELECT oid FROM pg_roles WHERE rolname=session_user))',
                (active_release,active_digest,manifest['releaseId'],digest,bundled.joinpath('manifest.json').read_bytes()),prepare=False)
            cursor.execute("SELECT set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
            return PendingRuntimeUpgrade(identity,active_release,manifest['releaseId'],'upgraded')
        return self._host._run_operation(transaction,upgrade)

    @_active_operation
    def status_in_transaction(self,transaction: TransactionHandle) -> Outcome[CatalogRuntimeStatus]:
        self._available()
        manifest,digest,_=_release()
        local_failure=[None]
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')",prepare=False)
            if not cursor.fetchone()[0]:return CatalogRuntimeStatus(False)
            cursor.execute('SELECT * FROM truss.catalog_status()',prepare=False)
            row=cursor.fetchone()
            if row is None:raise ValueError('Complete installed status required')
            if row[1:3]!=(manifest['releaseId'],digest) or json.loads(row[3])!=manifest['layoutProfile']:
                local_failure[0]='unsupported_profile'
                raise ValueError('Unsupported installed catalog release')
            return CatalogRuntimeStatus(True,row[0],int(row[4]),('catalog:fresh-registration','catalog:compatible-evolution','import:host-owned-scalar-graph','catalog:report','catalog:view','direct_read:scalar-object-id','group:rootless-scalar-graph','direct_read:edge-id','direct_read:relationship-page','receipt:authority-visibility','feed:caller-asserted-authority','feed:destination-receipt-reconciliation','history:retained-native-groups','compiled_query:weft-scalar-runtime'),
                release_id=row[1],release_sha256=row[2],layout_profile=ProfilePin(**json.loads(row[3])))
        return _catalog_failure(self._host._run_operation(transaction,observe),local_failure[0])
    @_active_operation
    def accept_in_transaction(self,transaction: TransactionHandle,prepared: PreparedAcceptance,*,request_key: str,origin_bytes: bytes=b'{}',bun_executable: str='bun') -> Outcome[CatalogRegistration | CatalogUnchanged | CatalogAcceptanceRefused]:
        self._available()
        local_failure=[None]
        cache_current=[True]
        def reject(code,message):
            local_failure[0]=code
            raise ValueError(message)
        def require_original():
            try:_require_original_preparation(prepared)
            except ValueError:reject('invalid_input','Original unchanged preparation required')
        def produce(ordinal):
            require_original()
            choices={key:value for key,value in prepared.input().items() if key not in ('interfaceVersion','documents')}
            configurations=(_configuration(),_configuration('0.8.0'),{**_configuration(),'supportProfile':dict(DECIMAL207_PROFILE)},{**_configuration(),'supportProfile':dict(REFERENCE08_PROFILE)},{**_configuration(),'supportProfile':dict(RECURSIVE08_PROFILE)},{**_configuration(),'supportProfile':dict(DECIMAL208_PROFILE)},{**_configuration(),'supportProfile':dict(CONTAINER07_PROFILE)},{**_configuration(),'supportProfile':dict(CONTAINER08_PROFILE)},{**_configuration(),'supportProfile':dict(RETAINED_METADATA_PROFILE)},{**_configuration(),'supportProfile':dict(CORE08_PROFILE)},{**_configuration(),'supportProfile':dict(NAMED_RELATIONSHIP_PROFILE)})
            retained_layout=json.loads(files('truss').joinpath('_catalog_runtime','upgrade-source-051.json').read_bytes())['layoutProfile']
            configurations+=tuple({**entry,'layoutProfile':retained_layout} for entry in configurations)
            if choices not in configurations:reject('unsupported_profile','Exact selected catalog preparation required')
            try:valid_request=type(request_key) is str and 1<=len(request_key.encode('utf8'))<=1024 and '\0' not in request_key
            except UnicodeError:valid_request=False
            if not valid_request:reject('invalid_input','Stable request key required')
            from ._acceptance_json import decode_acceptance_json
            if type(origin_bytes) is not bytes:reject('invalid_input','Original asserted origin object required')
            try:origin=decode_acceptance_json(origin_bytes)
            except (ValueError,UnicodeError):reject('invalid_input','Original asserted origin object required')
            if type(origin) is not dict:reject('invalid_input','Original asserted origin object required')
            support=evaluate_catalog_support(prepared)
            semantic=compose_original_catalog_report_semantics(prepared,support)
            if semantic['state']!='source_fields_ready':reject('unsupported_profile','Complete original source inventory required')
            from ._owner_evidence_json import decode_owner_evidence_json
            evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
            source={'umf':semantic['umf'],'diagnostics':evidence['validation']['diagnostics'],
                'documentInterpretations':evidence['validation']['documentInterpretations'],
                'losses':evidence['ingress']['basis']['losses'],'extensions':semantic['extensions'],
                'transformRegistrations':evidence['ingress']['basis']['transformRegistrations'],
                'assertionEntries':semantic['assertionEntries']}
            if compact_catalog_sources(prepared):source['sourceFormat']=SOURCE_REFERENCE_FORMAT
            require_original()
            return (prepared.input_bytes,prepared.archive_documents_bytes,prepared.declarations_bytes,
                    canonical_numeric_free(source),origin_bytes,request_key)
        def execute(cursor,observed,ordinal,parameters):
            _pin_cursor(cursor)
            require_original()
            cursor.execute('SELECT * FROM truss.catalog_accept_with_keys(%s,%s,%s,%s,%s,%s,NULL,false)',parameters,prepare=False)
            rows=cursor.fetchmany(2)
            if len(rows)!=1:raise ValueError('Complete catalog result required')
            revision,identity,report,replayed,unchanged,actor,violations=rows[0]
            if violations is not None:
                if identity is not None or report is not None or replayed or unchanged:
                    raise ValueError('Refusal must not publish an acceptance')
                entries=json.loads(bytes(violations))
                if type(entries) is not list or not entries:raise ValueError('Nonempty compatibility violations required')
                parsed=[]
                for entry in entries:
                    count=entry['affectedObjectCount']
                    if type(count) is not str or not count.isascii() or not count.isdecimal() or count.startswith('0') or len(count)>19:
                        raise ValueError('Positive exact affected-object count required')
                    if set(entry)=={'documentId','moduleId','relationshipId','side','rule','affectedObjectCount'} and entry['side'] in ('source','target') and entry['rule'] in ('relationship.min','relationship.max'):
                        parsed.append(CatalogRelationshipCompatibilityViolation(entry['documentId'],entry['moduleId'],entry['relationshipId'],entry['side'],entry['rule'],int(count)))
                    elif set(entry)=={'documentId','moduleId','recordId','fieldModuleId','fieldId','rule','affectedObjectCount'} and entry['rule'] in ('property.required','property.scalar_type','property.facets','property.retained_name_collision','property.rebind_value'):
                        parsed.append(CatalogCompatibilityViolation(entry['documentId'],entry['moduleId'],entry['recordId'],entry['fieldModuleId'],entry['fieldId'],entry['rule'],int(count)))
                    elif set(entry)=={'documentId','moduleId','recordId','keyId','rule','affectedObjectCount'} and entry['rule']=='key.duplicate':
                        parsed.append(CatalogKeyCompatibilityViolation(entry['documentId'],entry['moduleId'],entry['recordId'],entry['keyId'],entry['rule'],int(count)))
                    else:raise ValueError('Qualified compatibility violation required')
                return CatalogAcceptanceRefused(int(revision),tuple(parsed))
            report=bytes(report);decoded=json.loads(report)
            if decoded['revision']!=revision or decoded['registrationId']!=identity or decoded['acceptedInput']!=prepared.input():
                raise ValueError('Original catalog result correspondence required')
            if replayed:
                cursor.execute('SELECT revision FROM truss.catalog_status()',prepare=False)
                cache_current[0]=cursor.fetchone()[0]==revision
            if unchanged:return CatalogUnchanged(int(revision),identity,report,replayed,request_key,origin_bytes,actor)
            return CatalogRegistration(int(revision),identity,report,replayed)
        result=_catalog_failure(self._host._run_semantic_operation(transaction,execute,parameter_producer=produce),local_failure[0])
        if isinstance(result,Ok) and not isinstance(result.value,CatalogAcceptanceRefused) and cache_current[0]:
            known={document.document_id:document for document in self._group_documents}
            for interpretation in prepared.documents:
                known[interpretation.document.document_id]=interpretation.document
            self._group_documents=tuple(known.values())
        return result
    @_active_operation
    def report_in_transaction(self,transaction: TransactionHandle,revision: int=1) -> Outcome[CatalogReport]:
        self._available()
        if type(revision) is not int or not 1<=revision<=2147483647:
            return Error(ExecutionFailure('execution_obligation','Valid catalog revision required',catalog_code='invalid_input'))
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.catalog_report(%s)',(revision,),prepare=False)
            raw=bytes(cursor.fetchone()[0])
            if json.loads(raw)['revision']!=str(revision):raise ValueError('Original report revision required')
            return CatalogReport(revision,raw)
        return _catalog_failure(self._host._run_operation(transaction,observe))

    def catalog_view_request(self,*,definition_count: str='65536',encoded_bytes: str='16777216') -> CatalogViewRequest:
        from .catalog_view import CatalogViewRequest, CatalogViewLimits, CurrentCatalogSelection, CompleteCatalogScope
        from .contracts import ProfilePin
        from ._catalog_view_build import VIEW_PROFILE
        manifest,_,_=_release()
        return CatalogViewRequest(layout_profile=ProfilePin(**manifest['layoutProfile']),view_profile=VIEW_PROFILE,
            selection=CurrentCatalogSelection(),scope=CompleteCatalogScope(),
            limits=CatalogViewLimits(definition_count=definition_count,encoded_bytes=encoded_bytes))

    @_active_operation
    def configure_module_access_in_transaction(self,transaction: TransactionHandle,grants: tuple[ModuleAccessGrant,...]) -> Outcome[PendingModuleAccessConfiguration]:
        """Configure existing module-policy rows as the trusted administrator.

        This does not grant raw-table privileges or install business capabilities.
        """
        if type(grants) is not tuple or not 1<=len(grants)<=512 or any(type(grant) is not ModuleAccessGrant for grant in grants):
            return Error(ExecutionFailure('execution_obligation','Bounded typed module grants required'))
        if len({(grant.document_id,grant.module_id) for grant in grants})!=len(grants):
            return Error(ExecutionFailure('execution_obligation','Unique document-qualified module grants required'))
        manifest,digest,_=_release()
        def configure(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
            original_path=cursor.fetchone()[0]
            cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
            cursor.execute("""SELECT current_user=session_user,pg_catalog.current_setting('role')='none',
              pg_catalog.current_setting('transaction_isolation')='read committed',
              pg_catalog.current_setting('transaction_read_only')='off'""",prepare=False)
            if cursor.fetchone()!=(True,True,True,True):raise ValueError('Direct read-write READ COMMITTED administrator required')
            from ._installation_privileges import installation_administrator_with_cursor
            cursor.execute('SELECT owner_oid FROM truss.catalog_runtime_installation',prepare=False)
            installation_administrator_with_cursor(cursor,cursor.fetchone()[0])
            cursor.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()',prepare=False)
            if cursor.fetchone()!=(manifest['releaseId'],digest):raise ValueError('Selected installed runtime required')
            cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT',prepare=False)
            if cursor.fetchone()[0]<1:raise ValueError('Accepted catalog head required')
            for grant in grants:
                cursor.execute("""SELECT EXISTS(SELECT 1 FROM truss.schema_doc d
                  CROSS JOIN LATERAL pg_catalog.jsonb_array_elements(d.document::pg_catalog.jsonb->'modules') m
                  WHERE d.doc_id=%s AND m.value->>'id'=%s)""",(grant.document_id,grant.module_id),prepare=False)
                if cursor.fetchone()!=(True,):raise ValueError('Accepted document-qualified module required')
                cursor.execute("""WITH RECURSIVE permission_roles(oid) AS (
                    SELECT oid FROM pg_catalog.pg_roles WHERE rolname::pg_catalog.text IN (%s::pg_catalog.text,%s::pg_catalog.text)
                    UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m JOIN permission_roles p ON m.member=p.oid)
                  SELECT CASE WHEN EXISTS(SELECT 1 FROM permission_roles p JOIN pg_catalog.pg_roles r ON r.oid=p.oid
                    CROSS JOIN truss.catalog_runtime_installation i
                    WHERE r.rolcanlogin OR r.rolsuper OR r.rolcreaterole OR r.rolcreatedb
                      OR r.rolreplication OR r.rolbypassrls OR r.oid IN (i.owner_oid,i.registrar_oid)
                      OR r.rolname::pg_catalog.text IN ('pg_read_server_files','pg_write_server_files','pg_execute_server_program')
                      OR pg_catalog.has_schema_privilege(r.oid,'truss','CREATE')
                      OR EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                        WHERE n.nspname='truss' AND ((c.relkind IN ('r','p') AND
                          (pg_catalog.has_table_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
                           OR pg_catalog.has_any_column_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')))
                          OR (c.relkind='S' AND pg_catalog.has_sequence_privilege(r.oid,c.oid,'USAGE,SELECT,UPDATE')))))
                   THEN 0 ELSE (SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname::pg_catalog.text IN (%s::pg_catalog.text,%s::pg_catalog.text)) END""",
                  (grant.reader_role,grant.writer_role,grant.reader_role,grant.writer_role),prepare=False)
                if cursor.fetchone()!=(2,):raise ValueError('Existing ordinary permission roles required')
            for grant in grants:
                cursor.execute('''SELECT reader_role,writer_role FROM truss.module_access
                  WHERE document_id=%s AND module=%s FOR UPDATE NOWAIT''',(grant.document_id,grant.module_id),prepare=False)
                before=cursor.fetchone()
                expected=(grant.reader_role,grant.writer_role)
                cursor.execute('''INSERT INTO truss.module_access(document_id,module,reader_role,writer_role)
                  VALUES(%s,%s,%s,%s) ON CONFLICT(document_id,module)
                  DO UPDATE SET reader_role=EXCLUDED.reader_role,writer_role=EXCLUDED.writer_role
                  WHERE (module_access.reader_role,module_access.writer_role)
                    IS DISTINCT FROM (EXCLUDED.reader_role,EXCLUDED.writer_role)
                  RETURNING reader_role,writer_role''',
                  (grant.document_id,grant.module_id,grant.reader_role,grant.writer_role),prepare=False)
                returned=cursor.fetchone()
                if returned!=expected and not (returned is None and before==expected):
                    raise ValueError('Complete native module grant write required')
                cursor.execute('''SELECT reader_role,writer_role FROM truss.module_access
                  WHERE document_id=%s AND module=%s''',(grant.document_id,grant.module_id),prepare=False)
                if cursor.fetchone()!=expected:raise ValueError('Exact native module grant readback required')
            for grant in grants:
                cursor.execute('''SELECT reader_role,writer_role FROM truss.module_access
                  WHERE document_id=%s AND module=%s''',(grant.document_id,grant.module_id),prepare=False)
                if cursor.fetchone()!=(grant.reader_role,grant.writer_role):raise ValueError('Complete native module grant batch required')
            from psycopg import sql
            for grant in grants:
                for role in (grant.reader_role,grant.writer_role):
                    cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(role)),prepare=False)
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.traverse_objects(jsonb,jsonb,int,int,int,text,text),truss.get_object(text,text,text,bigint,int,text,text),truss.get_edge(text,text,text,bigint,int,text,text),truss.reached(bytea,int,text,text),truss.feed_reached(text,bytea,int,text,text),truss.import_context(text,text),truss.import_key_selection(text,text,text,text,text),truss.import_identity_key_selection(bytea,text,text),truss.import_object_identity(bytea,bytea,bytea,text,text),truss.import_edge_identity(bytea,text,text),truss.import_record_source(uuid,bytea,text),truss.import_report_record_authority(bytea,text,text,text),truss.page_edges(text,text,text,jsonb,text,int,int,bytea,text,text) TO {}').format(sql.Identifier(role)),prepare=False)
            for grant in grants:
                for role in (grant.reader_role,grant.writer_role):
                    for signature in ('reader_catalog(int,int,text,text)','accepted_document(text,int,text,text)',
                                      'query_binding(jsonb,int,int,int,text,text)','query_scope(jsonb)','query_objects(jsonb,int)','query_numeric_value(text,text)','query_timestamp_instant_key(text,text)','query_edges(jsonb,int)','query_page_objects(jsonb,int,text)','query_object_attribution(jsonb,int,bigint)','query_complete_related_keys(jsonb,int,int)','query_object_times(jsonb,int,bigint)','query_object_load_id(jsonb,int,bigint)',
                                      'key_read_selection(text,text,text,text,bytea,text,text)',
                                      'lookup_string_key(text,text,text,text,bytea,bytea,bytea,int,text,text)',
                                      'page_objects(text,text,text,int,int,bytea,text,text)','read_history(jsonb,bytea,bigint,int,int,text,text)','lookup_import_source(jsonb,int,text,text)'):
                        cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(role)),prepare=False)
            for grant in grants:
                for role in (grant.reader_role,grant.writer_role):
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.group_context(text,text) TO {}').format(sql.Identifier(role)),prepare=False)
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.group_type_reference(text,text,text,text,text) TO {}').format(sql.Identifier(role)),prepare=False)
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.group_relationship_reference(text,text,text,text,text) TO {}').format(sql.Identifier(role)),prepare=False)
                for signature in ('group_create_metadata(bytea,bytea,text,text)','apply_create_group(bytea,bytea,bytea,bytea,text,text)','object_group_begin(bytea,bytea,bytea,text,text,bytea,boolean)','group_condition_key_metadata(bytea,bytea,text,text)','object_group_metadata(uuid,int)','object_group_step(uuid,int,bytea)','object_group_finish(uuid)'):
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(grant.writer_role)),prepare=False)
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
            return PendingModuleAccessConfiguration(grants)
        return self._host._run_operation(transaction,configure)

    @_active_operation
    def catalog_view_in_transaction(self,transaction: TransactionHandle,request: CatalogViewRequest) -> Outcome[CatalogViewAvailable | CatalogViewUnavailable]:
        from .catalog_view import (CatalogViewRequest, CatalogViewUnavailable, CatalogViewAvailable,
            HistoricalCatalogSelection, CompleteCatalogScope)
        from .contracts import ProfilePin
        from ._catalog_view_build import VIEW_PROFILE, build_catalog_view
        if type(request) is not CatalogViewRequest:
            return Error(ExecutionFailure('execution_obligation','Typed catalog view request required',catalog_code='invalid_input'))
        manifest,digest,_=_release()
        layout=ProfilePin(**manifest['layoutProfile'])
        if request.layout_profile!=layout or request.view_profile!=VIEW_PROFILE:
            return Ok(CatalogViewUnavailable(reason='profile'))
        if type(request.scope) is not CompleteCatalogScope:return Ok(CatalogViewUnavailable(reason='closure'))
        selected=None
        if type(request.selection) is HistoricalCatalogSelection:
            if len(request.selection.catalog_revision)>10 or int(request.selection.catalog_revision)>2147483647:return Ok(CatalogViewUnavailable(reason='context'))
            selected=int(request.selection.catalog_revision)
        def bounded(text,maximum):
            bound=str(maximum)
            return len(text)<len(bound) or (len(text)==len(bound) and text<=bound)
        if not bounded(request.limits.definition_count,65536) or not bounded(request.limits.encoded_bytes,16777216):
            return Ok(CatalogViewUnavailable(reason='resource'))
        count=int(request.limits.definition_count);size=int(request.limits.encoded_bytes)
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.catalog_view_basis(%s,%s,%s)',(selected,count,16777216),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:return CatalogViewUnavailable(reason='context')
            basis=json.loads(bytes(raw))
            if basis['releaseId']!=manifest['releaseId'] or basis['releaseSha256']!=digest or basis['layoutProfile']!=manifest['layoutProfile']:
                raise ValueError('Exact selected installed catalog release required')
            view=build_catalog_view(basis,layout)
            if len(view.definitions)>count or len(view.original_bytes)>size:return CatalogViewUnavailable(reason='resource')
            return CatalogViewAvailable(view=view)
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation' and result.error.sql_state=='54000':
            return Ok(CatalogViewUnavailable(reason='resource'))
        return _catalog_failure(result)

    @_active_operation
    def traverse_in_transaction(self,transaction: TransactionHandle,*,start: TypedIdentity,hops: tuple[TraversalHop,...],maximum_objects: int=100,maximum_path_states: int=10000,maximum_bytes: int=1048576) -> Outcome[TraversalComplete | TraversalLimited | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        """Return unique terminals after 1–3 hops, or refuse the whole observation.

        Limits bound logical attempted path states and output, not physical
        PostgreSQL scans or allocation. Each call observes live membership.
        """
        from .catalog_view import CatalogDefinitionReference
        if type(start) is not TypedIdentity or type(hops) is not tuple or not 1<=len(hops)<=3:
            return Ok(ObjectReadInvalid(code='selection'))
        if any(type(hop) is not TraversalHop or type(hop.relationship) is not CatalogDefinitionReference or hop.relationship.kind!='relationship' or hop.direction not in ('outgoing','incoming','both') for hop in hops):
            return Ok(ObjectReadInvalid(code='hops'))
        if any(type(value) is not int or not 1<=value<=bound for value,bound in ((maximum_objects,1000),(maximum_path_states,10000),(maximum_bytes,16777216))):
            return Ok(ObjectReadInvalid(code='limits'))
        manifest,digest,_=_release()
        selection=[{'direction':hop.direction,'relationship':{'kind':'relationship','definitionPin':hop.relationship.definition_pin,'owner':{'documentId':hop.relationship.owner.document_id,'moduleId':hop.relationship.owner.module_id},'authoredIdentity':hop.relationship.authored_identity,'relationshipId':hop.relationship.relationship_id}} for hop in hops]
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.traverse_objects(%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s)',(json.dumps({'id':start.id,'typeId':start.type_id,'definitionPin':start.definition_pin,'owner':{'documentId':start.owner.document_id,'moduleId':start.owner.module_id}}),json.dumps(selection),maximum_objects,maximum_path_states,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:return ObjectNotFound()
            basis=json.loads(bytes(raw))
            if basis['outcome']=='not_found':return ObjectNotFound()
            if basis['outcome']=='limited':return TraversalLimited(reason=basis['reason'])
            if basis['outcome']!='complete':raise ValueError('Complete traversal required')
            objects=tuple(_object_result(json.dumps(item).encode(),manifest,digest).object for item in basis['objects'])
            if tuple((o.type_id,o.id) for o in objects)!=tuple(sorted(set((o.type_id,o.id) for o in objects))):raise ValueError('Ordered unique traversal terminals required')
            return TraversalComplete(objects=objects,catalog_revision=int(basis['catalogRevision']))
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            if result.error.sql_state=='22023':return Ok(ObjectReadInvalid(code='selection'))
            reason={'0A000':'profile','54000':'resource','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
        return result

    @_active_operation
    def get_object_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,
                                  record_id: str,object_id: int,maximum_bytes: int=1048576) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        """Read complete supported logical values using current module membership.

        This scalar-string profile uses authored addresses and native identities;
        it does not claim the historical DirectRecord definition-pin profile.
        """
        try:
            valid=all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v
                      for v in (document_id,module_id,record_id))
        except UnicodeError:valid=False
        if not valid or type(object_id) is not int or not 1<=object_id<=9223372036854775807:
            return Ok(ObjectReadInvalid(code='selection'))
        if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:
            return Ok(ObjectReadInvalid(code='limits'))
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.get_object(%s,%s,%s,%s,%s,%s,%s)',
                (document_id,module_id,record_id,object_id,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:return ObjectNotFound()
            return _object_result(raw,manifest,digest)
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'0A000':'profile','54000':'resource','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
        return result

    def import_in_transaction(self,transaction: TransactionHandle,input: ImportInput,*,documents: tuple[CatalogDocument,...],bun_executable: str='bun') -> ImportExecutionResult[Literal['host_adopted']]:
        """Import with indexed per-record outcomes; accepted effects remain caller-owned pending."""
        from ._import_runtime import run_import
        from .imports import ImportExecutionFailed
        with self._lock:
            if self._disposed:return ImportExecutionFailed(error=ExecutionFailure('execution_obligation','Assembly disposed'),report=None)
            manifest,digest,_=_release()
            return run_import(self._host,transaction,input,documents,manifest,digest,_pin_cursor,bun_executable=bun_executable)

    @_active_operation
    def import_context_in_transaction(self,transaction: TransactionHandle) -> Outcome[ImportRuntimeContext]:
        from .import_runtime import ImportRuntimeContext
        from .imports import ImportCatalogPin
        from .contracts import ProfilePin
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]))
            return ImportRuntimeContext(layout_profile=ProfilePin(**value['layoutProfile']),import_profile=ProfilePin(**value['importProfile']),
                value_profile=ProfilePin(**value['valueProfile']),payload_profile=ProfilePin(**value['importPayloadProfile']),
                catalog=ImportCatalogPin(revision=value['catalog']['revision'],model_bundle_sha256=value['catalog']['modelBundleSha256']))
        return self._host._run_operation(transaction,observe)

    @_active_operation
    def edge_import_record_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                         source_endpoint: TypedIdentity,target_endpoint: TypedIdentity,values: tuple[AuthoredValue,...],
                                         order_key: OrderKey,source: MapValue | None=None) -> Outcome[EdgeImportRecord]:
        """Build an edge import with an accepted pin; execution validates endpoints."""
        from .contracts import ProfilePin
        from .imports import EdgeImportIdentity,ImportCatalogPin
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            if type(source_endpoint) is not TypedIdentity or type(target_endpoint) is not TypedIdentity:
                raise ValueError('Exact caller endpoint identities required')
            cursor.execute('SELECT truss.import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
            context=json.loads(bytes(cursor.fetchone()[0]))
            builder=ImportRuntimeContext(layout_profile=ProfilePin(**context['layoutProfile']),import_profile=ProfilePin(**context['importProfile']),
                value_profile=ProfilePin(**context['valueProfile']),payload_profile=ProfilePin(**context['importPayloadProfile']),
                catalog=ImportCatalogPin(revision=context['catalog']['revision'],model_bundle_sha256=context['catalog']['modelBundleSha256']))
            payload=builder.edge_payload(values,order_key,source=source)
            cursor.execute('SELECT truss.group_relationship_reference(%s,%s,%s,%s,%s)',
                (document_id,module_id,relationship_id,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:raise ValueError('Available accepted relationship reference required')
            reference=json.loads(bytes(raw))
            return EdgeImportRecord(identity=EdgeImportIdentity(relationship_definition_pin=reference['definitionPin'],
                source=source_endpoint,target=target_endpoint),payload=payload,payload_profile=builder.payload_profile)
        return self._host._run_operation(transaction,observe)

    @_active_operation
    def object_import_record_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,
                                            values: tuple[AuthoredValue,...],source: MapValue | None=None) -> Outcome[ObjectImportRecord]:
        """Construct import identity from actual accepted primary-key definitions."""
        from .contracts import ObjectKeySelection,ObjectKeyComponent,ReadTypeReference,QualifiedOwner,ProfilePin,TextValue
        from .imports import ObjectImportRecord,ImportCatalogPin
        from .import_runtime import ImportRuntimeContext
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.import_key_selection(%s,%s,%s,%s,%s)',(document_id,module_id,record_id,manifest['releaseId'],digest),prepare=False)
            selection=json.loads(bytes(cursor.fetchone()[0]));components=[]
            for selected in selection['components']:
                matching=tuple(v.value for v in values if v.name==selected['name'])
                if len(matching)!=1 or not (type(matching[0]) is BooleanValue or type(matching[0]) is TextValue and matching[0].kind in ('string','integer','decimal','binary')):raise ValueError('Complete exact primary-key values required')
                components.append(ObjectKeyComponent(property_id=selected['propertyId'],definition_pin=selected['definitionPin'],value=matching[0]))
            identity=ObjectKeySelection(type=ReadTypeReference(type_id=selection['type']['typeId'],definition_pin=selection['type']['definitionPin'],
                owner=QualifiedOwner(document_id=document_id,module_id=module_id)),key_number=selection['keyNumber'],key_definition_pin=selection['keyDefinitionPin'],
                key_encoding_profile=ProfilePin(**selection['keyEncodingProfile']),components=tuple(components))
            cursor.execute('SELECT truss.import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False);context=json.loads(bytes(cursor.fetchone()[0]))
            builder=ImportRuntimeContext(layout_profile=ProfilePin(**context['layoutProfile']),import_profile=ProfilePin(**context['importProfile']),
                value_profile=ProfilePin(**context['valueProfile']),payload_profile=ProfilePin(**context['importPayloadProfile']),
                catalog=ImportCatalogPin(revision=context['catalog']['revision'],model_bundle_sha256=context['catalog']['modelBundleSha256']))
            return ObjectImportRecord(identity=identity,payload=builder.object_payload(values,source=source),payload_profile=builder.payload_profile)
        return self._host._run_operation(transaction,observe)

    @_active_operation
    def reached_in_transaction(self,transaction: TransactionHandle,token: str,*,maximum_token_bytes: int=16384,
                               maximum_evidence_bytes: int=1048576,consumer_id: str | None=None) -> Outcome[ReceiptIncluded | ReceiptVisibilityUnavailable]:
        """Resolve committed Truss effects in this authority read-only transaction; never wait."""
        from ._receipt_position import decode_receipt_position
        from .contracts import ProfilePin
        if type(maximum_token_bytes) is not int or not 1<=maximum_token_bytes<=16384 or type(maximum_evidence_bytes) is not int or not 1<=maximum_evidence_bytes<=16777216:
            return Ok(ReceiptVisibilityUnavailable(reason='resource'))
        if type(token) is not str:return Ok(ReceiptVisibilityUnavailable(reason='invalid_token'))
        if len(token)>maximum_token_bytes:return Ok(ReceiptVisibilityUnavailable(reason='resource'))
        try:locator=decode_receipt_position(token)
        except (ValueError,UnicodeError):return Ok(ReceiptVisibilityUnavailable(reason='invalid_token'))
        try:consumer_valid=consumer_id is None or type(consumer_id) is str and 1<=len(consumer_id.encode('utf8'))<=4096 and chr(0) not in consumer_id
        except UnicodeError:consumer_valid=False
        if not consumer_valid:return Ok(ReceiptVisibilityUnavailable(reason='invalid_consumer'))
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            if consumer_id is None:
                cursor.execute('SELECT truss.reached(%s,%s,%s,%s)',(locator.original_bytes,maximum_evidence_bytes,manifest['releaseId'],digest),prepare=False)
            else:
                cursor.execute('SELECT truss.feed_reached(%s,%s,%s,%s,%s)',(consumer_id,locator.original_bytes,maximum_evidence_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]))
            if value['outcome']=='unavailable':return ReceiptVisibilityUnavailable(reason=value['reason'])
            return ReceiptIncluded(included=value['included'],comparison_profile=ProfilePin(**value['comparisonProfile']))
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'42501':'authorization','0A000':'epoch_profile','54000':'resource','55P03':'observation_integrity','55000':'observation_integrity'}.get(result.error.sql_state)
            if reason:return Ok(ReceiptVisibilityUnavailable(reason=reason))
        return result

    @_active_operation
    def get_edge_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,
                                relationship_id: str,edge_id: int,maximum_bytes: int=1048576) -> Outcome[EdgeFound | EdgeNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        """Read one authorized independent edge, preserving exact scalar values."""
        return self._read_edges(transaction,document_id,module_id,relationship_id,edge_id=edge_id,maximum_bytes=maximum_bytes)

    @_active_operation
    def page_edges_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                  anchor: TypedIdentity, direction: Literal['outgoing','incoming']='outgoing',limit: int=100,
                                  maximum_bytes: int=1048576,continuation: EdgePageCursor | None=None) -> Outcome[EdgePage | EdgeNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        """Read a live relationship page ordered by order key, then native ID."""
        return self._read_edges(transaction,document_id,module_id,relationship_id,anchor=anchor,direction=direction,limit=limit,maximum_bytes=maximum_bytes,continuation=continuation)

    def _read_edges(self,transaction,document_id,module_id,relationship_id,*,edge_id=None,anchor=None,direction='outgoing',limit=100,maximum_bytes=1048576,continuation=None):
        from .contracts import TypedIdentity
        from ._group_runtime import _wire,_bytes
        try:valid=all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (document_id,module_id,relationship_id))
        except UnicodeError:valid=False
        if not valid or edge_id is not None and (type(edge_id) is not int or not 1<=edge_id<=9223372036854775807):return Ok(ObjectReadInvalid(code='selection'))
        if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:return Ok(ObjectReadInvalid(code='limits'))
        if edge_id is None and (type(anchor) is not TypedIdentity or direction not in ('outgoing','incoming') or type(limit) is not int or not 1<=limit<=1000
            or continuation is not None and (type(continuation) is not EdgePageCursor or type(continuation.content) is not bytes or not 1<=len(continuation.content)<=65536)):
            return Ok(ObjectReadInvalid(code='selection'))
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            if edge_id is not None:
                cursor.execute('SELECT truss.get_edge(%s,%s,%s,%s,%s,%s,%s)',(document_id,module_id,relationship_id,edge_id,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            else:
                cursor.execute('SELECT truss.page_edges(%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s)',
                    (document_id,module_id,relationship_id,_bytes(_wire(anchor)).decode('utf8'),direction,limit,maximum_bytes,None if continuation is None else continuation.content,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:return EdgeNotFound()
            value=json.loads(bytes(raw))
            if edge_id is not None:return EdgeFound(edge=_edge_result(value))
            token=None if value['continuation'] is None else EdgePageCursor(content=_bytes(value['continuation']))
            return EdgePage(edges=tuple(_edge_result(v) for v in value['edges']),catalog_revision=value['catalogRevision'],continuation=token)
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'0A000':'profile','54000':'resource','55P03':'observation','P1002':'context'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
            if result.error.sql_state=='22023':return Ok(ObjectReadInvalid(code='selection'))
        return result

    @_active_operation
    def page_objects_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,
                                    limit: int=100,cursor: ObjectPageCursor | None=None,maximum_bytes: int=1048576) -> Outcome[ObjectPage | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        try:
            valid=all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (document_id,module_id,record_id))
        except UnicodeError:valid=False
        if not valid:return Ok(ObjectReadInvalid(code='selection'))
        if type(limit) is not int or not 1<=limit<=1000 or type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:
            return Ok(ObjectReadInvalid(code='limits'))
        cursor_bytes=None
        if cursor is not None:
            if type(cursor) is not ObjectPageCursor:return Ok(ObjectReadInvalid(code='cursor'))
            if (cursor.document_id,cursor.module_id,cursor.record_id)!=(document_id,module_id,record_id):return Ok(ObjectReadInvalid(code='cursor_selection'))
            if any(type(v) is not int or not 1<=v<=maximum for v,maximum in ((cursor.type_id,2147483647),(cursor.catalog_revision,2147483647),(cursor.after_id,9223372036854775807))):
                return Ok(ObjectReadInvalid(code='cursor'))
            try:
                if cursor.profile!='truss-python-object-page/0.1' or any(type(v) is not str or not 1<=len(v.encode('utf8'))<=4096 or '\0' in v for v in (cursor.installation_id,cursor.source_epoch,cursor.release_sha256,cursor.definition_pin)):
                    return Ok(ObjectReadInvalid(code='cursor'))
                cursor_bytes=json.dumps({'profile':cursor.profile,'installationId':cursor.installation_id,'sourceEpoch':cursor.source_epoch,
                    'releaseSha256':cursor.release_sha256,'documentId':document_id,'moduleId':module_id,'recordId':record_id,
                    'typeId':str(cursor.type_id),'definitionPin':cursor.definition_pin,'catalogRevision':str(cursor.catalog_revision),'afterId':str(cursor.after_id)},ensure_ascii=False).encode('utf8')
            except UnicodeError:return Ok(ObjectReadInvalid(code='cursor'))
            if len(cursor_bytes)>65536:return Ok(ObjectReadInvalid(code='cursor'))
        manifest,digest,_=_release()
        def observe(native_cursor,observed):
            _pin_cursor(native_cursor)
            native_cursor.execute('SELECT truss.page_objects(%s,%s,%s,%s,%s,%s,%s,%s)',
                (document_id,module_id,record_id,limit,maximum_bytes,cursor_bytes,manifest['releaseId'],digest),prepare=False)
            raw=native_cursor.fetchone()[0]
            if raw is None:return ObjectNotFound()
            basis=json.loads(bytes(raw))
            if basis['profile']!='truss-python-object-page/0.1':raise ValueError('Exact page profile required')
            continuation=basis['continuation'];following=None
            if continuation is not None:
                following=ObjectPageCursor(installation_id=continuation['installationId'],source_epoch=continuation['sourceEpoch'],
                    release_sha256=continuation['releaseSha256'],document_id=continuation['documentId'],module_id=continuation['moduleId'],record_id=continuation['recordId'],
                    type_id=int(continuation['typeId']),definition_pin=continuation['definitionPin'],catalog_revision=int(continuation['catalogRevision']),after_id=int(continuation['afterId']))
            return ObjectPage(objects=tuple(_object_result(json.dumps(value).encode(),manifest,digest).object for value in basis['objects']),
                catalog_revision=basis['catalogRevision'],continuation=following)
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            if result.error.sql_state=='22023':return Ok(ObjectReadInvalid(code='cursor'))
            reason={'0A000':'profile','P1002':'context','54000':'resource','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
        return result

    @_active_operation
    def group_context_in_transaction(self,transaction: TransactionHandle) -> Outcome[GroupRuntimeContext]:
        from ._group_runtime import group_context
        manifest,digest,_=_release()
        return group_context(self._host,transaction,manifest,digest,_pin_cursor)

    @_active_operation
    def apply_in_transaction(self,transaction: TransactionHandle,input: GroupSemanticInput,request: GroupRequestSelection,*,
                             documents: tuple[CatalogDocument,...]=(),bun_executable: str='bun') -> Outcome[GroupApplicationResult]:
        """Apply one atomic group; host owns outer commit/rollback and durability."""
        from ._group_runtime import apply_group
        manifest,digest,_=_release()
        return apply_group(self._host,transaction,input,request,documents or self._group_documents,
                           manifest,digest,_pin_cursor,bun_executable=bun_executable)

    @_active_operation
    def get_type_reference_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str) -> Outcome[CatalogDefinitionReference | None]:
        """Resolve a genuine accepted type pin using current module read/write authority."""
        from .catalog_view import CatalogDefinitionReference
        from .contracts import QualifiedOwner
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.group_type_reference(%s,%s,%s,%s,%s)',
                (document_id,module_id,record_id,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:return None
            value=json.loads(bytes(raw))
            return CatalogDefinitionReference(kind='type',definition_pin=value['definitionPin'],type_id=value['typeId'],
                authored_identity=value['authoredIdentity'],owner=QualifiedOwner(document_id=value['owner']['documentId'],module_id=value['owner']['moduleId']))
        return self._host._run_operation(transaction,observe)

    @_active_operation
    def get_relationship_reference_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str) -> Outcome[CatalogDefinitionReference | None]:
        from .contracts import QualifiedOwner
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.group_relationship_reference(%s,%s,%s,%s,%s)',
                (document_id,module_id,relationship_id,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            if raw is None:return None
            value=json.loads(bytes(raw))
            return CatalogDefinitionReference(kind='relationship',definition_pin=value['definitionPin'],relationship_id=value['relationshipId'],
                authored_identity=value['authoredIdentity'],owner=QualifiedOwner(document_id=value['owner']['documentId'],module_id=value['owner']['moduleId']))
        return self._host._run_operation(transaction,observe)

    @property
    def group_selection(self) -> CapabilitySelection[Literal['group']]:
        """Exact supported provider selection; does not assert database readiness."""
        from .contracts import CapabilitySelection, ProfilePin
        manifest,_,_=_release()
        entries=json.loads(files('truss').joinpath('_catalog_runtime','group-profiles.json').read_bytes())['profiles']
        pins={entry['name']:ProfilePin(**entry['pin']) for entry in entries}
        return CapabilitySelection(family='group',capability_profile=pins['mutationProfile'],
            layout_profile=ProfilePin(**manifest['layoutProfile']),adapter_profile=pins['adapterProfile'],
            value_profile=pins['valueProfile'],policy_profile=pins['policyProfile'])

    def groups(self,selection: CapabilitySelection[Literal['group']],*,documents: tuple[CatalogDocument,...]=(),bun_executable: str='bun') -> GroupCapabilityAvailable | CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            if type(selection) is not CapabilitySelection or selection!=self.group_selection:return CapabilityUnavailable(reason='selection')
            def apply(transaction,input,request):
                return self.apply_in_transaction(transaction,input,request,documents=documents,bun_executable=bun_executable)
            return GroupCapabilityAvailable(capability=NativeGroupCapability(selection=self.group_selection,_apply=apply))

    def _reader_result(self,result):
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            state=result.error.sql_state
            if state=='42501':return Ok(CatalogRefused())
            reason={'0A000':'profile','25006':'profile','54000':'resource','55P03':'observation','42P01':'installation','42883':'installation'}.get(state)
            if reason:return Ok(CatalogUnavailable(code=reason))
        return result

    @_active_operation
    def lookup_import_source_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,maximum_bytes: int=1048576) -> Outcome[ImportSourceFound | ImportSourceAbsent | ImportSourceUnavailable]:
        """Read committed native import provenance, including after deletion."""
        try:
            valid=type(entity) is HistoryEntity and entity.kind in ('object','edge') and type(entity.id) is int and 1<=entity.id<=9223372036854775807
            valid=valid and all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (entity.document_id,entity.module_id,entity.definition_id))
        except (UnicodeError,TypeError):valid=False
        if not valid:return Ok(ImportSourceUnavailable(reason='context'))
        if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:return Ok(ImportSourceUnavailable(reason='resource'))
        manifest,digest,_=_release()
        selection=json.dumps({'kind':entity.kind,'documentId':entity.document_id,'moduleId':entity.module_id,'definitionId':entity.definition_id,'id':str(entity.id)})
        def read(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.lookup_import_source(%s::jsonb,%s,%s,%s)',(selection,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]))
            if value['outcome']=='absent':return ImportSourceAbsent()
            content=base64.b64decode(value['contentBase64'],validate=True)
            if sha256(content).hexdigest()!=value['sha256']:raise ValueError('Exact retained native provenance required')
            return ImportSourceFound(load_id=value['loadId'],content=content,sha256=value['sha256'],writer_xid=value['writerXid'])
        result=self._host._run_operation(transaction,read)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'42501':'authorization','22023':'context','0A000':'profile','55000':'integrity','54000':'resource','P1010':'observation','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ImportSourceUnavailable(reason=reason))
        return result

    @_active_operation
    def page_history_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,cursor: HistoryCursor | None=None,
                                    maximum_events: int=4096,maximum_bytes: int=8388608) -> Outcome[HistoryPage | HistoryUnavailable]:
        """Read one complete committed entity mutation group in journal order."""
        return self._read_history(transaction,entity,cursor,None,maximum_events,maximum_bytes)

    @_active_operation
    def reconstruct_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,version: int,
                                   maximum_events: int=4096,maximum_bytes: int=8388608) -> Outcome[HistoricalRecord | HistoricalDeleted | HistoryUnavailable]:
        """Return a retained full version image, or the real deletion marker."""
        if type(version) is not int or not 1<=version<=9223372036854775807:return Ok(HistoryUnavailable(reason='context'))
        return self._read_history(transaction,entity,None,version,maximum_events,maximum_bytes)

    def _read_history(self,transaction,entity,cursor,version,maximum_events,maximum_bytes):
        try:
            valid=type(entity) is HistoryEntity and entity.kind in ('object','edge') and type(entity.id) is int and 1<=entity.id<=9223372036854775807
            valid=valid and all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (entity.document_id,entity.module_id,entity.definition_id))
        except (UnicodeError,TypeError):valid=False
        if not valid or cursor is not None and (type(cursor) is not HistoryCursor or type(cursor.content) is not bytes or not 1<=len(cursor.content)<=16384):return Ok(HistoryUnavailable(reason='context'))
        if type(maximum_events) is not int or not 1<=maximum_events<=65536 or type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:return Ok(HistoryUnavailable(reason='resource'))
        manifest,digest,_=_release()
        selection=json.dumps({'kind':entity.kind,'documentId':entity.document_id,'moduleId':entity.module_id,'definitionId':entity.definition_id,'id':str(entity.id)})
        def retained(value):
            content=base64.b64decode(value['contentBase64'],validate=True)
            if sha256(content).hexdigest()!=value['sha256']:raise ValueError('Original retained event required')
            return RetainedHistoryEvent(content=content,sha256=value['sha256'],writer_xid=value['writerXid'],seq=value['seq'],version=int(value['version']))
        def read(native_cursor,observed):
            _pin_cursor(native_cursor)
            native_cursor.execute('SELECT truss.read_history(%s::jsonb,%s,%s,%s,%s,%s,%s)',(selection,None if cursor is None else cursor.content,version,maximum_events,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(native_cursor.fetchone()[0]))
            if value['outcome']=='page':
                continuation=None if 'cursorBase64' not in value else HistoryCursor(content=base64.b64decode(value['cursorBase64'],validate=True))
                return HistoryPage(events=tuple(retained(v) for v in value['events']),continuation=continuation,safe_watermark_xid=value['safeWatermarkXid'])
            record=base64.b64decode(value['recordBase64'],validate=True);event=retained(value['event'])
            if value['outcome']=='deleted':return HistoricalDeleted(deletion_version=int(value['version']),before=record,event=event)
            return HistoricalRecord(record=record,event=event)
        result=self._host._run_operation(transaction,read)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'42501':'authorization','54000':'resource','55P03':'observation','0A000':'profile','55000':'integrity','22023':'context','P1010':'history'}.get(result.error.sql_state)
            if reason:return Ok(HistoryUnavailable(reason=reason))
        return result

    @_active_operation
    def register_feed_consumer_in_transaction(self, transaction: TransactionHandle, *, consumer_id: str, reader_role: str) -> Outcome[FeedConsumer]:
        """Installation administrator enrolls a full-source consumer from genesis.

        Registration and role grants remain subject to the caller's commit.
        """
        from .feed import FeedConsumer, FeedCursor
        from ._installation_privileges import _name
        from psycopg import sql
        if type(consumer_id) is not str or not consumer_id or '\0' in consumer_id or len(consumer_id.encode('utf8'))>4096 or not _name(reader_role):
            return Error(ExecutionFailure('execution_obligation','Bounded consumer and role required'))
        manifest,digest,_=_release()
        def register(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
            original_path=cursor.fetchone()[0]
            cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
            from ._installation_privileges import installation_administrator_with_cursor
            cursor.execute('SELECT owner_oid FROM truss.catalog_runtime_installation',prepare=False)
            installation_administrator_with_cursor(cursor,cursor.fetchone()[0])
            cursor.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()',prepare=False)
            if cursor.fetchone()!=(manifest['releaseId'],digest):raise ValueError('Exact installed feed release required')
            cursor.execute('SELECT oid FROM pg_roles WHERE rolname=%s AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls',(reader_role,),prepare=False)
            role=cursor.fetchone()
            if role is None:raise ValueError('Ordinary native consumer role required')
            cursor.execute('SELECT reader_oid,registration_id::text,checkpoint_bytes FROM truss.runtime_feed_consumer WHERE consumer_id=%s FOR UPDATE NOWAIT',(consumer_id,),prepare=False)
            existing=cursor.fetchone()
            if existing is not None:
                if existing[0]!=role[0]:raise ValueError('Original consumer role required')
                registration,checkpoint=existing[1],bytes(existing[2])
            else:
                cursor.execute("INSERT INTO truss.runtime_feed_consumer(consumer_id,reader_oid,checkpoint_bytes) VALUES(%s,%s,''::bytea) RETURNING registration_id::text",(consumer_id,role[0]),prepare=False)
                registration=cursor.fetchone()[0]
                cursor.execute("SELECT truss.runtime_feed_cursor(%s,'0')",(consumer_id,),prepare=False)
                checkpoint=bytes(cursor.fetchone()[0])
                cursor.execute('UPDATE truss.runtime_feed_consumer SET checkpoint_bytes=%s WHERE consumer_id=%s',(checkpoint,consumer_id),prepare=False)
            cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(reader_role)),prepare=False)
            cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.feed_reached(text,bytea,int,text,text),truss.read_feed(text,int,int,text,text),truss.reread_feed(text,bytea,bytea,text,int,int,text,text),truss.acknowledge_feed(text,bytea,bytea,text,text,text),truss.acknowledge_feed_with_receipt(text,bytea,bytea,text,text,text,text,bytea,text,text),truss.reconcile_feed_ack(text,bytea,bytea,text,text,text,text,bytea,text,text) TO {}').format(sql.Identifier(reader_role)),prepare=False)
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
            return FeedConsumer(consumer_id=consumer_id,registration_id=registration,checkpoint=FeedCursor(content=checkpoint))
        return self._host._run_operation(transaction,register)

    def _feed_result(self,result):
        from .feed import FeedUnavailable
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reasons={'42501':'authorization','54000':'resource','55P03':'context','0A000':'profile','P1001':'conflict','22023':'context','55000':'integrity','25006':'context'}
            reason=reasons.get(result.error.sql_state)
            if reason:return Ok(FeedUnavailable(reason=reason))
        return result

    @_active_operation
    def read_feed_in_transaction(self,transaction: TransactionHandle,*,consumer_id: str,maximum_facts: int=4096,maximum_bytes: int=8388608) -> Outcome[FeedPage | FeedUnavailable]:
        """Read the next whole committed transaction or a safe empty interval.

        Polling does not acknowledge or assign a transaction ID. Read-only
        READ COMMITTED caller transactions are supported.
        """
        from .feed import FeedPage,FeedCursor,FeedUnavailable
        if type(consumer_id) is not str or not consumer_id or '\0' in consumer_id or len(consumer_id.encode('utf8'))>4096 or type(maximum_facts) is not int or not 1<=maximum_facts<=65536 or type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:
            return Ok(FeedUnavailable(reason='resource'))
        manifest,digest,_=_release()
        def read(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.read_feed(%s,%s,%s,%s,%s)',(consumer_id,maximum_facts,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]));content=base64.b64decode(value['payloadBase64'],validate=True)
            if sha256(content).hexdigest()!=value['sha256']:raise ValueError('Original complete feed payload required')
            return FeedPage(consumer_id=value['consumerId'],registration_id=value['registrationId'],
                prior=FeedCursor(content=base64.b64decode(value['priorBase64'],validate=True)),next=FeedCursor(content=base64.b64decode(value['nextBase64'],validate=True)),
                content=content,sha256=value['sha256'],writer_xid=value['writerXid'],safe_watermark_xid=value['safeWatermarkXid'],outcome=value['outcome'])
        return self._feed_result(self._host._run_operation(transaction,read))

    @_active_operation
    def reread_feed_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,maximum_facts: int=4096,maximum_bytes: int=8388608) -> Outcome[FeedPage | FeedUnavailable]:
        """Reproduce an original retained delivery, including after committed ACK.

        Requires current source authority and the original consumer registration.
        Does not change the checkpoint. Supports read-only READ COMMITTED.
        The returned watermark describes this reproduction's interval frontier.
        """
        from .feed import FeedPage,FeedCursor,FeedUnavailable
        if type(page) is not FeedPage or type(page.content) is not bytes or type(page.sha256) is not str or sha256(page.content).hexdigest()!=page.sha256:
            return Ok(FeedUnavailable(reason='integrity'))
        if type(maximum_facts) is not int or not 1<=maximum_facts<=65536 or type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:
            return Ok(FeedUnavailable(reason='resource'))
        if type(page.prior) is not FeedCursor or type(page.next) is not FeedCursor or type(page.prior.content) is not bytes or type(page.next.content) is not bytes:
            return Ok(FeedUnavailable(reason='integrity'))
        manifest,digest,_=_release()
        def read(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.reread_feed(%s,%s,%s,%s,%s,%s,%s,%s)',
                (page.consumer_id,page.prior.content,page.next.content,page.sha256,maximum_facts,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]));content=base64.b64decode(value['payloadBase64'],validate=True)
            prior=FeedCursor(content=base64.b64decode(value['priorBase64'],validate=True))
            next_cursor=FeedCursor(content=base64.b64decode(value['nextBase64'],validate=True))
            if (content!=page.content or sha256(content).hexdigest()!=value['sha256'] or value['sha256']!=page.sha256
                or prior!=page.prior or next_cursor!=page.next or value['consumerId']!=page.consumer_id
                or value['registrationId']!=page.registration_id or value['writerXid']!=page.writer_xid or value['outcome']!=page.outcome):
                return FeedUnavailable(reason='integrity')
            return FeedPage(consumer_id=value['consumerId'],registration_id=value['registrationId'],prior=prior,next=next_cursor,
                content=content,sha256=value['sha256'],writer_xid=value['writerXid'],safe_watermark_xid=value['safeWatermarkXid'],outcome=value['outcome'])
        return self._feed_result(self._host._run_operation(transaction,read))

    @_active_operation
    def acknowledge_feed_with_receipt_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,destination_id: str,request_sha256: str,publication_id: str,receipt_bytes: bytes) -> Outcome[FeedReceiptAcknowledged | FeedUnavailable]:
        """Retain opaque destination evidence with ACK; caller owns outer commit."""
        return self._feed_ack_receipt_operation(transaction,page,destination_id,request_sha256,publication_id,receipt_bytes,reconcile=False)

    @_active_operation
    def reconcile_feed_ack_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,destination_id: str,request_sha256: str,publication_id: str,receipt_bytes: bytes) -> Outcome[FeedAckReconciled | FeedUnavailable]:
        """Fresh read-only source receipt observation, with no ACK write."""
        return self._feed_ack_receipt_operation(transaction,page,destination_id,request_sha256,publication_id,receipt_bytes,reconcile=True)

    def _feed_ack_receipt_operation(self,transaction,page,destination_id,request_sha256,publication_id,receipt_bytes,*,reconcile):
        import re
        from .feed import FeedCursor
        try:
            valid=(type(page) is FeedPage and type(page.content) is bytes and sha256(page.content).hexdigest()==page.sha256
                and type(receipt_bytes) is bytes and 1<=len(receipt_bytes)<=1048576
                and all(type(v) is str and '\0' not in v and 1<=len(v.encode('utf8'))<=maximum for v,maximum in ((destination_id,1024),(publication_id,4096)))
                and type(request_sha256) is str and re.fullmatch('[0-9a-f]{64}',request_sha256) is not None)
        except (UnicodeError,TypeError):valid=False
        if not valid:return Ok(FeedUnavailable(reason='context'))
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            routine='reconcile_feed_ack' if reconcile else 'acknowledge_feed_with_receipt'
            cursor.execute('SELECT truss.'+routine+'(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (page.consumer_id,page.prior.content,page.next.content,page.sha256,destination_id,request_sha256,publication_id,receipt_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]));binding=value['binding'];retained=None
            checkpoint=FeedCursor(content=base64.b64decode(value['checkpointBase64'],validate=True))
            if binding is not None:
                original=base64.b64decode(value['receiptBase64'],validate=True)
                if sha256(original).hexdigest()!=binding['receiptSha256'] or binding['consumerId']!=page.consumer_id or binding['registrationId']!=page.registration_id:
                    raise ValueError('Original ACK receipt correspondence required')
                retained=FeedAckReceipt(installation_id=binding['installationId'],source_epoch=binding['sourceEpoch'],consumer_id=binding['consumerId'],registration_id=binding['registrationId'],
                    prior=FeedCursor(content=base64.b64decode(value['priorBase64'],validate=True)),next=FeedCursor(content=base64.b64decode(value['nextBase64'],validate=True)),feed_sha256=binding['feedSha256'],
                    destination_id=binding['destinationId'],request_sha256=binding['requestSha256'],publication_id=binding['publicationId'],receipt_bytes=original,receipt_sha256=binding['receiptSha256'])
            if reconcile:
                if value['outcome'] not in ('matched','missing','conflicting') or (retained is None)!=(value['outcome']=='missing'):raise ValueError('Exact ACK reconciliation result required')
                return FeedAckReconciled(checkpoint=checkpoint,outcome=value['outcome'],receipt=retained)
            if retained is None or value['outcome'] not in ('advanced','equal'):raise ValueError('Exact pending ACK receipt result required')
            return FeedReceiptAcknowledged(receipt=retained,checkpoint=checkpoint,outcome=value['outcome'])
        return self._feed_result(self._host._run_operation(transaction,observe))

    @_active_operation
    def acknowledge_feed_in_transaction(self,transaction: TransactionHandle,page: FeedPage) -> Outcome[FeedAcknowledged | FeedUnavailable]:
        """Assert durable downstream application; CAS the exact source interval.

        The caller must commit this transaction for a durable source checkpoint.
        This does not verify downstream durability or release retention.
        """
        from .feed import FeedPage,FeedCursor,FeedAcknowledged,FeedUnavailable
        if type(page) is not FeedPage or sha256(page.content).hexdigest()!=page.sha256:
            return Ok(FeedUnavailable(reason='integrity'))
        manifest,digest,_=_release()
        def acknowledge(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.acknowledge_feed(%s,%s,%s,%s,%s,%s)',(page.consumer_id,page.prior.content,page.next.content,page.sha256,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]))
            return FeedAcknowledged(outcome=value['outcome'],checkpoint=FeedCursor(content=base64.b64decode(value['checkpointBase64'],validate=True)))
        return self._feed_result(self._host._run_operation(transaction,acknowledge))

    @_active_operation
    def reader_catalog_in_transaction(self,transaction: TransactionHandle,*,maximum_count: int=65536,maximum_bytes: int=1048576) -> Outcome[ReaderCatalog | CatalogInvalid | CatalogRefused | CatalogUnavailable]:
        if type(maximum_count) is not int or not 1<=maximum_count<=65536 or type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:
            return Ok(CatalogInvalid(code='limits'))
        manifest,digest,_=_release()
        def read(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.reader_catalog(%s,%s,%s,%s)',(maximum_count,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            basis=json.loads(bytes(cursor.fetchone()[0]))
            return ReaderCatalog(catalog_revision=basis['catalogRevision'],layout_profile=basis['layoutProfile'],modules=tuple(basis['modules']))
        return self._reader_result(self._host._run_operation(transaction,read))

    @_active_operation
    def accepted_document_in_transaction(self,transaction: TransactionHandle,*,document_id: str,maximum_bytes: int=1048576) -> Outcome[AcceptedDocument | CatalogInvalid | CatalogRefused | CatalogUnavailable]:
        try: valid=type(document_id) is str and 1<=len(document_id.encode('utf8'))<=4096 and '\0' not in document_id
        except UnicodeError:valid=False
        if not valid:return Ok(CatalogInvalid(code='selection'))
        if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:return Ok(CatalogInvalid(code='limits'))
        manifest,digest,_=_release()
        def read(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.accepted_document(%s,%s,%s,%s)',(document_id,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            basis=json.loads(bytes(cursor.fetchone()[0]));content=base64.b64decode(basis['contentBase64'])
            if sha256(content).hexdigest()!=basis['sha256']:raise ValueError('Exact accepted document digest required')
            return AcceptedDocument(document_id=basis['documentId'],document_revision=basis['documentRevision'],artifact_identity=basis['artifactIdentity'],content=content,sha256=basis['sha256'],catalog_revision=basis['catalogRevision'],registration_id=basis['registrationId'],source_catalog_revision=basis['sourceCatalogRevision'])
        return self._reader_result(self._host._run_operation(transaction,read))

    @_active_operation
    def lookup_key_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,key_id: str,
                                  values: tuple[str | TextValue | BooleanValue,...],original_document: bytes | None=None,maximum_bytes: int=1048576,
                                  bun_executable: str='bun') -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        """Resolve an authored business key into complete values, native identity and version."""
        try:selection_valid=all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (document_id,module_id,record_id,key_id))
        except UnicodeError:selection_valid=False
        if not selection_valid:return Ok(ObjectReadInvalid(code='selection'))
        try:
            from ._group_runtime import _wire
            values_valid=type(values) is tuple and 1<=len(values)<=1024 and all(
                type(v) is str and '\0' not in v or type(v) is BooleanValue or
                type(v) is TextValue and v.kind in ('string','integer','decimal','binary') and '\0' not in v.text for v in values)
            encoded_values=json.dumps([{'kind':'string','text':v} if type(v) is str else _wire(v) for v in values],ensure_ascii=False,separators=(',',':')).encode('utf8') if values_valid else b''
        except (UnicodeError,TypeError):values_valid=False;encoded_values=b''
        if not values_valid:return Ok(ObjectReadInvalid(code='key_values'))
        if len(encoded_values)>1048576:return Ok(ObjectReadUnavailable(reason='resource'))
        if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:return Ok(ObjectReadInvalid(code='limits'))
        if original_document is not None and (type(original_document) is not bytes or not 1<=len(original_document)<=1048576):return Ok(ObjectReadInvalid(code='source'))
        manifest,digest,_=_release()
        def read(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.lookup_string_key(%s,%s,%s,%s,%s,%s,NULL,%s,%s,%s)',
                (document_id,module_id,record_id,key_id,original_document,encoded_values,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            return ObjectNotFound() if raw is None else _object_result(raw,manifest,digest)
        result=self._host._run_operation(transaction,read)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            if result.error.sql_state=='22023':return Ok(ObjectReadInvalid(code='source_or_key'))
            reason={'0A000':'profile','54000':'resource','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
        return result
