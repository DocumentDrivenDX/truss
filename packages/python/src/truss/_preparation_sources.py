"""Original owner source compilation; private, never current authority."""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import as_file, files
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from ._preparation_compiler_replay import replay_preparation_program
from ._preparation_program import OriginalPreparationProgram
from ._preparation_sources_release import MANIFEST_SHA256
from .weft import _decode

_FIELDS = {'configuration':'configuration','request':'request','compileResponse':'compile_response',
           'bindingEnvelope':'binding_artifact','loweringInvocation':'lowering'}


@dataclass(frozen=True, slots=True)
class OriginalPreparationSources:
    packet: bytes
    producer_identity: bytes
    authority: bool = False


def compile_preparation_sources(program, source_inputs, *, native_module_path, bun_executable='bun'):
    """Invoke both original producers; never accept a caller's compiled packet.

    Authored source authorization is the excluded installer's responsibility.
    Trusted engine executable/source and immutable installation custody apply.
    The result is byte custody, not native admission or an authenticated token.
    """
    if type(program) is not OriginalPreparationProgram or type(source_inputs) is not bytes:
        raise ValueError('Original program and authored source bytes required')
    original = _decode(source_inputs, 67108864, 'preparation_sources')[1]
    if type(original) is not dict:
        raise ValueError('Original authored sources required')
    for field, name in _FIELDS.items():
        value = original.get(field)
        if (type(value) is not dict or set(value) != {'mediaType','utf8','sha256'}
                or value['mediaType'] != 'application/json' or type(value['utf8']) is not str
                or value['utf8'].encode('utf8') != getattr(program,name)
                or value['sha256'] != sha256(getattr(program,name)).hexdigest()):
            raise ValueError('Exact original enrolled artifact bytes required: '+field)
    replay = replay_preparation_program(program, native_module_path=native_module_path)
    root = files('truss').joinpath('_preparation_sources')
    raw = root.joinpath('manifest.json').read_bytes()
    if sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('Original owner source compiler manifest required')
    manifest = _decode(raw, 65536, 'preparation_source_manifest')[1]
    for path, digest in manifest['files'].items():
        if sha256(root.joinpath(path).read_bytes()).hexdigest() != digest:
            raise ValueError('Original owner source compiler bytes required')
    executable = shutil.which(bun_executable)
    if executable is None:
        raise ValueError('Bun source compiler runtime required')
    with as_file(root.joinpath('producer.js')) as producer, tempfile.TemporaryDirectory(prefix='truss-preparation-sources-') as directory:
        source = Path(directory)/'input.json';source.write_bytes(source_inputs);source.chmod(0o600)
        try:
            result = subprocess.run([executable, str(producer), str(source)], capture_output=True, timeout=30, check=True)
        except (subprocess.SubprocessError, OSError) as error:
            raise ValueError('Original owner source compiler refused') from error
    packet = _decode(result.stdout, 67108864, 'preparation_source_packet')[1]
    if (packet.get('protocol') != 'truss.preparation-source-obligations/0.1-candidate'
            or packet.get('authority') is not False or packet.get('complete') is not False
            or packet.get('original') != original):
        raise ValueError('Original non-authoritative owner packet required')
    identity = json.dumps({'umfSource':manifest['revision'],'manifestSha256':MANIFEST_SHA256,
        'bundleSha256':manifest['files']['producer.js'],'weftSource':replay.source_commit,
        'weftNativeSha256':replay.native_sha256,'originalProgramSha256':replay.original_packet_sha256},
        separators=(',',':')).encode('utf8')
    return OriginalPreparationSources(result.stdout, identity)


@dataclass(frozen=True, slots=True)
class PendingPreparationSources:
    program_id: int
    status: str = 'pending_commit'
    authority: bool = False


