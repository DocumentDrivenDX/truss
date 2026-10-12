"""Public catalog runtime over caller-owned psycopg transactions.

This release registers one fresh scalar-string catalog, including authored keys
and relationships. Other capability families remain under implementation.
Ordinary-person catalog calls require READ COMMITTED, so authorization reads
observe committed membership changes. Higher isolation returns a refusal.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from uuid import uuid4
from threading import RLock
from functools import wraps
from .assembly_contracts import AssemblyDisposed
from .catalog_view import CatalogViewRequest, CatalogViewAvailable, CatalogViewUnavailable
from .object_read import ScalarObject, ObjectFound, ObjectNotFound, ObjectReadInvalid, ObjectReadUnavailable
from .execution import Ok, Error, ExecutionFailure, Outcome, TransactionHandle
from .psycopg_host import PsycopgHost
from .preparation import CatalogDocument, PreparedAcceptance, prepare_acceptance, _require_original_preparation
from ._catalog_support import evaluate_catalog_support, RELATIONAL_PROFILE
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
    for kind,dumper in ((str,StrBinaryDumper),(str,StrDumperUnknown),(bytes,BytesBinaryDumper),
                        (bytes,BytesDumper),(int,IntBinaryDumper),(int,IntDumper)):
        cursor.adapters.register_dumper(kind,dumper)


def _release():
    root=files('truss').joinpath('_catalog_runtime')
    original=root.joinpath('manifest.json').read_bytes()
    manifest=json.loads(original)
    sources=[]
    for name in ('layout.sql','lineage.sql','plan.sql','runtime.sql','barrier.sql','view.sql','read.sql'):
        raw=root.joinpath(name).read_bytes()
        if sha256(raw).hexdigest()!=manifest['files'][name]:raise ValueError('Catalog release source changed')
        sources.append(raw.decode('utf-8'))
    return manifest,sha256(original).hexdigest(),tuple(sources)


def _configuration():
    manifest,digest,_=_release()
    pin={'identity':manifest['releaseId'],'version':manifest.get('version','0.1'),'sha256':digest}
    umf_original=files('truss').joinpath('_umf','manifest.json').read_bytes()
    owner=json.loads(umf_original)['owner']
    return {'acceptanceProfile':pin,'layoutProfile':manifest['layoutProfile'],
        'policy':{'loss':'strict','profile':pin,'unknownEndpoint':'reject'},
        'supportProfile':RELATIONAL_PROFILE,'validatorProfile':{
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


class CatalogReferenceAssembly:
    """Actual installation/catalog provider. Settlement stays with the caller."""
    def __init__(self,configuration: CatalogRuntimeConfiguration,host: PsycopgHost) -> None:
        if type(configuration) is not CatalogRuntimeConfiguration or type(host) is not PsycopgHost:
            raise ValueError('Catalog configuration and adopted psycopg host required')
        if configuration.schema!='truss' or type(configuration.assembly_id) is not str or not 1<=len(configuration.assembly_id)<=256:
            raise ValueError('Supported catalog configuration required')
        self.configuration=configuration;self._host=host;self._disposed=False;self._lock=RLock()
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
            return prepare_acceptance(documents,canonical_numeric_free(_configuration()),bun_executable=bun_executable)
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
            cursor.execute('''INSERT INTO truss.catalog_runtime_installation
                SELECT true,pg_catalog.gen_random_uuid(),%s,%s,%s::pg_catalog.jsonb,%s::pg_catalog.jsonb,%s,%s,accepted_at
                FROM truss.schema_rev WHERE rev=0 RETURNING installation_id::pg_catalog.text''',
                (manifest['releaseId'],digest,json.dumps(manifest['layoutProfile']),json.dumps(_configuration()),privileges.owner_oid,privileges.client_oid),prepare=False)
            identity=cursor.fetchone()[0]
            for signature in ('catalog_accept(bytea,bytea,bytea,bytea,bytea,text)','catalog_report(int)','catalog_status()','catalog_view_basis(int,int,int)'):
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(roles.client)),prepare=False)
            cursor.execute("COMMENT ON SCHEMA truss IS 'Truss runtime 0.3: catalog and module-authorized scalar object reads; business writes unavailable'",prepare=False)
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()[0]!=original_path:raise ValueError('Caller search path restoration failed')
            return PendingCatalogInstallation(identity,roles.owner,roles.client,manifest['releaseId'])
        return self._host._run_operation(transaction,install)
    @_active_operation
    def status_in_transaction(self,transaction: TransactionHandle) -> Outcome[CatalogRuntimeStatus]:
        self._available()
        manifest,digest,_=_release()
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')",prepare=False)
            if not cursor.fetchone()[0]:return CatalogRuntimeStatus(False)
            cursor.execute('SELECT * FROM truss.catalog_status()',prepare=False)
            row=cursor.fetchone()
            if row is None or row[1:3]!=(manifest['releaseId'],digest) or json.loads(row[3])!=manifest['layoutProfile']:
                raise ValueError('Unsupported installed catalog release')
            return CatalogRuntimeStatus(True,row[0],int(row[4]),('catalog:fresh-registration','catalog:report','catalog:view','direct_read:scalar-object-id'))
        return self._host._run_operation(transaction,observe)
    @_active_operation
    def accept_in_transaction(self,transaction: TransactionHandle,prepared: PreparedAcceptance,*,request_key: str,origin_bytes: bytes=b'{}') -> Outcome[CatalogRegistration]:
        self._available()
        def produce(ordinal):
            _require_original_preparation(prepared)
            choices={key:value for key,value in prepared.input().items() if key not in ('interfaceVersion','documents')}
            if choices!=_configuration():raise ValueError('Exact selected catalog preparation required')
            if type(request_key) is not str or not 1<=len(request_key.encode())<=1024 or '\0' in request_key:raise ValueError('Stable request key required')
            from ._acceptance_json import decode_acceptance_json
            if type(origin_bytes) is not bytes or type(decode_acceptance_json(origin_bytes)) is not dict:raise ValueError('Original asserted origin object required')
            support=evaluate_catalog_support(prepared)
            semantic=compose_original_catalog_report_semantics(prepared,support)
            if semantic['state']!='source_fields_ready':raise ValueError('Complete original source inventory required')
            from ._owner_evidence_json import decode_owner_evidence_json
            evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
            source={'umf':semantic['umf'],'diagnostics':evidence['validation']['diagnostics'],
                'documentInterpretations':evidence['validation']['documentInterpretations'],
                'losses':evidence['ingress']['basis']['losses'],'extensions':semantic['extensions'],
                'transformRegistrations':evidence['ingress']['basis']['transformRegistrations'],
                'assertionEntries':semantic['assertionEntries']}
            _require_original_preparation(prepared)
            return (prepared.input_bytes,prepared.archive_documents_bytes,prepared.declarations_bytes,
                    canonical_numeric_free(source),origin_bytes,request_key)
        def execute(cursor,observed,ordinal,parameters):
            _pin_cursor(cursor)
            cursor.execute('SELECT * FROM truss.catalog_accept(%s,%s,%s,%s,%s,%s)',parameters,prepare=False)
            rows=cursor.fetchmany(2)
            if len(rows)!=1:raise ValueError('Complete catalog result required')
            revision,identity,report,replayed=rows[0]
            report=bytes(report);decoded=json.loads(report)
            if decoded['revision']!=revision or decoded['registrationId']!=identity or decoded['acceptedInput']!=prepared.input():
                raise ValueError('Original catalog result correspondence required')
            return CatalogRegistration(int(revision),identity,report,replayed)
        return self._host._run_semantic_operation(transaction,execute,parameter_producer=produce)
    @_active_operation
    def report_in_transaction(self,transaction: TransactionHandle,revision: int=1) -> Outcome[CatalogReport]:
        self._available()
        if type(revision) is not int or not 1<=revision<=2147483647:
            return Error(ExecutionFailure('execution_obligation','Valid catalog revision required'))
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.catalog_report(%s)',(revision,),prepare=False)
            raw=bytes(cursor.fetchone()[0])
            if json.loads(raw)['revision']!=str(revision):raise ValueError('Original report revision required')
            return CatalogReport(revision,raw)
        return self._host._run_operation(transaction,observe)

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
            if cursor.fetchone()!=(1,):raise ValueError('Accepted catalog head required')
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
                    cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.get_object(text,text,text,bigint,int,text,text) TO {}').format(sql.Identifier(role)),prepare=False)
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
            return Error(ExecutionFailure('execution_obligation','Typed catalog view request required'))
        manifest,digest,_=_release()
        layout=ProfilePin(**manifest['layoutProfile'])
        if request.layout_profile!=layout or request.view_profile!=VIEW_PROFILE:
            return Ok(CatalogViewUnavailable(reason='profile'))
        if type(request.scope) is not CompleteCatalogScope:return Ok(CatalogViewUnavailable(reason='closure'))
        selected=None
        if type(request.selection) is HistoricalCatalogSelection:
            if request.selection.catalog_revision!='1':return Ok(CatalogViewUnavailable(reason='context'))
            selected=1
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
            basis=json.loads(bytes(raw))
            if basis['releaseId']!=manifest['releaseId'] or basis['releaseSha256']!=digest:
                raise ValueError('Exact selected installed runtime required')
            return ObjectFound(object=ScalarObject(document_id=basis['documentId'],module_id=basis['moduleId'],
                record_id=basis['recordId'],id=int(basis['id']),type_id=int(basis['typeId']),version=int(basis['version']),
                catalog_revision=int(basis['catalogRevision']),record_revision=int(basis['recordRevision']),
                created_at=basis['createdAt'],updated_at=basis['updatedAt'],
                values=tuple(tuple(v) for v in basis['values']),retained=tuple(tuple(v) for v in basis['retained'])))
        result=self._host._run_operation(transaction,observe)
        if isinstance(result,Error) and result.error.code=='execution_obligation':
            reason={'0A000':'profile','54000':'resource','55P03':'observation'}.get(result.error.sql_state)
            if reason:return Ok(ObjectReadUnavailable(reason=reason))
        return result
