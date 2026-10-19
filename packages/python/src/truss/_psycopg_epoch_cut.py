# SPDX-License-Identifier: MIT OR Apache-2.0
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
            or selected!=('3.3.6','binary',180006,180006)):
        raise ValueError('Qualified PostgreSQL18.6 epoch-cut profile required')
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
        names = ('installation_id','source_epoch','target_incarnation','profile_hex',
                 'evidence_hex','evidence_sha256','actual_writer_xid','actual_database_oid',
                 'actual_backend_pid','original_actor','effective_actor','cut_scope')
        if (cursor.description is None or tuple(d.name for d in cursor.description)!=names
                or any(d.type_code!=25 for d in cursor.description)):
            raise ValueError('Exact original fenced epoch TEXT descriptors required')
        rows = cursor.fetchmany(2)
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


@dataclass(frozen=True)
class _DDLBarrierComparison:
    owner_oid: int
    function_oid: int
    source: str
    include_alter_routine: bool = False
    include_schema_ddl: bool = False
    include_database_ddl: bool = False


def _run_ddl_fenced_epoch_operation(host, transaction, comparison, barrier, callback):
    """Private original installed barrier readback; no authority capability.

    Covers two base tag sets plus optional ALTER ROUTINE, schema and unfiltered database DDL. Event-trigger administration, shared
    roles/ACL/config lifetime and dependency closure remain external premises.
    """
    if type(barrier) is not _DDLBarrierComparison or not callable(callback):
        raise ValueError('Original DDL barrier comparison and callback required')
    owner, function, source = barrier.owner_oid, barrier.function_oid, barrier.source
    if type(barrier.include_alter_routine) is not bool:raise ValueError('Exact ALTER ROUTINE barrier selection required')
    extended=barrier.include_alter_routine
    if type(barrier.include_schema_ddl) is not bool:raise ValueError('Exact schema DDL barrier selection required')
    schemas=barrier.include_schema_ddl
    if type(barrier.include_database_ddl) is not bool:raise ValueError('Exact database DDL barrier selection required')
    database_ddl=barrier.include_database_ddl
    if (type(owner) is not int or type(function) is not int
            or not 0 < owner <= 4294967295 or not 0 < function <= 4294967295
            or type(source) is not str or not 1 <= len(source.encode('utf8')) <= 65536):
        raise ValueError('Bounded original native barrier identity required')
    def qualify(cursor):
        cursor.execute("SELECT pg_catalog.current_setting('event_triggers')::pg_catalog.text",prepare=False,binary=False)
        if (cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25):
            raise ValueError('Exact native event trigger setting descriptor required')
        if cursor.fetchmany(2)!=[('on',)]:
            raise ValueError('Original native event trigger execution required')
        cursor.execute("SELECT e.evtname::pg_catalog.text,e.evtevent::pg_catalog.text,e.evtenabled::pg_catalog.text,"
                       "e.evtowner::pg_catalog.text,pg_catalog.to_jsonb(e.evttags)::pg_catalog.text,"
                       "p.oid::pg_catalog.text,p.proowner::pg_catalog.text,n.nspname::pg_catalog.text,p.proname::pg_catalog.text,"
                       "l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,"
                       "(p.prorettype OPERATOR(pg_catalog.=) 'pg_catalog.event_trigger'::pg_catalog.regtype)::pg_catalog.text,"
                       "p.proretset::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,"
                       "pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,"
                       "EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a "
                       "WHERE a.grantee OPERATOR(pg_catalog.=) 0 AND a.privilege_type OPERATOR(pg_catalog.=) 'EXECUTE')::pg_catalog.text "
                       "FROM pg_catalog.pg_event_trigger e JOIN pg_catalog.pg_proc p ON p.oid OPERATOR(pg_catalog.=) e.evtfoid "
                       "JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace "
                       "JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang "
                       "WHERE (e.evtname IN ('truss_routine_ddl_writer_barrier','truss_table_ddl_writer_barrier') OR ("+("true" if extended else "false")+" AND e.evtname='truss_z_routine_ddl_writer_barrier') OR ("+("true" if schemas else "false")+" AND e.evtname='truss_schema_ddl_writer_barrier') OR ("+("true" if database_ddl else "false")+" AND e.evtname='truss_database_ddl_writer_barrier')) "
                       "ORDER BY e.evtname",prepare=False,binary=False)
        if (cursor.description is None or len(cursor.description)!=19
                or any(d.type_code!=25 for d in cursor.description)):
            raise ValueError('Exact original DDL barrier TEXT descriptors required')
        rows=cursor.fetchmany(3+int(extended)+int(schemas)+int(database_ddl))
        suffix=(str(function),str(owner),'truss','runtime_fence_routine_ddl_writer','plpgsql','f','0',
                'true','false','false','v','["search_path=pg_catalog, pg_temp"]',source,'false')
        expected=[('truss_routine_ddl_writer_barrier','ddl_command_start','A',str(owner),
                   '["CREATE FUNCTION", "ALTER FUNCTION", "DROP FUNCTION", "CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE"]',*suffix),
                  ('truss_table_ddl_writer_barrier','ddl_command_start','A',str(owner),
                   '["CREATE TABLE", "ALTER TABLE", "DROP TABLE"]',*suffix)]
        if extended:expected.append(('truss_z_routine_ddl_writer_barrier','ddl_command_start','A',str(owner),'["ALTER ROUTINE"]',*suffix))
        if schemas:expected.append(('truss_schema_ddl_writer_barrier','ddl_command_start','A',str(owner),'["CREATE SCHEMA", "ALTER SCHEMA", "DROP SCHEMA"]',*suffix))
        if database_ddl:expected.append(('truss_database_ddl_writer_barrier','ddl_command_start','A',str(owner),None,*suffix))
        expected.sort(key=lambda row:row[0])
        if rows!=expected:
            raise ValueError('Exact original installed DDL barriers required')
        return callback(cursor)
    return _run_fenced_epoch_operation(host,transaction,comparison,qualify)