def register_preparation_sources_in_transaction(host, transaction, *, program_id,
        program, source_inputs, native_module_path, bun_executable='bun'):
    """Excluded issuer authenticates authored sources; caller owns commit.

    Both actual producers run here. Caller-serialized packets/replay receipts
    cannot replace invocation. This immutable association must commit before D.
    """
    from psycopg import sql
    from .psycopg_host import PsycopgHost
    from .execution import Error, ExecutionFailure
    from ._preparation_source_epoch import _context, _restore
    from ._preparation_program import _verify_home
    if type(host) is not PsycopgHost or type(program_id) is not int or not 1 <= program_id <= 9223372036854775807:
        return Error(ExecutionFailure('execution_obligation', 'Original program identifier required'))
    try:
        compiled = compile_preparation_sources(program, source_inputs,
            native_module_path=native_module_path, bun_executable=bun_executable)
    except (ValueError, TypeError, KeyError, OSError):
        return Error(ExecutionFailure('execution_obligation', 'Original preparation sources and actual producer correspondence required'))
    def register(cursor, observed):
        path, installation, owner, actor = _context(cursor)
        cursor.execute('LOCK TABLE ONLY truss.preparation_program_registration IN SHARE MODE NOWAIT', prepare=False)
        _verify_home(cursor, owner)
        cursor.execute('SELECT p.original_configuration,p.original_request,p.original_plan_artifact,p.original_binding_artifact,p.original_lowering FROM ONLY truss.preparation_program_registration p JOIN ONLY truss.action_store_registration s ON s.control_id=p.store_control_id WHERE p.program_id=%s AND p.compiler_source_pin=%s AND s.installation_id=%s::uuid AND p.store_receipt_bytes=s.initial_receipt_bytes FOR SHARE OF p NOWAIT', (program_id,program.compiler_source_pin,installation), prepare=False)
        expected = tuple(getattr(program, name) for name in _FIELDS.values())
        if cursor.fetchmany(2) != [expected]:
            raise ValueError('Exact original enrolled program correspondence required')
        cursor.execute("SELECT pg_catalog.to_regclass('truss.preparation_program_sources')", prepare=False)
        if cursor.fetchone() == (None,):
            raw = files('truss').joinpath('_security_bootstrap','preparation-program-sources-storage.sql').read_bytes()
            if sha256(raw).hexdigest() != _STORAGE_SHA256:
                raise ValueError('Original UMF source attachment storage required')
            cursor.execute(raw.decode('utf8'), prepare=False)
            cursor.execute('SELECT rolname FROM pg_catalog.pg_roles WHERE oid=%s::oid', (owner,), prepare=False)
            cursor.execute(sql.SQL('ALTER TABLE truss.preparation_program_sources OWNER TO {}').format(sql.Identifier(cursor.fetchone()[0])), prepare=False)
        cursor.execute('LOCK TABLE ONLY truss.preparation_program_sources IN SHARE ROW EXCLUSIVE MODE NOWAIT', prepare=False)
        cursor.execute("SELECT relowner,relkind,relpersistence,relrowsecurity,relforcerowsecurity FROM pg_catalog.pg_class WHERE oid='truss.preparation_program_sources'::regclass", prepare=False)
        if cursor.fetchmany(2) != [(owner,'r','p',False,False)]:
            raise ValueError('Original private source attachment home required')
        cursor.execute("SELECT a.grantee,a.grantor,a.is_grantable FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE c.oid='truss.preparation_program_sources'::regclass", prepare=False)
        acl = cursor.fetchmany(32)
        if not acl or any(row != (owner,owner,False) for row in acl):
            raise ValueError('Owner-only source attachment home required')
        cursor.execute("SELECT tgname,tgfoid::regprocedure::text,tgenabled,tgtype FROM pg_catalog.pg_trigger WHERE tgrelid='truss.preparation_program_sources'::regclass AND NOT tgisinternal", prepare=False)
        if cursor.fetchmany(2) != [('preparation_program_sources_immutable','truss.catalog_immutable()','A',58)]:
            raise ValueError('Original immutable source attachment required')
        cursor.execute('SELECT original_source_packet,producer_identity FROM ONLY truss.preparation_program_sources WHERE program_id=%s FOR SHARE NOWAIT', (program_id,), prepare=False)
        rows = cursor.fetchmany(2)
        if rows:
            if rows != [(compiled.packet,compiled.producer_identity)]:
                raise ValueError('Changed sources require a new original program')
        else:
            cursor.execute('INSERT INTO truss.preparation_program_sources VALUES(%s,%s,%s,pg_catalog.pg_current_xact_id(),%s::oid,pg_catalog.clock_timestamp())',
                (program_id,compiled.packet,compiled.producer_identity,int(actor)), prepare=False)
        _restore(cursor,path)
        return PendingPreparationSources(program_id)
    return host._run_operation(transaction,register)

_STORAGE_SHA256 = '177fc590f1bea4b967d0a0f21e7a492a70d2600f544e1407549c3ad4f94a4ad5'
