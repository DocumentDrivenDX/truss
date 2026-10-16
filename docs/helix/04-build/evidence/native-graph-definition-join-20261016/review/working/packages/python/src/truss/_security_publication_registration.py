"""Private original durable claim registration; no release or issuer authority.

Trusted direct installation administrator/coordinator is a premise. Original
operation identity is independently supplied, not authenticated here. Caller
settles its transaction and owns unknown-commit recovery; never retry a token.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor

_SOURCES={'register.sql': '55ad786b5b4e43a8b477dc1749fee3f92b94f7a48867c1c83b1b5e41c040fa73', 'capacity-lock.sql': '6c7d76e24b8f4cb83815c4ab25e94f069c147acae136eb16c4ce87307862e349'}

@dataclass(frozen=True, slots=True)
class PendingPublicationRegistration:
    operation_identity: bytes
    installation_identity: bytes
    authored_profile: bytes
    generation: int
    status: str = 'pending_commit'
    publication_allowed: bool = False


def register_publication_in_transaction(host,transaction,*,operation_identity,
                                        installation_identity,authored_profile,expected_generation):
    if (type(host) is not PsycopgHost or type(operation_identity) is not bytes
            or not 1<=len(operation_identity)<=2048 or type(installation_identity) is not bytes
            or not 1<=len(installation_identity)<=32768 or type(authored_profile) is not bytes
            or not 1<=len(authored_profile)<=32768 or type(expected_generation) is not int
            or not 1<=expected_generation<=9223372036854775807):
        return Error(ExecutionFailure('execution_obligation','Original bounded publication registration required'))
    def register(cursor,observed):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False);original_path=cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        cursor.execute("SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')",prepare=False)
        if cursor.fetchone()!=('180006','read committed','off'):raise ValueError('Original supported publication transaction required')
        cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation FOR SHARE',prepare=False)
        original=cursor.fetchmany(2)
        if len(original)!=1 or original[0][0].encode('utf8')!=installation_identity:raise ValueError('Original publication installation required')
        installation_administrator_with_cursor(cursor,original[0][1])
        cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE',prepare=False)
        if len(cursor.fetchmany(2))!=1:raise ValueError('Original publication head required')
        cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1 FOR SHARE',prepare=False)
        if cursor.fetchmany(2)!=[(installation_identity,authored_profile,expected_generation)]:raise ValueError('Original publication guard required')
        sources={}
        for name,digest in _SOURCES.items():
            raw=files('truss').joinpath('_security_bootstrap',name).read_bytes()
            if sha256(raw).hexdigest()!=digest:raise ValueError('Original publication source required')
            sources[name]=raw.decode('utf8')
        cursor.execute(sources['capacity-lock.sql'],prepare=False)
        source=sources['register.sql']
        for i in range(1,5):source=source.replace('$'+str(i),'%(p'+str(i)+')s')
        values={'p1':operation_identity,'p2':installation_identity,'p3':authored_profile,'p4':expected_generation}
        cursor.execute(source,values,prepare=False)
        if (cursor.description is None or tuple(c.name for c in cursor.description)!=('encode',)
                or any(c.type_code!=25 for c in cursor.description) or cursor.statusmessage!='INSERT 0 1'
                or cursor.fetchmany(2)!=[(operation_identity.hex(),)]):raise ValueError('Exact original publication insertion required')
        cursor.execute('SELECT operation_identity_bytes,installation_identity_bytes,policy_profile_bytes,generation,settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(operation_identity,),prepare=False)
        if cursor.fetchmany(2)!=[(operation_identity,installation_identity,authored_profile,expected_generation,False)]:raise ValueError('Original stored unsettled publication required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchone()!=(original_path,):raise ValueError('Original publication caller path restoration required')
        return PendingPublicationRegistration(operation_identity,installation_identity,authored_profile,expected_generation)
    return host._run_operation(transaction,register)
