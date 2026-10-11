"""Private within-operation epoch cut; not authenticated source/authority admission.

Requires independently qualified installed helper/ACL and caller-exclusive host
custody. No retained capability or liveness claim survives the callback. Full
source census, shared roles and authorization facts remain separate producers.
"""
from dataclasses import dataclass
from hashlib import sha256
from .psycopg_host import PsycopgHost, PsycopgProfile


@dataclass(frozen=True)
class _EpochComparison:
    installation: str
    epoch: str
    incarnation: str
    profile: bytes
    evidence: bytes


def _run_fenced_epoch_operation(host, transaction, comparison, callback):
    """Compare original selected bytes before private callback in one host scope."""
    if type(host) is not PsycopgHost or type(comparison) is not _EpochComparison:
        raise ValueError('Original selected host and exact comparison required')
    native_profile=host.profile
    if type(native_profile) is not PsycopgProfile:
        raise ValueError('Qualified epoch-cut host profile required')
    selected=(native_profile.psycopg,native_profile.implementation,native_profile.libpq,native_profile.server)
    if (tuple(type(v) for v in selected)!=(str,str,int,int)
            or selected!=('3.3.6','binary',180006,170011)):
        raise ValueError('Qualified PostgreSQL17.11 epoch-cut profile required')
    installation, epoch, incarnation, profile, evidence = (
        comparison.installation, comparison.epoch, comparison.incarnation,
        comparison.profile, comparison.evidence)
    for value, maximum in ((installation, 1024), (epoch, 256), (incarnation, 1024)):
        if type(value) is not str or not 1 <= len(value.encode('utf8')) <= maximum:
            raise ValueError('Bounded exact epoch comparison text required')
    if (type(profile) is not bytes or not 1 <= len(profile) <= 65536
            or type(evidence) is not bytes or not 1 <= len(evidence) <= 1048576):
        raise ValueError('Bounded original profile/evidence comparison required')
    if not callable(callback): raise ValueError('Private operation callback required')

    def execute(cursor, observed):
        from psycopg.types.string import StrDumper
        # Toolkit comparison parameters must not use host custom string codecs.
        cursor.adapters.register_dumper(str, StrDumper)
        cursor.execute("SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text,"
                       "(SELECT oid::pg_catalog.text FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()),"
                       "pg_catalog.pg_backend_pid()::pg_catalog.text,session_user::pg_catalog.text,current_user::pg_catalog.text",
                       prepare=False, binary=False)
        identity = cursor.fetchmany(2)
        if (len(identity) != 1 or len(identity[0]) != 5
                or any(type(v) is not str for v in identity[0])
                or identity[0][2] != observed[0][0]
                or (observed[1] is not None and identity[0][0] != observed[1])):
            raise ValueError('Original native operation identity required')
        cursor.execute('SELECT * FROM truss.runtime_lock_fenced_fresh_source_epoch(%s,%s,%s)',
                       (installation, epoch, incarnation),
                       prepare=False, binary=False)
        rows = cursor.fetchmany(2)
        names = ('installation_id','source_epoch','target_incarnation','profile_hex',
                 'evidence_hex','evidence_sha256','actual_writer_xid','actual_database_oid',
                 'actual_backend_pid','original_actor','effective_actor','cut_scope')
        expected = (installation, epoch, incarnation, profile.hex(), evidence.hex(),
                    sha256(evidence).hexdigest(), *identity[0],
                    'transaction_epoch_state_fence_only')
        if (cursor.description is None or tuple(d.name for d in cursor.description) != names
                or any(d.type_code != 25 for d in cursor.description)
                or len(rows) != 1 or len(rows[0]) != 12
                or any(type(v) is not str for v in rows[0]) or tuple(rows[0]) != expected):
            raise ValueError('Exact original fenced epoch projection required')
        # Callback has the original guarded cursor; no SQL/control/liveness token
        # is exposed outside the host operation. Host confirms scope completion.
        return callback(cursor)
    return host._run_operation(transaction, execute)
