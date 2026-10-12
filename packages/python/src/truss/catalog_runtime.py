"""Public catalog runtime over caller-owned psycopg transactions.

This release registers one fresh scalar-string catalog, including authored keys
and relationships. Other capability families remain under implementation.
Ordinary-person catalog calls require READ COMMITTED, so authorization reads
observe committed membership changes. Higher isolation returns a refusal.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from hashlib import sha256
from importlib.resources import files
import json
import base64
from uuid import uuid4
from threading import RLock
from functools import wraps
from typing import Literal
from .reader_catalog import ReaderCatalog, AcceptedDocument, CatalogRefused, CatalogInvalid, CatalogUnavailable
from .assembly_contracts import AssemblyDisposed, CapabilityUnavailable
from .catalog_view import CatalogViewRequest, CatalogViewAvailable, CatalogViewUnavailable, CatalogDefinitionReference
from .imports import ImportInput,ImportExecutionResult,ObjectImportRecord
from .import_runtime import ImportRuntimeContext
from .groups import AuthoredValue
from .contracts import MapValue
from .receipt_visibility import ReceiptIncluded,ReceiptVisibilityUnavailable
from .edge_read import ScalarEdge,EdgeFound,EdgeNotFound,EdgePage,EdgePageCursor
from .object_read import ScalarObject, ObjectFound, ObjectNotFound, ObjectReadInvalid, ObjectReadUnavailable, ObjectPage, ObjectPageCursor
from ._group_runtime import GroupRuntimeContext, NativeGroupCapability, GroupCapabilityAvailable
from .contracts import CapabilitySelection, TypedIdentity
from .groups import GroupSemanticInput, GroupRequestSelection, GroupApplicationResult
from .execution import Ok, Error, ExecutionFailure, Outcome, TransactionHandle
from .psycopg_host import PsycopgHost
from .preparation import CatalogDocument, PreparedAcceptance, prepare_acceptance, _require_original_preparation
from ._catalog_support import evaluate_catalog_support, SCALAR_PROFILE
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
class CatalogRuntimeStatus:
    installed: bool
    installation_id: str | None = None
    revision: int | None = None
    capabilities: tuple[str,...] = ()

@dataclass(frozen=True,slots=True)
class CatalogRegistration:
    revision: int
    registration_id: str
    report_bytes: bytes
    replayed: bool
    status: str = 'pending_commit'

@dataclass(frozen=True,slots=True)
class CatalogUnchanged:
    revision: int
    registration_id: str
    report_bytes: bytes
    replayed: bool
    request_key: str
    asserted_origin_bytes: bytes
    actor: str
    outcome: str = 'unchanged'
    status: str = 'pending_commit'

@dataclass(frozen=True,slots=True)
class CatalogCompatibilityViolation:
    document_id: str
    module_id: str
    record_id: str
    field_module_id: str
    field_id: str
    rule: Literal['property.required','property.scalar_type']
    affected_object_count: int

@dataclass(frozen=True,slots=True)
class CatalogAcceptanceRefused:
    revision: int
    violations: tuple[CatalogCompatibilityViolation,...]
    outcome: Literal['refused'] = 'refused'
    code: Literal['incompatible'] = 'incompatible'

@dataclass(frozen=True,slots=True)
class CatalogReport:
    revision: int
    original_bytes: bytes


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
    for name in ('layout.sql','lineage.sql','plan.sql','runtime.sql','barrier.sql','view.sql','scalars.sql','read.sql','keys.sql','groups.sql','reader.sql','key-read.sql','pages.sql','evolution.sql','operations.sql','preconditions.sql','imports.sql'):
        raw=root.joinpath(name).read_bytes()
        if sha256(raw).hexdigest()!=manifest['files'][name]:raise ValueError('Catalog release source changed')
        sources.append(raw.decode('utf-8'))
    profiles=root.joinpath('group-profiles.json').read_bytes()
    if sha256(profiles).hexdigest()!=manifest['files']['group-profiles.json']:raise ValueError('Selected group profiles required')
    for entry in json.loads(profiles)['profiles']:
        if sha256(entry['definition'].encode('utf8')).hexdigest()!=entry['pin']['sha256']:raise ValueError('Original profile definition required')
    return manifest,sha256(original).hexdigest(),tuple(sources)


def _configuration():
    manifest,digest,_=_release()
    pin={'identity':manifest['releaseId'],'version':manifest.get('version','0.1'),'sha256':digest}
    umf_original=files('truss').joinpath('_umf','manifest.json').read_bytes()
    owner=json.loads(umf_original)['owner']
    return {'acceptanceProfile':pin,'layoutProfile':manifest['layoutProfile'],
        'policy':{'loss':'strict','profile':pin,'unknownEndpoint':'reject'},
        'supportProfile':SCALAR_PROFILE,'validatorProfile':{
            'identity':'truss-packaged-umf-preparation','version':owner['revision'],'sha256':sha256(umf_original).hexdigest()},
        'binding':{'state':'absent'},'transforms':[]}


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
    if basis['releaseId']!=manifest['releaseId'] or basis['releaseSha256']!=digest:
        raise ValueError('Exact selected installed runtime required')
    def logical(value):
        if type(value) is dict:
            from .contracts import TextValue
            return TextValue(kind=value['kind'],text=value['text'])
        return value
    return ObjectFound(object=ScalarObject(document_id=basis['documentId'],module_id=basis['moduleId'],
        record_id=basis['recordId'],id=int(basis['id']),type_id=int(basis['typeId']),version=int(basis['version']),
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


class CatalogReferenceAssembly:
    """Actual installation/catalog provider. Settlement stays with the caller."""
    def __init__(self,configuration: CatalogRuntimeConfiguration,host: PsycopgHost) -> None:
        if type(configuration) is not CatalogRuntimeConfiguration or type(host) is not PsycopgHost:
            raise ValueError('Catalog configuration and adopted psycopg host required')
        if configuration.schema!='truss' or type(configuration.assembly_id) is not str or not 1<=len(configuration.assembly_id)<=256:
            raise ValueError('Supported catalog configuration required')
        self.configuration=configuration;self._host=host;self._disposed=False;self._lock=RLock();self._group_documents=()
    def catalog(self) -> CatalogReferenceAssembly:return self
    def dispose(self) -> AssemblyDisposed:
        with self._lock:
            self._disposed=True
            return AssemblyDisposed()
    def _available(self):
        if self._disposed:raise ValueError('Assembly disposed')
    def prepare_catalog(self,documents: tuple[CatalogDocument,...],*,bun_executable: str='bun') -> PreparedAcceptance:
        with self._lock:
            self._available()
            prepared=prepare_acceptance(documents,canonical_numeric_free(_configuration()),bun_executable=bun_executable)
            return prepared
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
            for signature in ('catalog_accept(bytea,bytea,bytea,bytea,bytea,text)','catalog_report(int)','catalog_status()','catalog_view_basis(int,int,int)'):
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(roles.client)),prepare=False)
            cursor.execute("COMMENT ON SCHEMA truss IS 'Truss runtime 0.16 candidate: catalog, scalar objects and independent directed relationships; feed unavailable'",prepare=False)
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
            return PendingCatalogInstallation(identity,roles.owner,roles.client,manifest['releaseId'])
        return self._host._run_operation(transaction,install)
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
            return CatalogRuntimeStatus(True,row[0],int(row[4]),('catalog:fresh-registration','catalog:report','catalog:view','direct_read:scalar-object-id','group:rootless-scalar-graph','direct_read:edge-id','direct_read:relationship-page','receipt:authority-visibility'))
        return _catalog_failure(self._host._run_operation(transaction,observe),local_failure[0])
    @_active_operation
    def accept_in_transaction(self,transaction: TransactionHandle,prepared: PreparedAcceptance,*,request_key: str,origin_bytes: bytes=b'{}') -> Outcome[CatalogRegistration | CatalogUnchanged | CatalogAcceptanceRefused]:
        self._available()
        local_failure=[None]
        def reject(code,message):
            local_failure[0]=code
            raise ValueError(message)
        def require_original():
            try:_require_original_preparation(prepared)
            except ValueError:reject('invalid_input','Original unchanged preparation required')
        def produce(ordinal):
            require_original()
            choices={key:value for key,value in prepared.input().items() if key not in ('interfaceVersion','documents')}
            if choices!=_configuration():reject('unsupported_profile','Exact selected catalog preparation required')
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
            require_original()
            return (prepared.input_bytes,prepared.archive_documents_bytes,prepared.declarations_bytes,
                    canonical_numeric_free(source),origin_bytes,request_key)
        def execute(cursor,observed,ordinal,parameters):
            _pin_cursor(cursor)
            cursor.execute('SELECT * FROM truss.catalog_accept(%s,%s,%s,%s,%s,%s)',parameters,prepare=False)
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
                    if set(entry)!={'documentId','moduleId','recordId','fieldModuleId','fieldId','rule','affectedObjectCount'} or entry['rule'] not in ('property.required','property.scalar_type'):
                        raise ValueError('Qualified compatibility violation required')
                    count=entry['affectedObjectCount']
                    if type(count) is not str or not count.isascii() or not count.isdecimal() or count.startswith('0') or len(count)>19:
                        raise ValueError('Positive exact affected-object count required')
                    parsed.append(CatalogCompatibilityViolation(entry['documentId'],entry['moduleId'],entry['recordId'],entry['fieldModuleId'],entry['fieldId'],entry['rule'],int(count)))
                return CatalogAcceptanceRefused(int(revision),tuple(parsed))
            report=bytes(report);decoded=json.loads(report)
            if decoded['revision']!=revision or decoded['registrationId']!=identity or decoded['acceptedInput']!=prepared.input():
                raise ValueError('Original catalog result correspondence required')
            if unchanged:return CatalogUnchanged(int(revision),identity,report,replayed,request_key,origin_bytes,actor)
            return CatalogRegistration(int(revision),identity,report,replayed)
        result=_catalog_failure(self._host._run_semantic_operation(transaction,execute,parameter_producer=produce),local_failure[0])
        if isinstance(result,Ok) and not isinstance(result.value,CatalogAcceptanceRefused):
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
            cursor.execute("SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=session_user",prepare=False)
            if cursor.fetchone()!=(True,):raise ValueError('Trusted installation administrator required')
            cursor.execute('SELECT release_id,release_sha256 FROM truss.catalog_runtime_installation',prepare=False)
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
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.get_object(text,text,text,bigint,int,text,text),truss.get_edge(text,text,text,bigint,int,text,text),truss.reached(bytea,int,text,text),truss.import_context(text,text),truss.import_key_selection(text,text,text,text,text),truss.import_identity_key_selection(bytea,text,text),truss.import_object_identity(bytea,bytea,bytea,text,text),truss.import_edge_identity(bytea,text,text),truss.import_record_source(uuid,bytea,text),truss.import_report_record_authority(bytea,text,text,text),truss.page_edges(text,text,text,jsonb,text,int,int,bytea,text,text) TO {}').format(sql.Identifier(role)),prepare=False)
            for grant in grants:
                for role in (grant.reader_role,grant.writer_role):
                    for signature in ('reader_catalog(int,int,text,text)','accepted_document(text,int,text,text)',
                                      'key_read_selection(text,text,text,text,bytea,text,text)',
                                      'lookup_string_key(text,text,text,text,bytea,bytea,bytea,int,text,text)',
                                      'page_objects(text,text,text,int,int,bytea,text,text)'):
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
                if len(matching)!=1 or type(matching[0]) is not TextValue or matching[0].kind!='string':raise ValueError('Complete exact string primary-key values required')
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
                               maximum_evidence_bytes: int=1048576) -> Outcome[ReceiptIncluded | ReceiptVisibilityUnavailable]:
        """Resolve committed Truss effects in this authority read-only transaction; never wait."""
        from ._receipt_position import decode_receipt_position
        from .contracts import ProfilePin
        if type(maximum_token_bytes) is not int or not 1<=maximum_token_bytes<=16384 or type(maximum_evidence_bytes) is not int or not 1<=maximum_evidence_bytes<=16777216:
            return Ok(ReceiptVisibilityUnavailable(reason='resource'))
        if type(token) is not str:return Ok(ReceiptVisibilityUnavailable(reason='invalid_token'))
        if len(token)>maximum_token_bytes:return Ok(ReceiptVisibilityUnavailable(reason='resource'))
        try:locator=decode_receipt_position(token)
        except (ValueError,UnicodeError):return Ok(ReceiptVisibilityUnavailable(reason='invalid_token'))
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.reached(%s,%s,%s,%s)',(locator.original_bytes,maximum_evidence_bytes,manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]))
            if value['outcome']=='unavailable':return ReceiptVisibilityUnavailable(reason=value['reason'])
            return ReceiptIncluded(included=value['included'],comparison_profile=ProfilePin(**value['comparisonProfile']))
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'42501':'authorization','0A000':'epoch_profile','54000':'resource','55P03':'observation_integrity'}.get(result.error.sql_state)
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
                                  values: tuple[str,...],original_document: bytes | None=None,maximum_bytes: int=1048576,
                                  bun_executable: str='bun') -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        """Resolve an authored business key into complete values, native identity and version."""
        try:selection_valid=all(type(v) is str and 1<=len(v.encode('utf8'))<=4096 and '\0' not in v for v in (document_id,module_id,record_id,key_id))
        except UnicodeError:selection_valid=False
        if not selection_valid:return Ok(ObjectReadInvalid(code='selection'))
        try:
            values_valid=type(values) is tuple and 1<=len(values)<=1024 and all(type(v) is str and '\0' not in v for v in values)
            encoded_values=json.dumps(values,ensure_ascii=False,separators=(',',':')).encode('utf8') if values_valid else b''
        except (UnicodeError,TypeError):values_valid=False;encoded_values=b''
        if not values_valid:return Ok(ObjectReadInvalid(code='key_values'))
        if len(encoded_values)>1048576:return Ok(ObjectReadUnavailable(reason='resource'))
        if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16777216:return Ok(ObjectReadInvalid(code='limits'))
        if original_document is not None and (type(original_document) is not bytes or not 1<=len(original_document)<=1048576):return Ok(ObjectReadInvalid(code='source'))
        manifest,digest,_=_release()
        def read(cursor,observed):
            from ._umf_key_tuples import encode_string_key_tuples,KeyTupleRequest
            _pin_cursor(cursor);source=original_document
            if source is None:
                cursor.execute('SELECT truss.accepted_document(%s,%s,%s,%s)',(document_id,16777216,manifest['releaseId'],digest),prepare=False)
                archive=json.loads(bytes(cursor.fetchone()[0]));source=base64.b64decode(archive['contentBase64'])
                if sha256(source).hexdigest()!=archive['sha256']:raise ValueError('Exact accepted source required')
            cursor.execute('SELECT truss.key_read_selection(%s,%s,%s,%s,%s,%s,%s)',
                (document_id,module_id,record_id,key_id,source,manifest['releaseId'],digest),prepare=False)
            selection=cursor.fetchone()[0]
            if selection is None:return ObjectNotFound()
            if json.loads(bytes(selection))['componentCount']!=len(values):return ObjectReadInvalid(code='key_values')
            try:encoded=encode_string_key_tuples(source,(KeyTupleRequest(module_id,record_id,key_id,values),),bun_executable=bun_executable)[0]
            except (ValueError,FileNotFoundError):return ObjectReadUnavailable(reason='profile')
            cursor.execute('SELECT truss.lookup_string_key(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (document_id,module_id,record_id,key_id,source,encoded_values,encoded.tuple_bytes,maximum_bytes,manifest['releaseId'],digest),prepare=False)
            raw=cursor.fetchone()[0]
            return ObjectNotFound() if raw is None else _object_result(raw,manifest,digest)
        result=self._host._run_operation(transaction,read)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            if result.error.sql_state=='22023':return Ok(ObjectReadInvalid(code='source_or_key'))
            reason={'0A000':'profile','54000':'resource','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
        return result