def _run_unprivileged_ddl_fenced_epoch_operation(host, transaction, comparison, barrier, callback):
    """Selected session/effective role snapshot exclusion, not role lifetime proof.

    Both identities must lack superuser/CREATEROLE/BYPASSRLS and transitive
    membership in the selected barrier owner. Issuer, reachable definer routines,
    concurrent shared-role changes and full grants remain separate obligations.
    """
    if type(barrier) is not _DDLBarrierComparison or not callable(callback):
        raise ValueError('Original DDL barrier comparison and callback required')
    owner=barrier.owner_oid
    def exclude(cursor):
        cursor.execute("SELECT s.oid::pg_catalog.text,s.rolsuper::pg_catalog.text,s.rolcreaterole::pg_catalog.text,s.rolbypassrls::pg_catalog.text,"
                       "c.oid::pg_catalog.text,c.rolsuper::pg_catalog.text,c.rolcreaterole::pg_catalog.text,c.rolbypassrls::pg_catalog.text,"
                       "pg_catalog.pg_has_role(s.oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text,"
                       "pg_catalog.pg_has_role(c.oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text "
                       "FROM pg_catalog.pg_roles s CROSS JOIN pg_catalog.pg_roles c "
                       "WHERE s.rolname OPERATOR(pg_catalog.=) session_user AND c.rolname OPERATOR(pg_catalog.=) current_user",
                       (str(owner),str(owner)),prepare=False,binary=False)
        rows=cursor.fetchmany(2)
        if (cursor.description is None or len(cursor.description)!=10
                or any(d.type_code!=25 for d in cursor.description) or len(rows)!=1
                or len(rows[0])!=10 or any(type(v) is not str for v in rows[0])
                or not rows[0][0].isdigit() or not rows[0][4].isdigit()
                or tuple(rows[0][1:4])+tuple(rows[0][5:])!=('false',)*8):
            raise ValueError('Original session and effective role administration exclusion required')
        return callback(cursor)
    return _run_ddl_fenced_epoch_operation(host,transaction,comparison,barrier,exclude)


def _run_no_definer_ddl_fenced_epoch_operation(host, transaction, comparison, barrier, callback):
    """Selected no-reachable-definer snapshot profile, not complete call closure.

    Conservatively includes EXECUTE reachability even without current schema
    USAGE (previously resolved statements can retain routine identities).
    Profiles allowing qualified definers require a separate exact inventory.
    """
    if not callable(callback):raise ValueError('Private operation callback required')
    def exclude(cursor):
        cursor.execute("SELECT p.oid::pg_catalog.text FROM pg_catalog.pg_proc p "
                       "WHERE p.prosecdef AND (pg_catalog.has_function_privilege(session_user,p.oid,'EXECUTE') "
                       "OR pg_catalog.has_function_privilege(current_user,p.oid,'EXECUTE')) LIMIT 1",
                       prepare=False,binary=False)
        rows=cursor.fetchmany(2)
        if (cursor.description is None or len(cursor.description)!=1
                or cursor.description[0].type_code!=25 or rows!=[]):
            raise ValueError('Selected no-reachable-definer profile required')
        return callback(cursor)
    return _run_unprivileged_ddl_fenced_epoch_operation(host,transaction,comparison,barrier,exclude)


def _run_set_role_excluded_ddl_fenced_epoch_operation(host, transaction, comparison, barrier, callback):
    """Selected SET-reachable role/definer snapshot, not shared-role lifetime.

    PostgreSQL16 SET reachability differs from inherited privilege availability.
    Qualified definer profiles and concurrent role/ACL changes remain separate.
    """
    if type(barrier) is not _DDLBarrierComparison or not callable(callback):
        raise ValueError('Original barrier and callback required')
    owner=barrier.owner_oid
    def exclude(cursor):
        cursor.execute("SELECT r.oid::pg_catalog.text FROM pg_catalog.pg_roles r "
                       "WHERE (pg_catalog.pg_has_role(session_user,r.oid,'SET') OR pg_catalog.pg_has_role(current_user,r.oid,'SET')) "
                       "AND (r.rolsuper OR r.rolcreaterole OR r.rolbypassrls OR r.oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid "
                       "OR EXISTS(SELECT 1 FROM pg_catalog.pg_proc p WHERE p.prosecdef "
                       "AND pg_catalog.has_function_privilege(r.oid,p.oid,'EXECUTE'))) LIMIT 1",
                       (str(owner),),prepare=False,binary=False)
        rows=cursor.fetchmany(2)
        if (cursor.description is None or len(cursor.description)!=1
                or cursor.description[0].type_code!=25 or rows!=[]):
            raise ValueError('Selected SET-reachable role exclusion required')
        return callback(cursor)
    return _run_no_definer_ddl_fenced_epoch_operation(host,transaction,comparison,barrier,exclude)


