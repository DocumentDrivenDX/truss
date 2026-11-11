# SPDX-License-Identifier: MIT OR Apache-2.0
"""Synthetic pure sensitivity tests. NO installed/native TN-14 qualification."""
import copy
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import shutil
import types
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('public_tn14_unit', ROOT / 'scripts/verify_published_temporal_consumer.py')
consumer = importlib.util.module_from_spec(spec); spec.loader.exec_module(consumer)
spec = importlib.util.spec_from_file_location('cleanup_tn14_unit', ROOT / 'scripts/temporal_qualification_support.py')
cleanup = importlib.util.module_from_spec(spec); spec.loader.exec_module(cleanup)


class PublicTemporalConsumerPureTests(unittest.TestCase):
    def test_missing_publication_refuses_before_owner_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            publication = root / 'publication.json'; publication.write_text('{}')
            with patch.object(consumer.importlib, 'import_module', side_effect=AssertionError('owner import')):
                with self.assertRaisesRegex(ValueError, 'public byte'):
                    consumer.preflight(root, publication, root, root)

    def test_publication_and_prerequisite_failure_never_reaches_install_or_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); output = root / 'result'
            with patch.object(consumer, 'preflight', side_effect=ValueError('missing original prerequisite')), \
                 patch.object(consumer, 'install_public', side_effect=AssertionError('install')), \
                 patch.object(consumer, 'run_native', side_effect=AssertionError('native')), \
                 patch.object(consumer.sys, 'platform', 'linux'):
                with self.assertRaisesRegex(ValueError, 'prerequisite'):
                    consumer.main(['--assets', str(root), '--publication', str(root/'publication'),
                                   '--source', str(root/'source'), '--output', str(output)])
                self.assertEqual(json.loads((output/'public-tn14-receipt.json').read_bytes())['status'], 'failed')

    def origins(self):
        cohort = {owner: dict(distribution=name, version='1.0') for owner, name in
                  [('truss', 'umf-truss'), ('core', 'umf-core'), ('access', 'umf_access'), ('weft', 'umf-weft')]}
        hashes = {owner: str(index+1)*64 for index, owner in enumerate(cohort)}
        rows = [dict(metadata=dict(name=entry['distribution'], version='1.0'), download_info=dict(
            url='https://files.pythonhosted.org/packages/'+entry['distribution']+'.whl',
            archive_info=dict(hashes=dict(sha256=hashes[owner])))) for owner, entry in cohort.items()]
        runtime = dict(distribution='pgserver-pg18', version='18.6.1', path='/unit/public-runtime.whl', sha256='a'*64)
        rows.append(dict(metadata=dict(name='pgserver-pg18', version='18.6.1'), download_info=dict(
            url='file:///unit/public-runtime.whl', archive_info=dict(hashes=dict(sha256='a'*64)))))
        return dict(install=rows), cohort, hashes, runtime

    def test_normal_public_resolver_and_exact_runtime_exception(self):
        report, cohort, hashes, runtime = self.origins()
        self.assertEqual(len(consumer.validate_origins(report, cohort, hashes, runtime)), 5)

    def test_private_source_local_and_owner_substitution_refuse(self):
        for change in ('private', 'source', 'local', 'owner-version', 'owner-hash', 'runtime-path', 'runtime-hash', 'runtime-name'):
            report, cohort, hashes, runtime = self.origins()
            item = report['install'][0]; info = item['download_info']
            if change == 'private': info['url'] = 'https://private.example/a.whl'
            if change == 'source': info['url'] = 'https://files.pythonhosted.org/a.tar.gz'
            if change == 'local': info['url'] = 'file:///unit/owner.whl'
            if change == 'owner-version': item['metadata']['version'] = '2.0'
            if change == 'owner-hash': info['archive_info']['hashes']['sha256'] = 'f'*64
            if change == 'runtime-path': report['install'][-1]['download_info']['url'] = 'file:///unit/another.whl'
            if change == 'runtime-hash': report['install'][-1]['download_info']['archive_info']['hashes']['sha256'] = 'f'*64
            if change == 'runtime-name': report['install'][-1]['metadata']['name'] = 'another-runtime'
            with self.subTest(change=change), self.assertRaises(ValueError):
                consumer.validate_origins(report, cohort, hashes, runtime)

    def test_each_temporal_type_and_value_is_independent(self):
        expected = consumer.expected_rows()
        consumer.assert_rows(expected, expected)
        for column, value in ((0, datetime(2024,1,1)), (1, datetime(2024,1,1)),
                              (2, datetime(2024,2,29,tzinfo=timezone.utc)), (1, '2024-01-01'),
                              (2, datetime(2024,2,29))):
            actual = list(expected); actual[0] = tuple(value if i == column else old for i, old in enumerate(actual[0]))
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                consumer.assert_rows(actual, expected)
        with self.assertRaises(ValueError): consumer.assert_rows(expected[:-1], expected)

    def test_hidden_full_key_boundaries_and_repeated_prefix_completeness(self):
        expected = consumer.expected_rows()
        metadata = dict(keyOutputPositions=[1,2], visibleOutputPositions=[0])
        pages = [(expected[:2], b'one'), (expected[2:4], b'two'), (expected[4:], None)]
        consumer.assert_pages(metadata, pages, expected)
        mutations = [({'keyOutputPositions':[1], 'visibleOutputPositions':[0]}, pages),
            ({'keyOutputPositions':[1,1], 'visibleOutputPositions':[0]}, pages),
            ({'keyOutputPositions':[0,1], 'visibleOutputPositions':[0,1]}, pages),
            (metadata, pages[:2]), (metadata, [(expected[:2],b'one'),(expected[:2],b'two'),(expected[4:],None)]), (metadata, [(expected[:2], b'one'),(expected[2:4],b'one'),(expected[4:],None)]),
            (metadata, [(expected[:2], b'one'),(expected[2:4],b'two'),(expected[4:],b'never-ended')])]
        for meta, batches in mutations:
            with self.subTest(meta=meta,batches=batches), self.assertRaises(ValueError):
                consumer.assert_pages(meta,batches,expected)

    def replay(self):
        document = NS(content=b'original authored document')
        inspection = {'actual':'owner inspection'}
        archive = [dict(originalText=document.content.decode(), validation=dict(inspection=inspection))]
        declarations = [dict(records=[dict(fields=[dict(declaration=dict(scalarType='timestamp'), nativeDescriptor=dict(nativeScalarType='localTimestamp'))])])]
        prepared = NS(input_bytes=b'input', archive_documents_bytes=json.dumps(archive).encode(), declarations_bytes=json.dumps(declarations).encode())
        summary = dict(sourceFormat='truss-registration-summary/2.1', documentValidations=[dict(inspection=inspection)])
        stored = (prepared.input_bytes, prepared.archive_documents_bytes, prepared.declarations_bytes, json.dumps(summary).encode())
        return prepared, document, stored, b'original report', NS(replayed=True, report_bytes=b'original report')

    def test_original_replay_inputs_retained_bytes_and_report(self):
        args = self.replay(); consumer.assert_replay(*args)
        for index in range(4):
            changed = list(args); stored = list(args[2]); stored[index] = b'{}'; changed[2] = tuple(stored)
            with self.subTest(index=index), self.assertRaises((ValueError,KeyError,TypeError)):
                consumer.assert_replay(*changed)
        for replay in (NS(replayed=False,report_bytes=b'original report'), NS(replayed=True,report_bytes=b'changed')):
            changed=list(args);changed[-1]=replay
            with self.assertRaises(ValueError): consumer.assert_replay(*changed)

    def test_missing_operations_kind_and_mixed_cleanup_never_qualify(self):
        operations = {name:dict(status='passed', kinds=list(consumer.KINDS)) for name in consumer.OPERATIONS}
        consumer.assert_operations(operations, NS(confirmed=True))
        for name in consumer.OPERATIONS:
            changed=copy.deepcopy(operations);changed.pop(name)
            with self.subTest(name=name),self.assertRaises(ValueError): consumer.assert_operations(changed,NS(confirmed=True))
        for name in ('write','import','typed-read'):
            for kind in consumer.KINDS:
                changed=copy.deepcopy(operations);changed[name]['kinds'].remove(kind)
                with self.subTest(name=name,kind=kind),self.assertRaises(ValueError): consumer.assert_operations(changed,NS(confirmed=True))
        with self.assertRaises(ValueError):consumer.assert_operations(operations,NS(confirmed=False))

    def fake_session(self):
        class Ok:
            def __init__(self,value):self.value=value
        class GroupSuccess:
            def __init__(self):self.response=NS(semantic=NS(results=[NS(outcome='created') for _ in range(3)]))
        class ImportCreated:pass
        class ImportReported:
            def __init__(self):self.report=NS(outcomes=[ImportCreated() for _ in range(3)],unprocessed_indices=())
        carrier=lambda **kwargs:NS(**kwargs)
        api=NS(truss=NS(Ok=Ok), groups=NS(GroupSuccess=GroupSuccess,RootlessOwnership=carrier,CreateObject=carrier,AuthoredValue=carrier),
            imports=NS(ImportReported=ImportReported,ImportCreated=ImportCreated),
            temporal=NS(CreateObject=carrier,AuthoredValue=carrier),contracts=NS(TextValue=carrier,LocalTimestampValue=carrier,MapValue=carrier))
        context=NS(input=Mock(return_value=NS()),request=Mock(return_value=NS()))
        selected=NS(group_context_in_transaction=Mock(return_value=Ok(context)),apply_in_transaction=Mock(return_value=Ok(GroupSuccess())),
            import_context_in_transaction=Mock(return_value=Ok(context)),object_import_record_in_transaction=Mock(side_effect=lambda *args,**kw:Ok(kw)),
            import_in_transaction=Mock(return_value=ImportReported()))
        assembly=NS(temporal_values=lambda:selected,get_type_reference_in_transaction=Mock(return_value=Ok(NS(definition_pin='real-pin'))),
            group_context_in_transaction=Mock(return_value=Ok(context)),apply_in_transaction=Mock(return_value=Ok(GroupSuccess())))
        @contextmanager
        def transaction():yield NS(),assembly,'tx'
        session=NS(api=api,transaction=transaction,ok=lambda result:result.value if isinstance(result,Ok) else self.fail('refusal'))
        return session,selected,context

    def test_actual_group_and_import_api_sequence_all_kinds(self):
        session,selected,context=self.fake_session()
        result=consumer.write_and_import(session,('original document',))
        self.assertEqual(result['write']['count'],3);self.assertEqual(result['import']['count'],3)
        self.assertEqual(selected.object_import_record_in_transaction.call_count,3)
        selected.group_context_in_transaction.assert_called_once_with('tx')
        selected.import_context_in_transaction.assert_called_once_with('tx')
        selected.apply_in_transaction.assert_called_once()
        self.assertEqual(selected.apply_in_transaction.call_args.kwargs['documents'],('original document',))
        selected.import_in_transaction.assert_called_once()
        for call in selected.object_import_record_in_transaction.call_args_list:
            supplied={item.name:item.value for item in call.kwargs['values']}
            self.assertEqual(supplied['A-instant'].kind,'timestamp');self.assertEqual(supplied['A-date'].kind,'date')
            self.assertTrue(supplied['A-local'].text.startswith('2024-02-29T12:00:'))
        operations=context.input.call_args_list[0].args[0]
        self.assertEqual(len(operations),3)
        self.assertEqual({item.name for item in operations[0].values}, {'A-label','A-value','A-date','A-instant','A-local','A-payload'})

    def test_missing_real_group_or_import_operation_refuses(self):
        for name in ('group_context_in_transaction','apply_in_transaction','import_context_in_transaction',
                     'object_import_record_in_transaction','import_in_transaction'):
            session,selected,context=self.fake_session();setattr(selected,name,Mock(side_effect=ValueError('missing operation')))
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'missing operation'):
                consumer.write_and_import(session,('original document',))

    def run_cleanup_fixture(self, outer, variant):
        # Reuse the authentic marker/map bytes and local socket-lock fixture
        # from the shared cleanup tests. No real backend or owner is imported.
        import test_temporal_qualification_driver as shared
        fixture = shared.OwnedDatabaseLayoutTests()
        root = outer / 'owned'
        root.mkdir()
        data = fixture.make_owned(root, name='data')
        output = outer / 'evidence'
        output.mkdir()
        oids = ['1', '4', '5']
        module, result, pid_probe = fixture.controls(data, oids)
        events = []
        if variant == 'copied before capture':
            shutil.copytree(data / 'base/1', data / 'base/9')
        elif variant == 'uncaptured':
            (data / 'PG_VERSION').unlink()
            (data / 'postmaster.pid').unlink()
        elif variant == 'wrong socket':
            (root / 'socket/.s.PGSQL.5432.lock').write_bytes(b'77\n')
        elif variant == 'missing base':
            shutil.rmtree(data / 'base')
        class Runtime(module.LocalPostgres):
            def __init__(self, requested):
                if requested != data:
                    raise AssertionError('TN-14 requested a different owner')

            def __enter__(self):
                events.append('start')
                return self

            def close(self):
                events.append('stop')
                if variant in ('retry stop', 'retry changed socket'):
                    if variant == 'retry changed socket':
                        (root / 'socket/.s.PGSQL.5432.lock').write_bytes(b'77\n')
                    raise RuntimeError('stub original stop failure')
                (data / 'postmaster.pid').unlink()
        module.LocalPostgres = Runtime
        module.CatalogDocument = lambda *_args: object()
        module.contracts = module.groups = module.imports = module.temporal = NS()
        calls = {'membership': 0}
        def process(argv, **kwargs):
            if argv[0].endswith('/psql'):
                calls['membership'] += 1
                events.append(('membership', tuple(oids)))
                if variant == 'refresh refusal' and calls['membership'] == 2:
                    return subprocess.CompletedProcess(argv, 1, '', 'stub query refusal')
            elif argv[-1] == 'stop':
                events.append('retry')
                self.assertEqual((data / 'postmaster.pid').read_text().splitlines()[0], '314')
                (data / 'postmaster.pid').unlink()
                return subprocess.CompletedProcess(argv, 0, 'stopped', '')
            else:
                events.append('status')
                self.assertFalse((data / 'postmaster.pid').exists())
            return result(argv, **kwargs)
        def observe_pid(pid, signal):
            if not (data / 'postmaster.pid').exists():
                events.append('pid absent')
            return pid_probe(pid, signal)

        def operations(names):
            items = {}
            for name in names:
                items[name] = {'status': 'passed', 'kinds': list(consumer.KINDS)}
                if variant != 'missing result' or name != 'ordinary-1.2':
                    (output / (name + '-result.json')).write_bytes(name.encode('ascii'))
            return items
        def first(*_args):
            if variant == 'late member':
                shutil.copytree(data / 'base/1', data / 'base/9')
                oids.append('9')
            elif variant == 'nested cluster':
                nested = data / 'base/1/nested'
                nested.mkdir()
                (nested / 'PG_VERSION').write_bytes(b'18\n')
                (nested / 'postmaster.pid').write_bytes(b'77\n')
            elif variant == 'mixed sibling':
                sibling = root / 'other'
                sibling.mkdir()
                (sibling / 'PG_VERSION').write_bytes(b'18\n')
            elif variant == 'wrong PID':
                (data / 'postmaster.pid').write_bytes(b'77\n')
            elif variant == 'replaced root':
                data.rename(outer / 'original-data')
                shutil.copytree(outer / 'original-data', data)
            return operations(('install', 'accept-local-property', 'replay-2.1'))

        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, {'truss': module, 'psycopg': types.ModuleType('psycopg'),
                                                       'weft': types.ModuleType('weft')}))
            stack.enter_context(patch.object(consumer, 'load_control', return_value=cleanup))
            stack.enter_context(patch.object(consumer.tempfile, 'mkdtemp', return_value=str(root)))
            stack.enter_context(patch.object(consumer, 'PublicSession', return_value=NS()))
            stack.enter_context(patch.object(consumer, 'accept_and_replay', side_effect=first))
            stack.enter_context(patch.object(consumer, 'write_and_import', side_effect=lambda *_: operations(('write', 'import'))))
            stack.enter_context(patch.object(consumer, 'generated_models', return_value=NS()))
            stack.enter_context(patch.object(consumer, 'typed_reads', side_effect=lambda *_: operations(
                ('typed-read', 'hidden-composite-pages', 'ordinary-1.2'))))
            stack.enter_context(patch.object(cleanup, '_socket_identity', return_value=[7, 8]))
            stack.enter_context(patch.object(cleanup.subprocess, 'run', side_effect=process))
            stack.enter_context(patch.object(cleanup.os, 'kill', side_effect=observe_pid))
            alarms = stack.enter_context(patch.object(consumer.signal, 'alarm'))
            handlers = stack.enter_context(patch.object(consumer.signal, 'signal', return_value='previous'))
            args = ({'profile': {'serverVersion': '18.6'}}, output, outer)
            if variant == 'late member':
                observed, receipt = consumer.run_native(*args)
                for name in consumer.OPERATIONS:
                    self.assertEqual(observed[name]['result']['sha256'], consumer.digest(name.encode('ascii')))
                self.assertEqual(set(receipt['clusters'][0]['databaseLayout']['databases']), {'1', '4', '5', '9'})
                self.assertTrue(receipt['clusters'][0]['dataDeleted'])
            else:
                with self.assertRaises((ValueError, RuntimeError)):
                    consumer.run_native(*args)
                receipt = json.loads((output / 'cleanup.json').read_bytes())
                self.assertTrue(data.exists())
                self.assertTrue(all(not row['dataDeleted'] for row in receipt['clusters']))
            self.assertEqual([call.args for call in alarms.call_args_list], [(300,), (0,)])
            self.assertEqual([call.args[1] for call in handlers.call_args_list[2:]], ['previous', 'previous'])
        # The on-disk operation evidence remains original even when cleanup refuses.
        operations_json = json.loads((output / 'operations.json').read_bytes())
        self.assertEqual(set(operations_json), set(consumer.OPERATIONS))
        self.assertTrue(all('result' not in row for row in operations_json.values()))
        return root, events, receipt

    def test_reviewed_cleanup_captures_original_pid_before_stop_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root, events, receipt = self.run_cleanup_fixture(Path(directory).resolve(), 'late member')
            self.assertFalse(root.exists())
            self.assertEqual(events[:4], ['start', ('membership', ('1', '4', '5')),
                                         ('membership', ('1', '4', '5', '9')), 'stop'])
            self.assertEqual(events[-2:], ['status', 'pid absent'])
            record = receipt['clusters'][0]
            self.assertEqual((record['originalPostmasterPid'], record['pgCtlStatus'],
                              record['originalPostmasterPidAbsent']), (314, 3, True))

    def test_uncaptured_and_mixed_uncertain_cleanup_retains_data(self):
        variants = ('uncaptured', 'mixed sibling', 'nested cluster', 'copied before capture',
                    'wrong socket', 'wrong PID', 'replaced root', 'refresh refusal', 'missing base',
                    'retry stop', 'retry changed socket', 'missing result')
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root, events, receipt = self.run_cleanup_fixture(Path(directory).resolve(), variant)
                self.assertTrue(root.is_dir())
                if variant in ('uncaptured', 'wrong PID', 'replaced root'):
                    self.assertNotIn('stop', events)
                    self.assertNotIn('retry', events)
                elif variant == 'retry stop':
                    self.assertEqual(events.count('retry'), 1)
                    self.assertTrue(receipt['cleanupErrors'])
                else:
                    self.assertEqual(events.count('stop'), 1)
                    self.assertNotIn('retry', events)

    def test_record_compares_source_and_native_payload_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            stream=io.BytesIO()
            with ZipFile(stream,'w') as wheel:
                wheel.writestr('owner/__init__.py',b'original source')
                wheel.writestr('owner/native.so',b'original native')
            for name,raw in [('owner/__init__.py',b'original source'),('owner/native.so',b'original native')]:
                path=root/name;path.parent.mkdir(exist_ok=True);path.write_bytes(raw)
            class Entry(str):
                hash=None;size=None
            dist=NS(files=[Entry('owner/__init__.py'),Entry('owner/native.so')],locate_file=lambda entry:root/entry)
            # A payload byte substitution refuses before the unhashed-RECORD guard.
            (root/'owner/native.so').write_bytes(b'swapped same-version binary')
            with self.assertRaisesRegex(ValueError,'substitution'):
                consumer.verify_record(dist,stream.getvalue())

    def test_typed_reads_use_actual_compiler_and_target_pages_and_ordinary_sibling(self):
        from types import ModuleType
        access=ModuleType('umf_access');types=ModuleType('umf_access.types');types.StrictModel=type('StrictModel',(),{})
        class Model:
            UMF_SOURCE=NS(document_sha256='original')
            UMF_FIELDS=(('m','A-instant','instant'),('m','A-date','day'),('m','A-local','local'),('m','A-label','label'))
            model_fields={name:NS(rebuild_annotation=lambda:datetime) for module,element,name in UMF_FIELDS}
        class Ordinary:
            UMF_FIELDS=(('m','B-label','label'),('m','B-value','value'))
        wanted=consumer.expected_rows()
        whole=[NS(instant=instant,day=day,local=local,label='row-'+str(i)) for i,(instant,day,local) in enumerate(wanted)]
        request=dict(target=dict(bindingJson=json.dumps(dict(queryAbi=dict(version='1.2')))))
        read=NS(artifact=lambda:dict(request=request))
        paged=NS(artifact=lambda:dict(page=dict(keyOutputPositions=[3,4],visibleOutputPositions=[0,1,2])))
        ordinary=NS(artifact=lambda:dict(request=request))
        def run(mutation=None):
            pages=[NS(items=whole[:2],next_after=NS(owner_cursor=b'one')),
                   NS(items=whole[2:4],next_after=NS(owner_cursor=b'two')),NS(items=whole[4:],next_after=None)]
            sibling=[NS(label='row-0',value='shared-key')]
            if mutation=='page':pages[1].items=whole[:2]
            if mutation=='ordinary':sibling[0].value=7
            if mutation=='type':whole[0].day=datetime(2024,1,1)
            targets=[NS(verify=Mock(),read=Mock(return_value=whole)),NS(page=Mock(side_effect=pages)),NS(read=Mock(return_value=sibling))]
            session=NS(query=Mock(side_effect=[(read,'parameters'),(paged,'parameters'),(ordinary,'parameters')]),target=Mock(side_effect=targets))
            result=consumer.typed_reads(session,{'A':Model,'B':Ordinary})
            self.assertTrue(session.query.call_args_list[1].kwargs['page'])
            self.assertTrue(session.query.call_args_list[2].kwargs['ordinary'])
            self.assertEqual(targets[1].page.call_args_list[0].kwargs,{'after':None})
            self.assertEqual(targets[1].page.call_args_list[1].kwargs['after'].owner_cursor,b'one')
            self.assertEqual(result['ordinary-1.2']['rows'],1)
        with patch.dict(sys.modules,{'umf_access':access,'umf_access.types':types}):
            run()
            for mutation in ('page','ordinary','type'):
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):run(mutation)


    def test_real_prepare_accept_replay_grant_sequence_and_original_request(self):
        def run(mutation=None):
            prepared,document,stored,report,replay=self.replay()
            class Ok:
                def __init__(self,value):self.value=value
            class Pending:pass
            class SQL:
                def __init__(self,text):self.text=text
                def format(self,*args):return self
            selected=NS(prepare_catalog=Mock(return_value=prepared),accept_in_transaction=Mock(side_effect=[
                Ok(NS(revision=1,replayed=False,report_bytes=report)),Ok(replay),Ok(replay)]))
            if mutation=='prepare':selected.prepare_catalog.side_effect=ValueError('missing prepare')
            if mutation=='accept':selected.accept_in_transaction.side_effect=ValueError('missing accept')
            if mutation=='replay':replay.report_bytes=b'changed replay report'
            if mutation=='source':stored=(*stored[:3],b'{"sourceFormat":"truss-registration-summary/2.0"}')
            assembly=NS(temporal_values=lambda:selected,install_in_transaction=Mock(return_value=Ok(NS(status='pending_commit',registrar_role='actual-registrar'))),
                configure_module_access_in_transaction=Mock(return_value=Ok(Pending() if mutation!='grants' else object())))
            admin=NS(execute=Mock(side_effect=lambda sql,*args:NS(fetchone=lambda:stored)))
            @contextmanager
            def transaction(**kwargs):yield NS(),assembly,'tx'
            @contextmanager
            def administration():yield admin
            api=NS(pg=NS(sql=NS(SQL=SQL,Identifier=lambda name:name)),truss=NS(PendingModuleAccessConfiguration=Pending,ModuleAccessGrant=lambda *args:args))
            session=NS(api=api,transaction=transaction,admin=administration,ok=lambda result:result.value)
            result=consumer.accept_and_replay(session,document)
            self.assertEqual(result['replay-2.1']['status'],'passed')
            selected.prepare_catalog.assert_called_once_with((document,))
            self.assertEqual(selected.accept_in_transaction.call_count,3)
            for call in selected.accept_in_transaction.call_args_list:
                self.assertIs(call.args[1],prepared)
                self.assertEqual(call.kwargs,dict(request_key='tn14-public-model'))
            assembly.install_in_transaction.assert_called_once_with('tx')
            assembly.configure_module_access_in_transaction.assert_called_once()
        run()
        for mutation in ('prepare','accept','replay','source','grants'):
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):run(mutation)

    def test_installer_uses_download_only_and_normal_resolver_with_exact_extras(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'runtime').mkdir();wheel=root/'runtime/pgserver_pg18-18.6.1.whl'
            wheel.write_bytes(b'synthetic public runtime');sha=consumer.digest(wheel.read_bytes())
            (root/'runtime/SHA256SUMS').write_text(sha+'  '+wheel.name+'\n')
            context=dict(profile=dict(distribution='pgserver-pg18',distributionVersion='18.6.1',
                repository='https://github.com/DocumentDrivenDX/pgserver',releaseTag='exact-profile-tag'),
                profileSha256='profile',binding=dict(candidateWheel=dict(distribution='umf-truss',version='candidate')))
            with patch.object(consumer.subprocess,'run') as run:
                runtime=consumer.install_public(context,root,root)
                calls=[call.args[0] for call in run.call_args_list]
                self.assertIn('--download-only',calls[0])
                self.assertIn('umf-truss[local,native,query,typed-sdk]==candidate',calls[1])
                self.assertIn('https://pypi.org/simple',calls[1]);self.assertIn(str(wheel.resolve()),calls[1])
                self.assertNotIn('--no-deps',calls[1]);self.assertNotIn('--find-links',calls[1])
                self.assertEqual(calls[2][-1],'check');self.assertEqual(runtime['sha256'],sha)

    def test_retained_operation_evidence_preserves_bytes_and_type_distinctions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            consumer.retain_result(root,'original',dict(report=b'original bytes',values=consumer.expected_rows()[0]))
            retained=json.loads((root/'original-result.json').read_bytes())
            self.assertEqual(retained['report']['sha256'],consumer.digest(b'original bytes'))
            self.assertTrue(retained['values'][0]['aware']);self.assertEqual(retained['values'][1]['type'],'date')
            self.assertFalse(retained['values'][2]['aware'])



if __name__ == '__main__':
    unittest.main()
