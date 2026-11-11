# SPDX-License-Identifier: MIT OR Apache-2.0
"""Qualification driver sensitivity only; no native server or build is started."""
import importlib.util
import ast
from contextlib import nullcontext
import base64
import os
import zlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from temporal_qualification_support import collect_exact,strict_result,RecordedResult,OwnedNativeCleanup

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('temporal_qualification_driver',ROOT/'scripts/qualify-temporal-native.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)


class TemporalQualificationDriverTests(unittest.TestCase):
    def result(self,n=2):
        result=unittest.TestResult();result.testsRun=n;return result

    def cleanup_import_stub(self):
        class LocalPostgres:
            def __enter__(self):return self
            def close(self):return None
        module=types.ModuleType('truss');module.LocalPostgres=LocalPostgres
        return patch.dict(sys.modules,{'truss':module})

    def test_exact_case_counts_zero_skip_xfail_xpass_and_inventory_cleanup_required(self):
        expected=['one','two'];result=self.result()
        self.assertTrue(strict_result(result,expected,expected,inventory_verified=True,cleanup_confirmed=True)['passed'])
        for name in ('skipped','expectedFailures','unexpectedSuccesses','failures','errors'):
            result=self.result();getattr(result,name).append(('case','detail'))
            with self.subTest(field=name):self.assertFalse(strict_result(result,expected,expected,inventory_verified=True,cleanup_confirmed=True)['passed'])
        for expected,observed,n,inventory,cleanup in ((['one','two'],['two','one'],2,True,True),
                (['one','two'],['one'],1,True,True),(['one','one'],['one','one'],2,True,True),
                ([],[],0,True,True),(['one','two'],['one','two'],2,False,True),(['one','two'],['one','two'],2,True,False)):
            with self.subTest(expected=expected,observed=observed):
                self.assertFalse(strict_result(self.result(n),expected,observed,inventory_verified=inventory,cleanup_confirmed=cleanup)['passed'])

    def test_collection_refuses_module_class_expansion_duplicates_or_missing_case(self):
        name='temporal_driver_unit_fixture';module=types.ModuleType(name)
        class UnitCase(unittest.TestCase):
            def test_one(self):pass
            def test_two(self):pass
        UnitCase.__module__=name;UnitCase.__qualname__='UnitCase';module.UnitCase=UnitCase
        with patch.dict(sys.modules,{name:module}):
            selector=name+'.UnitCase.test_one'
            self.assertEqual(collect_exact([selector]).countTestCases(),1)
            for invalid in ([name],[name+'.UnitCase'],[selector,selector],[name+'.UnitCase.missing']):
                with self.subTest(invalid=invalid),self.assertRaises(ValueError):collect_exact(invalid)

    def test_governed_census_preserves_original_hf_cases_and_ordinary_overlap_only_once(self):
        selected=driver.ledger();self.assertEqual(sum(selected['expectedCounts'].values()),130)
        self.assertEqual(selected['expectedCounts']['journal'],10)
        self.assertEqual(sum(v for k,v in selected['expectedCounts'].items() if k not in ('journal','public55')),119)
        self.assertEqual(selected['expectedCounts']['public55'],1)
        original=json.loads((ROOT/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
        self.assertEqual([(r['id'],r['test']) for r in selected['stages']['hf']],[(r['id'],r['test']) for r in original['cases']])
        self.assertEqual(len(selected['ordinaryCoveredOnceByHF']),3)
        self.assertTrue(set(selected['ordinaryCoveredOnceByHF'])<={r['test'] for r in selected['stages']['hf']})
        self.assertFalse(set(selected['ordinaryCoveredOnceByHF'])&{r['test'] for r in selected['stages']['ordinary']})

    def test_isolated_fixture_delete_requires_status3_and_original_pid_absent_before_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'owned';data=root/'data';data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
            output=Path(directory)/'cleanup.json';monitor=OwnedNativeCleanup([],output);events=[]
            monitor.records[str(data.resolve())]={'dataDirectory':str(data.resolve()),'pgCtl':'/unit/pg_ctl','originalPostmasterPid':42,'confirmed':False,'dataDeleted':False}
            def status(*args,**kw):events.append('status');self.assertTrue(data.exists());return subprocess.CompletedProcess(args[0],3,'not running','')
            def absent(pid,signal):events.append('original-pid');self.assertTrue(data.exists());raise ProcessLookupError()
            with self.cleanup_import_stub(),patch('temporal_qualification_support.subprocess.run',side_effect=status),patch('temporal_qualification_support.os.kill',side_effect=absent),monitor:
                shutil.rmtree(root)
            self.assertEqual(events,['status','original-pid']);self.assertFalse(root.exists());self.assertTrue(monitor.confirmed)
            proof=json.loads(output.read_bytes())['clusters'][0]
            self.assertEqual((proof['pgCtlStatus'],proof['originalPostmasterPidAbsent'],proof['dataDeleted']),(3,True,True))

    def test_original_pid_is_captured_before_owned_close_stops_cluster(self):
        with tempfile.TemporaryDirectory() as directory:
            data=Path(directory)/'data';data.mkdir();(data/'PG_VERSION').write_text('18');(data/'postmaster.pid').write_text('314\n')
            events=[];monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
            class LocalPostgres:
                def __enter__(self):events.append(('start',));return self
                def close(self):
                    if not monitor.records or next(iter(monitor.records.values()))['originalPostmasterPid']!=314:
                        raise AssertionError('Original PID was not captured before stop')
                    events.append(('stop',));return None
            LocalPostgres.directory=data;LocalPostgres.psql_path=Path('/unit/bin/psql')
            module=types.ModuleType('truss');module.LocalPostgres=LocalPostgres
            with patch.dict(sys.modules,{'truss':module}), \
                 patch('temporal_qualification_support.subprocess.run',side_effect=lambda *a,**k:subprocess.CompletedProcess(a[0],3,'','')), \
                 patch('temporal_qualification_support.os.kill',side_effect=ProcessLookupError),monitor:
                runtime=LocalPostgres();runtime.__enter__();runtime.close()
            self.assertEqual(events,[('start',),('stop',)])
            self.assertEqual(next(iter(monitor.records.values()))['originalPostmasterPid'],314)

    def test_missing_or_malformed_original_pid_fails_closed_and_retains_cluster(self):
        for contents in (None,'not-a-pid\n','0\n'):
            with self.subTest(contents=contents),tempfile.TemporaryDirectory() as directory:
                data=Path(directory)/'data';data.mkdir();(data/'PG_VERSION').write_text('18')
                if contents is not None:(data/'postmaster.pid').write_text(contents)
                monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
                with self.assertRaisesRegex(RuntimeError,'retain data'):
                    monitor.capture(data,Path('/unit/bin'))
                self.assertTrue(data.exists());self.assertFalse(monitor.confirmed)
                self.assertTrue(monitor.uncertain)

    def test_empty_cleanup_ledger_cannot_pass_or_delete_an_owned_cluster(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'owned';data=root/'data';data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
            monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
            self.assertFalse(monitor.confirmed)
            with self.cleanup_import_stub(),monitor,self.assertRaisesRegex(RuntimeError,'Unobserved PG'):
                shutil.rmtree(root)
            self.assertTrue(data.exists());self.assertFalse(monitor.confirmed)

    def test_missing_pid_in_mixed_clusters_keeps_campaign_cleanup_unconfirmed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);owned=root/'owned';data=owned/'data';data.mkdir(parents=True)
            (data/'PG_VERSION').write_text('18');(data/'postmaster.pid').write_text('2718\n')
            missing=root/'missing';missing.mkdir();(missing/'PG_VERSION').write_text('18')
            monitor=OwnedNativeCleanup([],root/'cleanup.json')
            def absent(pid,signal):self.assertEqual(pid,2718);raise ProcessLookupError()
            with self.cleanup_import_stub(), \
                 patch('temporal_qualification_support.subprocess.run',return_value=subprocess.CompletedProcess([],3,'','')), \
                 patch('temporal_qualification_support.os.kill',side_effect=absent),monitor:
                monitor.capture(data,Path('/unit/bin'))
                # Simulate the original postmaster's removal of its PID file.
                (data/'postmaster.pid').unlink()
                shutil.rmtree(owned)
                with self.assertRaisesRegex(RuntimeError,'retain data'):
                    monitor.capture(missing,Path('/unit/bin'))
            record=next(iter(monitor.records.values()))
            self.assertTrue(record['confirmed'] and record['dataDeleted'])
            self.assertFalse(monitor.confirmed)
            proof=json.loads((root/'cleanup.json').read_bytes())
            self.assertEqual(proof['clusters'][0]['originalPostmasterPid'],2718)
            self.assertEqual(proof['uncertainPaths'][0]['dataDirectory'],str(missing.resolve()))
            self.assertTrue(missing.exists())
            self.assertFalse(monitor.confirmed)


    def test_driver_test_class_has_no_shadowed_method_definitions(self):
        source=Path(__file__).read_text(encoding='utf-8')
        tree=ast.parse(source,filename=str(Path(__file__)))
        for node in ast.walk(tree):
            if isinstance(node,ast.ClassDef):
                methods=[child.name for child in node.body if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef))]
                duplicates=sorted({name for name in methods if methods.count(name)>1})
                self.assertFalse(duplicates,f'{node.name} has shadowed methods: {duplicates}')

    def test_unknown_pg_directory_is_retained_without_claiming_observed_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'owned';data=root/'data';data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
            monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
            with self.cleanup_import_stub(),monitor,self.assertRaisesRegex(RuntimeError,'Unobserved PG'):
                shutil.rmtree(root)
            self.assertTrue(data.exists());self.assertFalse(monitor.confirmed)

    def test_live_or_uncertain_original_pid_never_allows_delete(self):
        for code,pid_error in ((0,ProcessLookupError()),(3,None),(3,PermissionError())):
            with self.subTest(code=code,pidError=type(pid_error).__name__),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)/'owned';data=(root/'data').resolve();data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
                monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
                monitor.records[str(data)]={'dataDirectory':str(data),'pgCtl':'/unit/pg_ctl','originalPostmasterPid':42,'confirmed':False,'dataDeleted':False}
                with patch('temporal_qualification_support.subprocess.run',return_value=subprocess.CompletedProcess([],code,'','')), \
                     patch('temporal_qualification_support.os.kill',side_effect=pid_error),self.cleanup_import_stub(),self.assertRaises(RuntimeError):
                    with monitor:shutil.rmtree(root)
                self.assertTrue(data.exists());self.assertFalse(monitor.confirmed)

    def test_missing_actual_artifact_enrollment_refuses_before_runtime_initialization(self):
        import release_cohort
        from truss import LocalPostgres
        selected=release_cohort.load_cohort();selected['qualified']=None
        original=release_cohort.load_cohort
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'unsealed.json';path.write_text(json.dumps(selected))
            def unsealed(*args,**kwargs):return original(path,**kwargs)
            with patch.object(driver,'assert_qualification_checkout',return_value={}),patch.object(release_cohort,'load_cohort',side_effect=unsealed),patch.object(driver.sys,'platform','linux'),patch.object(driver.platform,'machine',return_value='x86_64'), \
                 patch.object(LocalPostgres,'__enter__') as started, \
                 self.assertRaisesRegex(ValueError,'identities deferred'):
                driver.preflight({'schema':'truss-temporal-qualification-input/1'})
            started.assert_not_called()

    def test_public055_fixture_is_bound_to_immutable_publication_and_original_runtime_constraints(self):
        from test_temporal_public055_refusal_native import provenance,PUBLIC055_WHEEL_SHA256,PUBLIC055_NATIVE_SHA256
        selected=provenance()
        publication=json.loads((ROOT/selected['publishedProof']).read_bytes())
        wheel=next(row for row in publication['assets'] if row['name']==selected['wheelFilename'])
        self.assertEqual(wheel['sha256'],PUBLIC055_WHEEL_SHA256)
        self.assertEqual(wheel['bytes'],selected['wheelBytes'])
        self.assertTrue(publication['release']['is_immutable'])
        self.assertEqual(selected['nativeManifestSHA256'],PUBLIC055_NATIVE_SHA256)
        self.assertEqual(selected['requestedExtras'],['local','native'])
        self.assertEqual(selected['constraintsSHA256'],'cbc86dce6b1241d367798d37d5eebfab436b477b5e1c5bc27b12c1bbcdcf2889')
        self.assertEqual(len(selected['dependencyPins311Linux']),13)
        self.assertFalse(set(selected['dependencyPins311Linux'])&set(selected['forbiddenOwnerDistributions']))
        self.assertEqual(selected['dependencyPins311Linux']['mini-racer'],'0.14.1')

    def test_public055_seed_retains_original_api_sequence_except_bounded_install_keyword(self):
        import ast
        import copy
        original=ast.parse((ROOT/'packages/python/tests/runtime_migration_fixture.py').read_text())
        authored=ast.parse((ROOT/'packages/python/tests/public055_seed_fixture.py').read_text())
        before=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='seed')
        after=copy.deepcopy(next(n for n in authored.body if isinstance(n,ast.FunctionDef) and n.name=='seed'))
        installation=[n for n in ast.walk(after) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='install_in_transaction']
        self.assertEqual(len(installation),1)
        self.assertEqual([(k.arg,ast.literal_eval(k.value)) for k in installation[0].keywords],[('operation_timeout_ms',180000)])
        installation[0].keywords=[]
        self.assertEqual(ast.dump(before,include_attributes=False),ast.dump(after,include_attributes=False))

    def test_public055_snapshot_retains_full_acl_names_without_changing_public054(self):
        from unittest.mock import MagicMock
        from test_temporal_public055_refusal_native import TemporalPublic055RefusalTests
        from test_temporal_catalog_transport_native import TemporalCatalogTransportTests
        from truss import _migration_verify
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        prefix='same_native_routine_'+('x'*70)
        full=[['routine',prefix+'(text,integer)','EXECUTE'],['routine',prefix+'(text,bigint)','EXECUTE']]
        original={'tables':{'retained':'exact source'},'acl':[['routine',prefix[:63],'EXECUTE']]}
        case=TemporalPublic055RefusalTests('test_public55_populated_installation_refuses_candidate_without_effects')
        with patch.object(TemporalCatalogTransportTests,'snapshot',return_value=dict(original)),patch.object(_migration_verify,'acl',return_value=full) as observed:
            actual=case.snapshot(connection)
        observed.assert_called_once_with(cursor,full_names=True)
        self.assertEqual(actual['acl'],full);self.assertEqual(actual['tables'],original['tables'])
        before=subprocess.check_output(['git','show','6e2a38e66fd6322bd04a86cb49898b48b9ef5dbf:packages/python/tests/test_temporal_catalog_transport_native.py'],cwd=ROOT)
        self.assertEqual((ROOT/'packages/python/tests/test_temporal_catalog_transport_native.py').read_bytes(),before)


