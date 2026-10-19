# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private original claim settlement; no completion authentication or release grant.

Only the trusted original coordinator after protected release completed or was
conclusively withheld may call this operation. That completion is a premise,
not proved by this adapter. Caller owns commit and unknown-ack reconciliation;
never automatically retry, delete or reuse the original operation token.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor

_SOURCES={'settle.sql': '3671425cba05dd5baf1d604f5a775d67fcdefaa1ce7d8e5e67e57d282118fd78'}

@dataclass(frozen=True, slots=True)
class PendingPublicationSettlement:
    operation_identity: bytes
    installation_identity: bytes
    authored_profile: bytes
    generation: int
    status: str = 'pending_commit'
    publication_allowed: bool = False


def settle_publication_in_transaction(host,transaction,*,operation_identity,
                                        installation_identity,authored_profile,expected_generation):
    if (type(host) is not PsycopgHost or type(operation_identity) is not bytes
            or not 1<=len(operation_identity)<=2048 or type(installation_identity) is not bytes
            or not 1<=len(installation_identity)<=32768 or type(authored_profile) is not bytes
            or not 1<=len(authored_profile)<=32768 or type(expected_generation) is not int
            or not 1<=expected_generation<=9223372036854775807):
        return Error(ExecutionFailure('execution_obligation','Original bounded publication settlement required'))
    def settle(cursor,observed):
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
        source=sources['settle.sql']
        for i in range(1,5):source=source.replace('$'+str(i),'%(p'+str(i)+')s')
        values={'p1':operation_identity,'p2':installation_identity,'p3':authored_profile,'p4':expected_generation}
        cursor.execute(source,values,prepare=False)
        if (cursor.description is None or tuple(c.name for c in cursor.description)!=('encode',)
                or any(c.type_code!=25 for c in cursor.description) or cursor.statusmessage!='UPDATE 1'
                or cursor.fetchmany(2)!=[(operation_identity.hex(),)]):raise ValueError('Exact original publication settlement required')
        cursor.execute('SELECT operation_identity_bytes,installation_identity_bytes,policy_profile_bytes,generation,settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(operation_identity,),prepare=False)
        if cursor.fetchmany(2)!=[(operation_identity,installation_identity,authored_profile,expected_generation,True)]:raise ValueError('Original stored settled publication required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchone()!=(original_path,):raise ValueError('Original publication caller path restoration required')
        return PendingPublicationSettlement(operation_identity,installation_identity,authored_profile,expected_generation)
    return host._run_operation(transaction,settle)
