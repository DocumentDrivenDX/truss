"""Private prelocked trigger-coordinated data mutation; no permission/profile issuer.

Trusted direct installation administrator and independently qualified physical
mutation callback are premises. Trigger installation/lifetime, exact declared
event count, native source parity and complete participant coverage remain
separate admission. No count proves which individual effects participated. Caller settles the transaction.
"""
from dataclasses import dataclass
import inspect
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor


@dataclass(frozen=True, slots=True)
class PendingDataWriterGeneration:
    installation_identity: bytes
    authored_profile: bytes
    generation: int
    status: str = 'pending_commit'
    security_ready: bool = False


def write_data_in_transaction(host, transaction, *, installation_identity,
                              authored_profile, expected_generation, expected_event_count, action):
    if (type(host) is not PsycopgHost or type(installation_identity) is not bytes
            or not 1<=len(installation_identity)<=32768 or type(authored_profile) is not bytes
            or not 1<=len(authored_profile)<=32768 or type(expected_generation) is not int
            or not 1<=expected_generation<9223372036854775807
            or type(expected_event_count) is not int
            or not 1<=expected_event_count<=9223372036854775807-expected_generation
            or not callable(action)
            or any(check(candidate) for candidate in (action,getattr(action,'__call__',None))
                   for check in (inspect.iscoroutinefunction,inspect.isasyncgenfunction,inspect.isgeneratorfunction))):
        return Error(ExecutionFailure('execution_obligation','Original bounded synchronous data writer change required'))
    def write(cursor, observed):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False);original_path=cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        cursor.execute("SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')",prepare=False)
        if cursor.fetchone()!=('180006','read committed','off'):raise ValueError('Original supported read-write read-committed data writer transaction required')
        cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation FOR SHARE',prepare=False)
        original=cursor.fetchmany(2)
        if len(original)!=1 or original[0][0].encode('utf8')!=installation_identity:
            raise ValueError('Original data writer installation required')
        installation_administrator_with_cursor(cursor,original[0][1])
        cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE',prepare=False)
        if len(cursor.fetchmany(2))!=1:raise ValueError('Original data writer head required')
        cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE',prepare=False)
        if cursor.fetchmany(2)!=[(installation_identity,authored_profile,expected_generation)]:
            raise ValueError('Original exclusive data writer guard required')
        # Separate fresh statement after draining original guard-share holders.
        cursor.execute('SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled LIMIT 1',prepare=False)
        if cursor.fetchall():raise ValueError('Original publication operations remain unsettled')
        # Issue callback DML only after the separate guard/claim commands.
        result=action(cursor)
        if inspect.isgenerator(result) or inspect.iscoroutine(result):
            result.close();raise ValueError('Original data writer action must complete synchronously')
        if result is not None:raise ValueError('Original data writer action must complete or raise')
        cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1',prepare=False)
        if cursor.fetchmany(2)!=[(installation_identity,authored_profile,expected_generation+expected_event_count)]:
            raise ValueError('Original stored data writer generation required')
        cursor.execute('SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled LIMIT 1',prepare=False)
        if cursor.fetchall():raise ValueError('Original publication exclusion changed during data writer advance')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchone()!=(original_path,):raise ValueError('Original data writer caller path restoration required')
        return PendingDataWriterGeneration(installation_identity,authored_profile,expected_generation+expected_event_count)
    return host._run_operation(transaction,write)