# Read-only fixture bytes from the stopped, retained PostgreSQL 18.6 cluster.
# The control flow below uses stubbed stop/status/PID and never opens a server.
_AUTHENTIC_RELMAP = zlib.decompress(base64.b64decode(
    'eJwTV49kEGRgYHjNAsEPofg5FN+HYhFuCBaFYm8BCPaB4iYuCG6G4n4ongDFSVCcDMVpUJwOxfW8'
    'EDwKBgZ8+rbqPgAcXBZu'
))
_AUTHENTIC_CONTROL = zlib.decompress(base64.b64decode(
    'eJzbZ65+hP/s5ywOdgYGYwYhHkYGCBAEioHoHzKFjMg0Ixr+wARRn2wM4YPACyZUNcjmoYMXzNhE'
    'sQOYWSlAzAHEXFC+A5TmgNLt14wcGRRALKBDFCBaQWpAzDPsEIVw9+k6R6W4/AldPLf8T7GeR+hO'
    'OUHFOS+Uei5J+67+rPgndAZQjWqohjDxrhwFo2AUjIJRMApGwSgYBaNgFIyCUTAKRsEoGAWjYBSM'
    'glEwCkbBKBgFo2AUjIJRMAroDwBavyL4'
))


class OwnedDatabaseLayoutTests(unittest.TestCase):
    def make_owned(self, root, name='owned'):
        data = root / name
        data.mkdir()
        (data / 'PG_VERSION').write_bytes(b'18\n')
        socket = root / 'socket'
        socket.mkdir()
        pid = b'314\n' + os.fsencode(data) + b'\n1700000000\n5432\n' + os.fsencode(socket) + b'\n'
        (data / 'postmaster.pid').write_bytes(pid)
        (socket / '.s.PGSQL.5432.lock').write_bytes(pid)
        (data / 'global').mkdir()
        (data / 'global/pg_control').write_bytes(_AUTHENTIC_CONTROL)
        for oid in ('1', '4', '5'):
            database = data / 'base' / oid
            database.mkdir(parents=True)
            (database / 'PG_VERSION').write_bytes(b'18\n')
            (database / 'pg_filenode.map').write_bytes(_AUTHENTIC_RELMAP)
            # The relation file is a stub. Its filename comes from the real map.
            (database / '1259').write_bytes(b'relation fixture')
        return data

    def controls(self, data, oids=None):
        socket = data.parent / 'socket'
        if oids is None:
            oids = ['1', '4', '5']
        module = types.ModuleType('truss')
        class LocalPostgres:
            directory = data
            psql_path = Path('/unit/bin/psql')
            info = types.SimpleNamespace(socket_directory=socket, server_version='18.6')
            _info = info

            def __enter__(self):
                return self

            def close(self):
                (data / 'postmaster.pid').unlink()
        module.LocalPostgres = LocalPostgres
        def status(argv, **kwargs):
            if argv[0] == '/unit/bin/psql':
                self.assertIn(str(socket), argv)
                self.assertIn('FROM pg_catalog.pg_database', argv[-1])
                self.assertIn('default_transaction_read_only=on', kwargs['env']['PGOPTIONS'])
                self.assertTrue((data / 'postmaster.pid').is_file())
                result = {'data': str(data), 'socket': str(socket), 'port': '5432',
                          'listen': '', 'unix': True, 'version': '180006', 'oids': oids}
                return subprocess.CompletedProcess(argv, 0, json.dumps(result), '')
            self.assertEqual(argv, ['/unit/bin/pg_ctl', '-D', str(data), 'status'])
            self.assertTrue(data.is_dir())
            return subprocess.CompletedProcess(argv, 3, 'not running', '')
        def absent(pid, signal):
            self.assertEqual((pid, signal), (314, 0))
            self.assertTrue(data.is_dir())
            if (data / 'postmaster.pid').exists():
                return
            raise ProcessLookupError
        return (module, status, absent)

    def test_authentic_per_database_markers_allow_owned_delete_after_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            data = self.make_owned(root)
            module, status, absent = self.controls(data)
            monitor = OwnedNativeCleanup([], root / 'cleanup.json')
            with patch.dict(sys.modules, {'truss': module}), \
                    patch('temporal_qualification_support.subprocess.run', side_effect=status), \
                    patch('temporal_qualification_support._socket_identity', return_value=[7, 8], create=True), \
                    patch('temporal_qualification_support.os.kill', side_effect=absent), monitor:
                runtime = module.LocalPostgres()
                runtime.__enter__()
                self.assertEqual(monitor.records[str(data)]['originalPostmasterPid'], 314)
                runtime.close()
                self.assertTrue(data.exists())
                shutil.rmtree(data)
            self.assertTrue(monitor.confirmed)
            record = json.loads((root / 'cleanup.json').read_bytes())['clusters'][0]
            self.assertEqual(set(record['databaseLayout']['databases']), {'1', '4', '5'})
            self.assertEqual((record['pgCtlStatus'], record['originalPostmasterPidAbsent'],
                              record['dataDeleted']), (3, True, True))

    def test_unobserved_or_changed_layout_retains_entire_requested_tree(self):
        cases = ('unknown sibling', 'nested marker', 'nested postmaster pid',
                 'nested postmaster opts', 'nested control', 'leading zero',
                 'non-ASCII OID', 'zero', 'uint32 overflow', 'wrong version',
                 'missing map', 'bad map CRC', 'wrong root PID binding',
                 'database identity', 'root identity', 'new legitimate-looking OID',
                 'copied valid OID before capture', 'unlisted added before close', 'socket lock mismatch',
                 'symlink marker', 'symlink database', 'symlink base',
                 'symlink deletion target', 'symlink ancestor', 'dir_fd', 'partial root')
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                scratch = Path(tmp).resolve()
                root = scratch / 'requested'
                root.mkdir()
                data = self.make_owned(root)
                db = data / 'base/1'
                target = root
                flags = {}
                if case in ('leading zero', 'non-ASCII OID', 'zero', 'uint32 overflow'):
                    name = {'leading zero': '01', 'non-ASCII OID': '١', 'zero': '0',
                            'uint32 overflow': '4294967296'}[case]
                    db.rename(db.with_name(name))
                elif case == 'wrong version':
                    (db / 'PG_VERSION').write_bytes(b'17\n')
                elif case == 'missing map':
                    (db / 'pg_filenode.map').unlink()
                elif case == 'bad map CRC':
                    (db / 'pg_filenode.map').write_bytes(_AUTHENTIC_RELMAP[:-1] + bytes([_AUTHENTIC_RELMAP[-1] ^ 1]))
                elif case == 'wrong root PID binding':
                    (data / 'postmaster.pid').write_bytes(b'314\n/other\n')
                elif case == 'copied valid OID before capture':
                    shutil.copytree(db, db.with_name('9'))
                elif case == 'socket lock mismatch':
                    (root / 'socket/.s.PGSQL.5432.lock').write_bytes(b'99\n')

                module, status, absent = self.controls(data)
                monitor = OwnedNativeCleanup([], scratch / 'cleanup.json')
                with patch.dict(sys.modules, {'truss': module}), \
                        patch('temporal_qualification_support.subprocess.run', side_effect=status), \
                    patch('temporal_qualification_support._socket_identity', return_value=[7, 8], create=True), \
                        patch('temporal_qualification_support.os.kill', side_effect=absent), monitor:
                    runtime = module.LocalPostgres()
                    runtime.__enter__()
                    if case == 'unlisted added before close':
                        shutil.copytree(db, db.with_name('9'))
                    runtime.close()
                    if case in ('copied valid OID before capture', 'unlisted added before close'):
                        self.assertIn('Unregistered PostgreSQL database directory',
                                      monitor.records[str(data)]['layoutUncertain'])
                        self.assertFalse((data / 'postmaster.pid').exists())
                    if case == 'unknown sibling':
                        sibling = root / 'sibling'
                        sibling.mkdir()
                        (sibling / 'PG_VERSION').write_bytes(b'18\n')
                    elif case.startswith('nested'):
                        relative = {'nested marker': 'nested/PG_VERSION',
                                    'nested postmaster pid': 'postmaster.pid',
                                    'nested postmaster opts': 'postmaster.opts',
                                    'nested control': 'global/pg_control'}[case]
                        marker = db / relative
                        marker.parent.mkdir(exist_ok=True)
                        marker.write_bytes(b'18\n')
                    elif case == 'database identity':
                        db.rename(scratch / 'original-db')
                        shutil.copytree(scratch / 'original-db', db)
                    elif case == 'root identity':
                        data.rename(scratch / 'original-root')
                        shutil.copytree(scratch / 'original-root', data)
                    elif case == 'new legitimate-looking OID':
                        shutil.copytree(db, db.with_name('9'))
                    elif case == 'symlink marker':
                        (db / 'PG_VERSION').unlink()
                        (db / 'PG_VERSION').symlink_to(data / 'PG_VERSION')
                    elif case == 'symlink database':
                        db.rename(scratch / 'original-db')
                        db.symlink_to(scratch / 'original-db', target_is_directory=True)
                    elif case == 'symlink base':
                        (data / 'base').rename(scratch / 'original-base')
                        (data / 'base').symlink_to(scratch / 'original-base', target_is_directory=True)
                    elif case == 'symlink deletion target':
                        target = scratch / 'root-alias'
                        target.symlink_to(root, target_is_directory=True)
                    elif case == 'symlink ancestor':
                        alias = scratch / 'root-alias'
                        alias.symlink_to(root, target_is_directory=True)
                        target = alias / 'owned'
                    elif case == 'dir_fd':
                        flags = {'dir_fd': -1}
                    elif case == 'partial root':
                        target = data / 'base'
                    if case == 'symlink deletion target':
                        with self.assertRaises(OSError):
                            shutil.rmtree(target)
                        self.assertTrue(target.is_symlink())
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'retained|retain data'):
                            shutil.rmtree(target, **flags)
                        self.assertTrue(monitor.uncertain)
                self.assertTrue(data.exists())
                self.assertTrue(root.exists())
                self.assertFalse(monitor.confirmed)


    def test_authoritative_refresh_admits_database_created_after_enter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            data = self.make_owned(root)
            oids = ['1', '4', '5']
            module, status, absent = self.controls(data, oids)
            monitor = OwnedNativeCleanup([], root / 'cleanup.json')
            with patch.dict(sys.modules, {'truss': module}), \
                    patch('temporal_qualification_support._socket_identity', return_value=[7, 8]), \
                    patch('temporal_qualification_support.subprocess.run', side_effect=status), \
                    patch('temporal_qualification_support.os.kill', side_effect=absent), monitor:
                runtime = module.LocalPostgres()
                runtime.__enter__()
                shutil.copytree(data / 'base/1', data / 'base/9')
                oids.append('9')
                runtime.close()
                shutil.rmtree(data)
            self.assertTrue(monitor.confirmed)
            self.assertEqual(set(monitor.records[str(data)]['databaseLayout']['databases']),
                             {'1', '4', '5', '9'})

    def test_raw_capture_without_trusted_socket_retains_even_genuine_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            data = self.make_owned(root)
            module, status, absent = self.controls(data)
            monitor = OwnedNativeCleanup([], root / 'cleanup.json')
            with patch.dict(sys.modules, {'truss': module}), \
                    patch('temporal_qualification_support.subprocess.run', side_effect=status), \
                    patch('temporal_qualification_support.os.kill', side_effect=absent), monitor:
                monitor.capture(data, Path('/unit/bin'))
                (data / 'postmaster.pid').unlink()
                monitor.confirm(monitor.records[str(data)])
                with self.assertRaisesRegex(RuntimeError, 'socket authority unavailable'):
                    shutil.rmtree(data)
            self.assertTrue(data.is_dir())

    def test_ordinary_rmtree_preserves_missing_path_and_unlinks_nested_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            outside = self.make_owned(root)
            ordinary = root / 'ordinary'
            ordinary.mkdir()
            (ordinary / 'link').symlink_to(outside, target_is_directory=True)
            direct = root / 'direct'
            direct.symlink_to(outside, target_is_directory=True)
            with TemporalQualificationDriverTests().cleanup_import_stub(), OwnedNativeCleanup([], root / 'cleanup.json'):
                shutil.rmtree(root / 'missing', ignore_errors=True)
                with self.assertRaises(FileNotFoundError):
                    shutil.rmtree(root / 'missing')
                shutil.rmtree(direct, ignore_errors=True)
                self.assertTrue(direct.is_symlink())
                shutil.rmtree(ordinary)
            self.assertTrue((outside / 'postmaster.pid').is_file())
            self.assertFalse(ordinary.exists())

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS system temp alias')
    def test_platform_temp_alias_joins_owned_runtime_and_original_rmtree_path(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            root = Path(tmp)
            canonical = root.resolve()
            data = self.make_owned(canonical)
            module, status, absent = self.controls(data)
            monitor = OwnedNativeCleanup([], canonical / 'cleanup.json')
            with patch.dict(sys.modules, {'truss': module}), \
                    patch('temporal_qualification_support._socket_identity', return_value=[7, 8]), \
                    patch('temporal_qualification_support.subprocess.run', side_effect=status), \
                    patch('temporal_qualification_support.os.kill', side_effect=absent), monitor:
                runtime = module.LocalPostgres()
                runtime.__enter__()
                runtime.close()
                shutil.rmtree(root / 'owned')
            self.assertTrue(monitor.confirmed)

    def test_noncanonical_paths_refuse_before_ancestry_or_stop_for_live_owned_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            data = self.make_owned(root)
            unmarked = data / 'base/1/unmarked'
            unmarked.mkdir()
            (unmarked / 'keep').write_bytes(b'live data')
            module, status, absent = self.controls(data)
            monitor = OwnedNativeCleanup([], root / 'cleanup.json')
            with patch.dict(sys.modules, {'truss': module}), \
                    patch('temporal_qualification_support._socket_identity', return_value=[7, 8]), \
                    patch('temporal_qualification_support.subprocess.run', side_effect=status) as calls, \
                    patch('temporal_qualification_support.os.kill', side_effect=absent) as signals, monitor:
                runtime = module.LocalPostgres()
                runtime.__enter__()
                calls.reset_mock()
                signals.reset_mock()
                for path, options in (('/' + str(unmarked), {}),
                                      (data / 'base/1/../1/unmarked', {}),
                                      (Path('base/1/unmarked'), {}),
                                      (unmarked, {'dir_fd': -1})):
                    with self.subTest(path=path), patch.object(
                            monitor, '_deletion_roots', wraps=monitor._deletion_roots) as ancestry:
                        with self.assertRaisesRegex(RuntimeError, 'Ambiguous'):
                            shutil.rmtree(path, ignore_errors=True, **options)
                        ancestry.assert_not_called()
                        calls.assert_not_called()
                        signals.assert_not_called()
                        self.assertEqual((unmarked / 'keep').read_bytes(), b'live data')
                        self.assertTrue((data / 'postmaster.pid').is_file())
                runtime.close()
            self.assertTrue(unmarked.is_dir())

    def test_physical_case_alias_refuses_owned_descendant_and_enclosing_root_before_stop(self):
        import temporal_qualification_support as support

        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp).resolve()
            root = scratch / 'OwnedContainer'
            root.mkdir()
            data = self.make_owned(root)
            unmarked = data / 'base/1/unmarked'
            unmarked.mkdir()
            (unmarked / 'keep').write_bytes(b'live data')
            aliased_data = root / 'OWNED'
            aliased_enclosing = scratch / 'ownedcontainer'
            actual_case_aliases = aliased_data.exists() and aliased_enclosing.exists()
            identity_mock = nullcontext()
            if actual_case_aliases:
                self.assertTrue(aliased_data.samefile(data))
                self.assertTrue(aliased_enclosing.samefile(root))
            else:
                # Exercise the same physical-overlap branch on case-sensitive
                # filesystems without depending on a second mount or native PG.
                shutil.copytree(data, aliased_data)
                aliased_enclosing.mkdir()
                directory_identity = support._directory_identity
                aliases = {aliased_data: data, aliased_enclosing: root}
                identity_mock = patch.object(support, '_directory_identity', side_effect=lambda path:
                                             directory_identity(aliases.get(path, path)))
            module, status, absent = self.controls(data)
            monitor = OwnedNativeCleanup([], scratch / 'cleanup.json')
            with patch.dict(sys.modules, {'truss': module}), \
                    patch.object(support, '_socket_identity', return_value=[7, 8]), \
                    patch.object(support.subprocess, 'run', side_effect=status) as calls, \
                    patch.object(support.os, 'kill', side_effect=absent) as signals, monitor:
                runtime = module.LocalPostgres()
                runtime.__enter__()
                calls.reset_mock()
                signals.reset_mock()
                with identity_mock, patch.object(monitor, '_check_deletion_tree',
                                                  wraps=monitor._check_deletion_tree) as scan:
                    for target in (aliased_data / 'base/1/unmarked', aliased_enclosing):
                        with self.subTest(target=target, actual_case_aliases=actual_case_aliases):
                            with self.assertRaisesRegex(RuntimeError, 'Physical alias'):
                                shutil.rmtree(target, ignore_errors=True)
                            self.assertTrue(target.is_dir())
                            self.assertEqual((unmarked / 'keep').read_bytes(), b'live data')
                            self.assertTrue((data / 'postmaster.pid').is_file())
                            scan.assert_not_called()
                            calls.assert_not_called()
                            signals.assert_not_called()
                runtime.close()
            self.assertTrue(root.is_dir())
