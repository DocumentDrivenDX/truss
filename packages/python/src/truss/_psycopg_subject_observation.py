"""Private ordinary caller/TEXT observation; not subject issuance or authority."""
from dataclasses import dataclass
from hashlib import sha256
import inspect
import json
from ._owner_evidence_json import decode_owner_evidence_json
from .psycopg_host import PsycopgHost


@dataclass(frozen=True,slots=True)
class _SubjectSelection:
    original_request: bytes
    original_document: bytes
    module: str
    record: str
    key: str
    principal: str
    schema: str
    routine: str
    columns: tuple[str,...]
    actor_carrier: str = 'text'


@dataclass(frozen=True,slots=True)
class _SubjectObservation:
    principal: str
    document_sha256: str
    identity: tuple[str,str,str]
    columns: tuple[str,...]
    values: tuple[str,...]
    utf8_hex: tuple[str,...]
    original_inspection: bytes


def _observe_ordinary_subject(host, transaction, selection, original_inspector):
    """Reacquire original host custody; output is immutable historical evidence."""
    if type(host) is not PsycopgHost or type(selection) is not _SubjectSelection:
        raise ValueError('Original host and immutable selection required')
    if (type(selection.original_request) is not bytes or not 1<=len(selection.original_request)<=4_000_000
            or type(selection.original_document) is not bytes or not 1<=len(selection.original_document)<=1048576):
        raise ValueError('Bounded original sources required')
    request=selection.original_request.decode('utf8',errors='strict')
    selection.original_document.decode('utf8',errors='strict')
    for value,maximum in [(selection.module,4096),(selection.record,4096),(selection.key,4096),
                          (selection.principal,63),(selection.schema,63),(selection.routine,63)]:
        if type(value) is not str or not 1<=len(value.encode('utf8'))<=maximum or '\0' in value:
            raise ValueError('Exact bounded identities required')
    if (type(selection.columns) is not tuple or not 1<=len(selection.columns)<=32
            or any(type(c) is not str or not 1<=len(c.encode('utf8'))<=63 or '\0' in c for c in selection.columns)
            or len(set(selection.columns))!=len(selection.columns) or type(selection.actor_carrier) is not str or selection.actor_carrier not in ('name','text')):
        raise ValueError('Ordered native subject mapping required')
    if (not callable(original_inspector) or any(check(candidate)
            for candidate in (original_inspector,getattr(original_inspector,'__call__',None))
            for check in (inspect.iscoroutinefunction,inspect.isgeneratorfunction,inspect.isasyncgenfunction))):
        raise ValueError('Original synchronous inspector required')
    digest=sha256(selection.original_document).hexdigest()
    probe=json.dumps({'sourceSha256':digest,'identity':{'module':selection.module,'element':selection.record,'key':selection.key}})
    raw=original_inspector(request,probe)
    if inspect.iscoroutine(raw) or inspect.isgenerator(raw):
        raw.close();raise ValueError('Deferred original inspection refused')
    if type(raw) is not str or not 1<=len(raw.encode('utf8'))<=65536:
        raise ValueError('Original bounded inspection response required')
    original=raw.encode('utf8');response=decode_owner_evidence_json(original)
    if (type(response) is not dict or set(response)!={'interfaceVersion','status','securityReady'}
            or response['interfaceVersion']!='weft-security-subject-selection/0.1.0'
            or response['status']!='inspected' or response['securityReady'] is not False):
        raise ValueError('Original non-ready subject inspection required')
    def observe(cursor,observed):
        from psycopg import sql
        if observed[0][2:] not in (('repeatable_read','read_only'),('serializable','read_only')):
            raise ValueError('Stable native read-only transaction required')
        def principal():
            cursor.execute("SELECT SESSION_USER::pg_catalog.text,CURRENT_USER::pg_catalog.text,"
                           "r.rolsuper::pg_catalog.text,r.rolbypassrls::pg_catalog.text,"
                           "pg_catalog.current_setting('client_encoding')::pg_catalog.text "
                           "FROM pg_catalog.pg_roles r WHERE r.rolname OPERATOR(pg_catalog.=) SESSION_USER",prepare=False,binary=False)
            if (cursor.description is None or len(cursor.description)!=5 or any(d.type_code!=25 for d in cursor.description)
                    or cursor.fetchmany(2)!=[(selection.principal,selection.principal,'false','false','UTF8')]):
                raise ValueError('Pinned original ordinary caller required')
        principal()
        statement=sql.SQL('SELECT * FROM {}(SESSION_USER::pg_catalog.{})').format(
            sql.Identifier(selection.schema,selection.routine),sql.SQL(selection.actor_carrier))
        cursor.execute(statement,prepare=False,binary=False)
        # Refuse foreign OIDs before fetch can invoke caller-installed loaders.
        if (cursor.description is None or tuple(d.name for d in cursor.description)!=selection.columns
                or any(d.type_code!=25 for d in cursor.description)):
            raise ValueError('Exact original native TEXT descriptors required')
        rows=cursor.fetchmany(2)
        if (len(rows)!=1 or len(rows[0])!=len(selection.columns) or any(type(v) is not str for v in rows[0])):
            raise ValueError('Exact original native TEXT subject tuple required')
        values=tuple(rows[0]);encoded=tuple(v.encode('utf8',errors='strict') for v in values)
        if any(len(v)>65536 for v in encoded) or sum(map(len,encoded))>1048576:
            raise ValueError('Native subject tuple budget exceeded')
        principal()
        return _SubjectObservation(selection.principal,digest,(selection.module,selection.record,selection.key),
                                   selection.columns,values,tuple(v.hex() for v in encoded),original)
    return host._run_operation(transaction,observe)
