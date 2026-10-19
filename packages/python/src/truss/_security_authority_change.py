# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private participating authority mutation; no permission or ready-profile issuer.

Trusted direct installation administrator and independently qualified physical
mutation callback are premises. Native guard/claim/source parity and complete
participant coverage remain separate admission. Caller settles the transaction.
"""
from dataclasses import dataclass
from importlib.resources import files
import inspect
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor


@dataclass(frozen=True, slots=True)
class PendingAuthorityGeneration:
    installation_identity: bytes
    authored_profile: bytes
    generation: int
    status: str = 'pending_commit'
    security_ready: bool = False


def change_authority_in_transaction(host, transaction, *, installation_identity,
                                    authored_profile, expected_generation, action):
    if (type(host) is not PsycopgHost or type(installation_identity) is not bytes
            or not 1<=len(installation_identity)<=32768 or type(authored_profile) is not bytes
            or not 1<=len(authored_profile)<=32768 or type(expected_generation) is not int
            or not 1<=expected_generation<9223372036854775807 or not callable(action)
            or any(check(candidate) for candidate in (action,getattr(action,'__call__',None))
                   for check in (inspect.iscoroutinefunction,inspect.isasyncgenfunction,inspect.isgeneratorfunction))):
        return Error(ExecutionFailure('execution_obligation','Original bounded synchronous authority change required'))
    def change(cursor, observed):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False);original_path=cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        cursor.execute("SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')",prepare=False)
        if cursor.fetchone()!=('180006','read committed','off'):raise ValueError('Original supported read-write read-committed authority transaction required')
        cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation FOR SHARE',prepare=False)
        original=cursor.fetchmany(2)
        if len(original)!=1 or original[0][0].encode('utf8')!=installation_identity:
            raise ValueError('Original authority installation required')
        installation_administrator_with_cursor(cursor,original[0][1])
        cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE',prepare=False)
        if len(cursor.fetchmany(2))!=1:raise ValueError('Original authority head required')
        cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE',prepare=False)
        if cursor.fetchmany(2)!=[(installation_identity,authored_profile,expected_generation)]:
            raise ValueError('Original exclusive authority guard required')
        # Separate fresh statement after draining original guard-share holders.
        cursor.execute('SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled LIMIT 1',prepare=False)
        if cursor.fetchall():raise ValueError('Original publication operations remain unsettled')
        raw=files('truss').joinpath('_security_bootstrap','advance.sql').read_bytes()
        source=raw.decode('utf8')
        for i in range(1,4):source=source.replace('$'+str(i),'%(p'+str(i)+')s')
        result=action(cursor)
        if inspect.isgenerator(result) or inspect.iscoroutine(result):
            result.close();raise ValueError('Original authority action must complete synchronously')
        if result is not None:raise ValueError('Original authority action must complete or raise')
        cursor.execute(source,{'p1':installation_identity,'p2':authored_profile,'p3':expected_generation},prepare=False)
        if (cursor.description is None or tuple(c.name for c in cursor.description)!=('singleton','installation_identity_bytes_hex','policy_profile_bytes_hex','generation')
                or any(c.type_code!=25 for c in cursor.description) or cursor.statusmessage!='UPDATE 1'
                or cursor.fetchmany(2)!=[('1',installation_identity.hex(),authored_profile.hex(),str(expected_generation+1))]):
            raise ValueError('Exact original authority advance required')
        cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1',prepare=False)
        if cursor.fetchmany(2)!=[(installation_identity,authored_profile,expected_generation+1)]:
            raise ValueError('Original stored authority generation required')
        cursor.execute('SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled LIMIT 1',prepare=False)
        if cursor.fetchall():raise ValueError('Original publication exclusion changed during authority advance')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchone()!=(original_path,):raise ValueError('Original authority caller path restoration required')
        return PendingAuthorityGeneration(installation_identity,authored_profile,expected_generation+1)
    return host._run_operation(transaction,change)
