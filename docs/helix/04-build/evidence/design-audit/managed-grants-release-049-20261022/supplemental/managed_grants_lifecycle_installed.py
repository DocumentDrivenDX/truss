#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Installed-wheel managed-grant catalog lifecycle qualification.

Run with the qualification venv and PYTHONPATH=scripts:packages/python/tests.
The package itself is imported only from the installed wheel.
"""
from __future__ import annotations

import copy
import hashlib
from importlib.metadata import version as package_version
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import psycopg
from truss import (CatalogDocument, CatalogRuntimeConfiguration, Error, ModuleAccessGrant,
                   Ok, adopt_psycopg_host, create_reference_assembly)
from truss.contracts import MapValue, TextValue
from truss.groups import AuthoredValue, CreateObject, GroupSuccess, RootlessOwnership
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
from native_fixture import DatabaseFixture, WorkerCluster, connect as native_connect
from test_catalog_relational_support import relational_document


EXPECTED_WHEEL_SHA256 = os.environ.get('TRUSS_EXPECTED_WHEEL_SHA256')
EXPECTED_MANIFEST_SHA256 = os.environ.get('TRUSS_EXPECTED_RUNTIME_MANIFEST_SHA256')
EXPECTED_VERSION = os.environ.get('TRUSS_EXPECTED_PACKAGE_VERSION', '0.0.48')
BUN = '/opt/homebrew/bin/bun'
WHEEL = Path(os.environ.get('TRUSS_QUALIFICATION_WHEEL',
    '/private/tmp/truss-managed-grants-qualification/dist-final-1/truss_toolkit-0.0.48-py3-none-any.whl'))
OUT = Path(__file__).with_name('managed_grants_lifecycle_installed.json')


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def wheel_provenance() -> dict:
    import truss
    from truss._migration_recipe import load_recipe
    import psycopg.pq
    import weft

    installed = Path(truss.__file__).resolve()
    require('site-packages' in str(installed), f'not imported from installed wheel: {installed}')
    require(not str(installed).startswith(str(Path.cwd() / 'packages/python/src')),
            f'source tree shadowed wheel: {installed}')
    require(EXPECTED_WHEEL_SHA256 is not None and EXPECTED_MANIFEST_SHA256 is not None,
            'final wheel and runtime manifest SHA256 expectations must be supplied in the environment')
    wheel_hash = hashlib.sha256(WHEEL.read_bytes()).hexdigest()
    require(wheel_hash == EXPECTED_WHEEL_SHA256, f'wheel digest changed: {wheel_hash}')
    runtime_manifest_hash = hashlib.sha256(
        (installed.parent / '_catalog_runtime' / 'manifest.json').read_bytes()).hexdigest()
    manifest, _, recipe_hash = load_recipe()
    manifest_target = manifest.get('target')
    require(runtime_manifest_hash == EXPECTED_MANIFEST_SHA256 and manifest_target == runtime_manifest_hash,
            f'installed runtime manifest or recipe target changed: {runtime_manifest_hash}/{manifest_target}')
    installed_version = package_version('truss-toolkit')
    require(installed_version == EXPECTED_VERSION, f'installed version changed: {installed_version}')
    return {'package': str(installed), 'version': installed_version,
            'wheel': str(WHEEL), 'wheelSha256': wheel_hash,
            'migrationRecipeSha256': recipe_hash, 'managedTargetSha256': runtime_manifest_hash,
            'psycopg': psycopg.__version__, 'libpqImplementation': psycopg.pq.__impl__,
            'weft': getattr(weft, '__version__', 'version-unavailable'),
            'bun': subprocess.run([BUN, '--version'], check=True, text=True,
                                  capture_output=True).stdout.strip()}


def grant_trigger(admin_uri: str, platform: str) -> None:
    observer = native_connect(admin_uri, timeout=20)
    try:
        observer.run('''CREATE FUNCTION public.mg_lifecycle_grant_fixture()
          RETURNS event_trigger LANGUAGE plpgsql SECURITY DEFINER
          SET search_path=pg_catalog AS $$
          DECLARE item record; grantee text;
          BEGIN
            grantee := current_setting('truss.fixture_grantee', true);
            IF grantee IS NULL OR grantee = '' THEN RETURN; END IF;
            FOR item IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands() LOOP
              IF item.schema_name = 'truss' AND item.object_type = 'schema' THEN
                EXECUTE pg_catalog.format('GRANT USAGE, CREATE ON SCHEMA truss TO %I WITH GRANT OPTION', grantee);
              ELSIF item.schema_name = 'truss' AND item.object_type = 'table'
                    AND item.object_identity = 'truss.object' THEN
                EXECUTE pg_catalog.format('GRANT SELECT ON TABLE truss.object TO %I WITH GRANT OPTION', grantee);
              END IF;
            END LOOP;
          END $$''')
        observer.run('''CREATE EVENT TRIGGER mg_lifecycle_grant_fixture
          ON ddl_command_end EXECUTE FUNCTION public.mg_lifecycle_grant_fixture()''')
    finally:
        observer.close()


def pg_acl_snapshot(conn: psycopg.Connection, role_oid: int) -> list[tuple]:
    return conn.execute('''
      SELECT x.class, x.object_oid::text, x.object_name, x.grantor_oid::text,
             x.privilege, x.is_grantable
      FROM (
        SELECT 'schema'::text AS class, n.oid AS object_oid, n.nspname AS object_name,
               g.grantor AS grantor_oid, g.privilege_type AS privilege, g.is_grantable
        FROM pg_catalog.pg_namespace n
        CROSS JOIN LATERAL pg_catalog.aclexplode(n.nspacl) g
        WHERE n.nspname='truss' AND g.grantee=%s
        UNION ALL
        SELECT CASE c.relkind WHEN 'S' THEN 'sequence' ELSE 'relation' END,
               c.oid, n.nspname||'.'||c.relname, g.grantor, g.privilege_type, g.is_grantable
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL pg_catalog.aclexplode(c.relacl) g
        WHERE n.nspname='truss' AND g.grantee=%s
        UNION ALL
        SELECT 'routine', p.oid, n.nspname||'.'||p.proname||'('||pg_catalog.pg_get_function_identity_arguments(p.oid)||')',
               g.grantor, g.privilege_type, g.is_grantable
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) g
        WHERE n.nspname='truss' AND g.grantee=%s
        UNION ALL
        SELECT 'type', t.oid, n.nspname||'.'||t.typname, g.grantor, g.privilege_type, g.is_grantable
        FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace
        CROSS JOIN LATERAL pg_catalog.aclexplode(t.typacl) g
        WHERE n.nspname='truss' AND g.grantee=%s
        UNION ALL
        SELECT 'column', a.attrelid, n.nspname||'.'||c.relname||'.'||a.attname,
               g.grantor, g.privilege_type, g.is_grantable
        FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL pg_catalog.aclexplode(a.attacl) g
        WHERE n.nspname='truss' AND a.attnum>0 AND NOT a.attisdropped AND g.grantee=%s
      ) x ORDER BY 1,2,4,5,6
    ''', (role_oid, role_oid, role_oid, role_oid, role_oid)).fetchall()


def admin_connect(uri: str) -> psycopg.Connection:
    return psycopg.connect(**psycopg.conninfo.conninfo_to_dict(uri), autocommit=True,
                            options='-c statement_timeout=10000')


def accept(assembly, host, connection, tx, source: dict, revision: str, key: str):
    source_bytes = json.dumps(source, ensure_ascii=False, separators=(',', ':')).encode()
    doc = CatalogDocument('adoc', revision, source_bytes)
    prepared = assembly.prepare_catalog((doc,), source_version=source['umf'], bun_executable=BUN)
    result = assembly.accept_in_transaction(tx, prepared, request_key=key, bun_executable=BUN)
    if isinstance(result, Error):
        raise AssertionError(f'catalog {revision} failed: {result!r}; native={host._custody.last_attempt.error!r}')
    require(isinstance(result, Ok), f'catalog {revision} returned unexpected outcome: {result!r}')
    return result.value, source_bytes, doc


def main() -> None:
    require(not OUT.exists(), f'refusing to overwrite existing receipt: {OUT}')
    provenance = wheel_provenance()
    suffix = uuid4().hex[:10]
    platform = 'mgl_platform_' + suffix
    reader = 'mgl_reader_' + suffix
    writer = 'mgl_writer_' + suffix
    result = {'provenance': provenance, 'checks': {}, 'retirement': {}}
    with WorkerCluster() as worker:
        result['nativeWorker'] = {'settings': worker.settings,
                                  'socketOnly': worker.settings['listen_addresses'] == '',
                                  'serverVersion': worker.settings['server_version']}
        fixture = DatabaseFixture(worker.root)
        installer = host = admin = None
        try:
            fixture.admin.run(f'ALTER ROLE "{fixture.role}" LOGIN CREATEROLE')
            fixture.admin.run(f'CREATE ROLE "{platform}" NOLOGIN')
            fixture.admin.run(f'CREATE ROLE "{reader}" NOLOGIN')
            fixture.admin.run(f'CREATE ROLE "{writer}" NOLOGIN')
            client = 'mgl_client_' + suffix
            fixture.admin.run(f'CREATE ROLE "{client}" LOGIN')
            fixture.admin.run(f'GRANT "{writer}" TO "{client}" WITH INHERIT TRUE, SET FALSE')
            grant_trigger(fixture.get_uri(), platform)
            params = psycopg.conninfo.conninfo_to_dict(fixture.get_uri())
            installer_params = {**params, 'user': fixture.role}
            installer = psycopg.connect(**installer_params, autocommit=True,
                                        options='-c statement_timeout=10000')
            installer.execute('BEGIN')
            installer.execute("SELECT pg_catalog.set_config('truss.fixture_grantee', %s, true)", (platform,))
            host = adopt_psycopg_host(installer, statement_timeout_ms=10000, operation_timeout_ms=30000)
            tx = host.adopt_transaction().value
            assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            installed = assembly.install_in_transaction(tx, tolerated_grantees=(platform,))
            require(isinstance(installed, Ok) and installed.value.status == 'pending_commit',
                    f'managed install failed: {installed!r}; native={host._custody.last_attempt.error!r}')
            host.detach()
            installer.commit()
            installer.close()
            installer = host = None

            fixture.admin.run(f'GRANT "{installed.value.registrar_role}" TO "{client}" WITH INHERIT TRUE, SET FALSE')
            client_params = {**params, 'user': client}
            installer = psycopg.connect(**client_params, autocommit=True,
                                        options='-c statement_timeout=10000')
            installer.execute('BEGIN')
            host = adopt_psycopg_host(installer, statement_timeout_ms=10000, operation_timeout_ms=30000)
            tx = host.adopt_transaction().value
            assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            source = relational_document()
            source['id'] = 'adoc'
            first, source_r1, document_r1 = accept(assembly, host, installer, tx, source, 'r1', 'managed-life-r1')
            require(getattr(first, 'revision', None) == 1, f'first accepted revision unexpected: {first!r}')
            view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
            require(isinstance(view, Ok), f'catalog view unavailable after r1: {view!r}')
            type_ref = next(d.reference for d in view.value.view.definitions
                            if d.reference.kind == 'type' and
                            d.reference.owner.document_id == 'adoc' and
                            d.reference.authored_identity == 'A')
            host.detach()
            installer.commit()
            installer.close()
            installer = host = None

            installer = admin_connect(fixture.get_uri())
            installer.execute('BEGIN')
            host = adopt_psycopg_host(installer, statement_timeout_ms=10000, operation_timeout_ms=30000)
            tx = host.adopt_transaction().value
            assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            configured = assembly.configure_module_access_in_transaction(
                tx, (ModuleAccessGrant('adoc', 'm', reader, writer),))
            require(isinstance(configured, Ok), f'module access configuration failed: {configured!r}')
            host.detach()
            installer.commit()
            installer.close()
            installer = host = None

            installer = psycopg.connect(**client_params, autocommit=True,
                                        options='-c statement_timeout=10000')
            installer.execute('BEGIN')
            host = adopt_psycopg_host(installer, statement_timeout_ms=10000, operation_timeout_ms=30000)
            tx = host.adopt_transaction().value
            assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            object_input = CreateObject(type_definition_pin=type_ref.definition_pin,
                values=(AuthoredValue(name='A-label', value=TextValue(kind='string', text='retained-label')),
                        AuthoredValue(name='A-value', value=TextValue(kind='string', text='retained-value'))),
                ownership=RootlessOwnership(), alias='managed-life-object')
            context = assembly.group_context_in_transaction(tx)
            require(isinstance(context, Ok), f'group context unavailable: {context!r}')
            applied = assembly.apply_in_transaction(tx, context.value.input((object_input,), MapValue(entries=())),
                context.value.request('managed-life-create'), documents=(document_r1,), bun_executable=BUN)
            require(isinstance(applied, Ok) and isinstance(applied.value, GroupSuccess),
                    f'object creation failed: {applied!r}')
            object_id = int(applied.value.response.semantic.results[0].identity.id)
            host.detach()
            installer.commit()
            installer.close()
            installer = host = None

            migrations = RuntimeMigrations(lambda: admin_connect(fixture.get_uri()),
                HostRecoveryRegistry(fixture.root / ('managed-lifecycle-' + suffix + '.sqlite')))
            require(migrations.status()['state'] == 'current' and migrations.verify() == migrations.status(),
                    'migration status was not current after initial accepted catalog')

            admin = admin_connect(fixture.get_uri())
            platform_oid = admin.execute('SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s', (platform,)).fetchone()[0]
            carrier_r1 = admin.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton').fetchone()[0]
            acl_r1 = pg_acl_snapshot(admin, platform_oid)
            require(bool(acl_r1), 'event-trigger platform ACL was not observed')
            result['managedPolicy'] = {
                'platformRole': platform, 'platformRoleOid': platform_oid,
                'roles': carrier_r1['roles'],
                'carrierSha256': hashlib.sha256(json.dumps(carrier_r1, sort_keys=True,
                    separators=(',', ':')).encode()).hexdigest(),
                'initialAclRows': [list(row) for row in acl_r1]}
            object_row_r1 = admin.execute('SELECT id, type_id, props, retained, root_id, root_type, rev, ver FROM truss.object WHERE id=%s', (object_id,)).fetchone()
            require(object_row_r1 is not None, 'created object row missing before evolution')
            head_r1 = admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0]
            require(head_r1 == 1, f'head after r1 is {head_r1}')
            admin.close()
            admin = None

            # Add one optional field and member: a supported additive evolution.
            source_r2 = copy.deepcopy(source)
            module = source_r2['modules'][0]
            record = next(e for e in module['elements'] if e['id'] == 'A')
            record['members'].append({'module': 'm', 'element': 'A-note'})
            module['elements'].append({'id': 'A-note', 'name': 'A-note', 'kind': 'field',
                'scalarType': 'string', 'nullability': 'absent-allowed', 'cardinality': 'one', 'extensions': {}})
            installer = psycopg.connect(**client_params, autocommit=True,
                                        options='-c statement_timeout=10000')
            installer.execute('BEGIN')
            host = adopt_psycopg_host(installer, statement_timeout_ms=10000, operation_timeout_ms=30000)
            tx = host.adopt_transaction().value
            assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            registered_r2, source_r2_bytes, _ = accept(assembly, host, installer, tx, source_r2, 'r2', 'managed-life-r2')
            require(getattr(registered_r2, 'revision', None) == 2,
                    f'supported additive evolution did not reach revision 2: {registered_r2!r}')
            host.detach()
            installer.commit()
            installer.close()
            installer = host = None

            admin = admin_connect(fixture.get_uri())
            require(admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0] == 2,
                    'supported evolution did not advance committed head')
            stored_r1_hash, stored_r1 = admin.execute('SELECT content_sha256, document FROM truss.schema_doc WHERE doc_id=%s AND rev=%s',
                                       ('adoc', 1)).fetchone()
            stored_r2_hash, stored_r2 = admin.execute('SELECT content_sha256, document FROM truss.schema_doc WHERE doc_id=%s AND rev=%s',
                                       ('adoc', 2)).fetchone()
            require(stored_r1_hash == hashlib.sha256(source_r1).hexdigest(),
                    'r1 original content digest changed')
            require(stored_r2_hash == hashlib.sha256(source_r2_bytes).hexdigest(),
                    'r2 original content digest changed')
            require(json.loads(stored_r1) == json.loads(source_r1), 'r1 source semantics changed')
            require(json.loads(stored_r2) == json.loads(source_r2_bytes), 'r2 source semantics were not retained')
            stored_r1_bytes = stored_r1.encode()
            stored_r2_bytes = stored_r2.encode()
            require(admin.execute('SELECT id, type_id, props, retained, root_id, root_type, rev, ver FROM truss.object WHERE id=%s',
                                  (object_id,)).fetchone() == object_row_r1,
                    'native object row changed during additive evolution')
            require(admin.execute('SELECT count(*) FROM truss.journal').fetchone()[0] == 1,
                    'journal history changed during additive evolution')
            report_r1 = admin.execute('SELECT report_bytes FROM truss.catalog_acceptance_report WHERE rev=1').fetchone()[0]
            report_r2 = admin.execute('SELECT report_bytes FROM truss.catalog_acceptance_report WHERE rev=2').fetchone()[0]
            require(bytes(report_r1) == first.report_bytes and bytes(report_r2) == registered_r2.report_bytes,
                    'accepted registration reports were not preserved byte-for-byte')
            carrier_r2 = admin.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton').fetchone()[0]
            acl_r2 = pg_acl_snapshot(admin, platform_oid)
            require(carrier_r2 == carrier_r1 and acl_r2 == acl_r1,
                    'managed policy or selected platform ACL changed during supported evolution')
            result['checks']['supported_additive_evolution'] = {
                'head': 2, 'r1SourceSha256': hashlib.sha256(stored_r1_bytes).hexdigest(),
                'r2SourceSha256': hashlib.sha256(stored_r2_bytes).hexdigest(),
                'historicalSourceAndObjectPreserved': True, 'managedCarrierPreserved': True,
                'selectedAclRows': len(acl_r2)}
            admin.close()
            admin = None

            # Attempt record retirement through the ordinary acceptance API.
            source_r3 = copy.deepcopy(source_r2)
            module3 = source_r3['modules'][0]
            module3['elements'] = [e for e in module3['elements']
                                   if e['id'] not in {'A', 'A-label', 'A-value', 'A-note'}]
            module3['relationships'] = []
            installer = psycopg.connect(**client_params, autocommit=True,
                                        options='-c statement_timeout=10000')
            installer.execute('BEGIN')
            installer.execute('CREATE TEMP TABLE managed_retirement_caller_work(value text)')
            installer.execute("INSERT INTO managed_retirement_caller_work VALUES ('kept')")
            host = adopt_psycopg_host(installer, statement_timeout_ms=10000, operation_timeout_ms=30000)
            tx = host.adopt_transaction().value
            assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            prepared_r3 = assembly.prepare_catalog((CatalogDocument('adoc', 'r3',
                json.dumps(source_r3, ensure_ascii=False, separators=(',', ':')).encode()),),
                source_version=source_r3['umf'], bun_executable=BUN)
            refusal = assembly.accept_in_transaction(tx, prepared_r3, request_key='managed-life-retire-r3', bun_executable=BUN)
            native_error = getattr(getattr(host._custody, 'last_attempt', None), 'error', None)
            diagnostic = {'sqlstate': getattr(native_error, 'sqlstate', None),
                          'message': getattr(getattr(native_error, 'diag', None), 'message_primary', str(native_error)),
                          'exception': repr(native_error)}
            result['retirement'] = {'outcome': type(getattr(refusal, 'value', refusal)).__name__,
                                    'public': repr(refusal), 'nativeAttempt': diagnostic}
            require(isinstance(refusal, Error) and refusal.error.sql_state == '0A000' and
                    refusal.error.catalog_code == 'unsupported_profile',
                    f'retirement failed for an unrelated reason or was accepted: {refusal!r}; native={diagnostic!r}')
            require(diagnostic['sqlstate'] == '0A000' and
                    diagnostic['message'] == 'record retirement requires explicit support',
                    f'expected exact bounded retirement diagnostic, got {diagnostic!r}')
            require(installer.execute('SELECT 42').fetchone() == (42,),
                    'caller transaction was not usable after retirement refusal')
            require(installer.execute('SELECT value FROM managed_retirement_caller_work').fetchone() == ('kept',),
                    'retirement refusal disturbed caller-owned transaction work')
            host.detach()
            installer.commit()
            installer.close()
            installer = host = None

            admin = admin_connect(fixture.get_uri())
            head_after = admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0]
            docs_after = admin.execute('SELECT doc_id, rev, document FROM truss.schema_doc ORDER BY rev').fetchall()
            reports_after = admin.execute('SELECT rev, report_bytes FROM truss.catalog_acceptance_report ORDER BY rev').fetchall()
            object_after = admin.execute('SELECT id, type_id, props, retained, root_id, root_type, rev, ver FROM truss.object WHERE id=%s',
                                         (object_id,)).fetchone()
            journal_after = admin.execute('SELECT count(*) FROM truss.journal').fetchone()[0]
            carrier_after = admin.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton').fetchone()[0]
            acl_after = pg_acl_snapshot(admin, platform_oid)
            require(head_after == 2 and [(r[0], r[1], r[2]) for r in docs_after] ==
                    [('adoc', 1, stored_r1), ('adoc', 2, stored_r2)],
                    'retirement refusal changed committed head or source history')
            require([(r[0], bytes(r[1])) for r in reports_after] ==
                    [(1, first.report_bytes), (2, registered_r2.report_bytes)],
                    'retirement refusal changed report/history bytes')
            require(object_after == object_row_r1 and journal_after == 1,
                    'retirement refusal changed native data or journal history')
            require(carrier_after == carrier_r1 and acl_after == acl_r1,
                    'retirement refusal changed managed policy or selected platform ACLs')
            result['retirement'].update({'headPreserved': head_after, 'sourceHistoryPreserved': True,
                'objectAndJournalPreserved': True, 'managedCarrierPreserved': True,
                'selectedAclPreserved': True})

            # Variation on a selected, installed object grant must remain admissible.
            admin.execute(psycopg.sql.SQL('GRANT INSERT ON TABLE truss.object TO {}').format(
                psycopg.sql.Identifier(platform)))
            changed_acl = pg_acl_snapshot(admin, platform_oid)
            require(changed_acl != acl_r1, 'native INSERT ACL variation was not applied')
            current = migrations.status()
            require(current['state'] == 'current' and migrations.verify() == current,
                    'migration status rejected a later selected-role ACL addition')
            require(admin.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton').fetchone()[0] == carrier_r1,
                    'carrier changed after selected-role ACL addition')
            admin.execute(psycopg.sql.SQL('REVOKE INSERT ON TABLE truss.object FROM {}').format(
                psycopg.sql.Identifier(platform)))
            restored_acl = pg_acl_snapshot(admin, platform_oid)
            require(restored_acl == acl_r1, 'native ACL did not return to its captured baseline')
            current = migrations.status()
            require(current['state'] == 'current' and migrations.verify() == current,
                    'migration status rejected a later selected-role ACL removal')
            require(admin.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton').fetchone()[0] == carrier_r1,
                    'carrier changed after selected-role ACL removal')
            result['checks']['selected_acl_variation'] = {
                'addedPrivilege': 'INSERT ON truss.object', 'addAndRemoveAcceptedByStatus': True,
                'policyCarrierUnchanged': True,
                'carrierSha256': hashlib.sha256(json.dumps(carrier_r1, sort_keys=True,
                    separators=(',', ':')).encode()).hexdigest(),
                'aclBefore': [list(row) for row in acl_r1],
                'aclAfterAdd': [list(row) for row in changed_acl],
                'aclAfterRevoke': [list(row) for row in restored_acl], 'aclRestored': True}
            admin.close()
            admin = None
        finally:
            if host is not None:
                host.detach()
            if installer is not None:
                if not installer.closed:
                    installer.rollback()
                    installer.close()
                installer = None
            if admin is not None:
                admin.close()
                admin = None
            fixture.cleanup()
            worker.verify_clean()
    result['cleanup'] = {'ownedWorkerInventoryRestored': True, 'workerStoppedByContext': True}
    result['python'] = sys.version
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