def _exclude_native_predefined_role_reachability(cursor):
    """Actual native role snapshot only; neither authentication nor lifetime."""
    cursor.execute("SELECT p.oid::pg_catalog.text FROM pg_catalog.pg_roles r CROSS JOIN pg_catalog.pg_roles p "
                   "WHERE (pg_catalog.pg_has_role(session_user,r.oid,'SET') OR pg_catalog.pg_has_role(current_user,r.oid,'SET')) "
                   "AND pg_catalog.left(p.rolname::pg_catalog.text,3) OPERATOR(pg_catalog.=) 'pg_' "
                   "AND (pg_catalog.pg_has_role(r.oid,p.oid,'USAGE') OR pg_catalog.pg_has_role(r.oid,p.oid,'SET')) LIMIT 1",
                   prepare=False,binary=False)
    rows=cursor.fetchmany(2)
    if (cursor.description is None or len(cursor.description)!=1
            or cursor.description[0].type_code!=25 or rows!=[]):
        raise ValueError('Selected predefined-role exclusion required')


def _run_predefined_role_excluded_ddl_fenced_epoch_operation(host, transaction, comparison, barrier, callback):
    """Conservative predefined-role snapshot; no complete privilege/lifetime proof.

    Inspect inherited privileges of every SET-reachable identity, not membership
    alone. Reserved pg_ roles are excluded without assigning portable meanings to
    their version-dependent capabilities. Ordinary object grants remain separate.
    """
    def exclude(cursor):
        _exclude_native_predefined_role_reachability(cursor)
        return callback(cursor)
    if not callable(callback):raise ValueError('Original callback required')
    return _run_set_role_excluded_ddl_fenced_epoch_operation(host,transaction,comparison,barrier,exclude)


@dataclass(frozen=True)
class _AuthorityIssuerComparison:
    owner_oid: int
    writer_oid: int
    writer_source: str
    issuer_oid: int
    issuer_source: str


def _run_issuer_verified_epoch_operation(host, transaction, comparison, barrier, issuer, callback):
    """Original installed writer/issuer correspondence, not authority issuance.

    Language-handler/role/ACL lifetime, issuer credentials and profile/evidence
    provenance remain independent requirements. No capability is returned.
    """
    if type(issuer) is not _AuthorityIssuerComparison or not callable(callback):
        raise ValueError('Original issuer comparison and callback required')
    owner,writer,writer_source,issue,issue_source=(issuer.owner_oid,issuer.writer_oid,issuer.writer_source,issuer.issuer_oid,issuer.issuer_source)
    if (any(type(v) is not int or not 0<v<=4294967295 for v in (owner,writer,issue))
            or any(type(v) is not str or not 1<=len(v.encode('utf8'))<=65536 for v in (writer_source,issue_source))):
        raise ValueError('Bounded original issuer identities required')
    def qualify(cursor):
        cursor.execute("SELECT p.proname::pg_catalog.text,p.oid::pg_catalog.text,p.proowner::pg_catalog.text,"
                       "l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,"
                       "p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,p.proretset::pg_catalog.text,"
                       "p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,"
                       "EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a "
                       "WHERE a.grantee OPERATOR(pg_catalog.=) 0 AND a.privilege_type OPERATOR(pg_catalog.=) 'EXECUTE')::pg_catalog.text "
                       "FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace "
                       "JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang "
                       "WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname IN ('runtime_fence_shared_authority_writer','runtime_issue_authority_epoch') "
                       "ORDER BY p.proname,p.oid",prepare=False,binary=False)
        rows=cursor.fetchmany(3)
        common=('false','false','false','v','["search_path=pg_catalog, pg_temp"]')
        expected=[('runtime_fence_shared_authority_writer',str(writer),str(owner),'plpgsql','f','0','','2278',*common,writer_source,'false'),
                  ('runtime_issue_authority_epoch',str(issue),str(owner),'plpgsql','f','5','25 25 25 17 17','25',*common,issue_source,'false')]
        if (cursor.description is None or len(cursor.description)!=15
                or any(d.type_code!=25 for d in cursor.description) or rows!=expected):
            raise ValueError('Exact original installed authority writer/issuer required')
        return callback(cursor)
    return _run_ddl_fenced_epoch_operation(host,transaction,comparison,barrier,qualify)
