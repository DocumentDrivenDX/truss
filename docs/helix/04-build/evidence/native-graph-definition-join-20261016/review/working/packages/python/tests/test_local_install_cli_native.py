"""Basic explicit CLI installation and retained-directory status confirmation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class LocalInstallCliTests(unittest.TestCase):
    def test_install_commit_and_restart_status(self):
        parent = Path(tempfile.mkdtemp(prefix='truss-install-cli-', dir='/private/tmp'))
        directory = parent / 'postgres'
        command = [sys.executable, '-m', 'truss.cli', '--data-dir', str(directory),
                   '--install', '--probe']
        reports = []
        for _ in range(2):
            result = subprocess.run(command, check=True, capture_output=True, text=True,
                                    env=dict(os.environ))
            reports.append(json.loads(result.stdout))
            self.assertTrue((directory / 'PG_VERSION').is_file())
            self.assertFalse((directory / 'postmaster.pid').exists())
        first, second = reports
        self.assertEqual(first['scope'], 'local_truss_candidate')
        self.assertEqual(first['trussInstallation'], 'installed')
        self.assertEqual(first['serverVersion'], '18.6')
        self.assertEqual(first['installation']['action'], 'created')
        self.assertEqual(first['installation']['releaseId'], 'truss-catalog-runtime/0.31-candidate')
        self.assertRegex(first['installation']['releaseSha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(first['installation']['layoutProfile'], {
            'identity': 'truss-layout', 'version': '0.16',
            'sha256': '261e32c6c62624418f124ac7fbe3c206338322a03755b7ac0f1a7c7d86002368'})
        self.assertTrue(first['installation']['ownerRole'])
        self.assertTrue(first['installation']['registrarRole'])
        self.assertEqual(second['installation']['action'], 'status_confirmed')
        self.assertEqual(second['installation']['installationId'], first['installation']['installationId'])
        self.assertEqual(second['installation']['catalogRevision'], 0)
        self.assertEqual(second['installation']['releaseId'], first['installation']['releaseId'])
        self.assertEqual(second['installation']['releaseSha256'], first['installation']['releaseSha256'])
        self.assertEqual(second['installation']['layoutProfile'], first['installation']['layoutProfile'])
        self.assertNotIn('ownerRole', second['installation'])
        self.assertNotIn('registrarRole', second['installation'])
        unchanged = subprocess.run([sys.executable, '-m', 'truss.cli', '--data-dir', str(directory),
                                    '--upgrade', '--probe'], check=True, capture_output=True,
                                   text=True, env=dict(os.environ))
        report = json.loads(unchanged.stdout)['installation']
        self.assertEqual(report['action'], 'unchanged')
        self.assertEqual(report['installationId'], first['installation']['installationId'])
        self.assertEqual(report['previousReleaseId'], 'truss-catalog-runtime/0.31-candidate')
        self.assertEqual(report['releaseId'], report['previousReleaseId'])
        self.assertEqual(report['layoutProfile'], first['installation']['layoutProfile'])
        self.assertFalse((directory / 'postmaster.pid').exists())
        # Preserve source data on subprocess/assertion failures; clean only success.
        shutil.rmtree(parent)

    @unittest.skipUnless(os.environ.get('TRUSS_UPGRADE_SOURCE_PACKAGE'), 'Exact installed old candidate required')
    def test_explicit_upgrade_from_real_029_installation(self):
        parent = Path(tempfile.mkdtemp(prefix='truss-upgrade-cli-', dir='/private/tmp'))
        directory = parent / 'postgres'
        source = Path(os.environ['TRUSS_UPGRADE_SOURCE_PACKAGE']).resolve()
        script = '''import json,sys
from pathlib import Path
import psycopg,truss
from truss import LocalPostgres,Ok,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
assert Path(truss.__file__).resolve().is_relative_to(Path(sys.argv[2]).resolve())
with LocalPostgres(sys.argv[1]) as runtime:
    with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as connection:
        with connection.transaction():
            host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
            try:
                tx=host.adopt_transaction();assert isinstance(tx,Ok)
                assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host);assert isinstance(assembly,Ok)
                installed=assembly.value.install_in_transaction(tx.value);assert isinstance(installed,Ok)
                assert installed.value.release_id=='truss-catalog-runtime/0.29-candidate'
            finally:host.detach()
        print(json.dumps({'installationId':installed.value.installation_id,'releaseId':installed.value.release_id}))
'''
        original = subprocess.run([sys.executable, '-c', script, str(directory), str(source)],
            env=dict(os.environ, PYTHONPATH=str(source)), check=True, capture_output=True, text=True)
        before = json.loads(original.stdout)
        result = subprocess.run([sys.executable, '-m', 'truss.cli', '--data-dir', str(directory),
                                 '--upgrade', '--probe'], check=True, capture_output=True,
                                text=True, env=dict(os.environ))
        after = json.loads(result.stdout)['installation']
        self.assertEqual(after['action'], 'upgraded')
        self.assertEqual(after['installationId'], before['installationId'])
        self.assertEqual(after['previousReleaseId'], before['releaseId'])
        self.assertEqual(after['releaseId'], 'truss-catalog-runtime/0.31-candidate')
        self.assertRegex(after['releaseSha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(after['layoutProfile']['version'], '0.16')
        self.assertEqual(after['catalogRevision'], 0)
        self.assertFalse((directory / 'postmaster.pid').exists())
        shutil.rmtree(parent)
