# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic actual own-session Subject observation and original UMF Key bytes."""
from hashlib import sha256
from dataclasses import replace
from unittest.mock import patch
import json
import os
from pathlib import Path
import shutil
import psycopg
from truss import (Ok, Error, CatalogDocument, ModuleAccessGrant, adopt_psycopg_host)
from truss.contracts import TextValue, MapValue
from truss.groups import CreateObject, AuthoredValue, RootlessOwnership, RequestNone, GroupSuccess
from truss._current_query_sources import register_current_query_sources_in_transaction
from truss._current_query_subjects import (register_current_query_subjects_in_transaction,
    observe_current_query_subject_in_transaction)
import test_catalog_runtime_native as catalog


class CurrentQuerySubjectsNativeTests(catalog.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(catalog.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name] = None

    def source_inputs(self):
        return (Path(__file__).parent/'fixtures/current-query-initialize.json').read_bytes(),None

    def test_ordinary_session_observes_only_enrolled_subject_and_original_key(self):
        bun = os.environ.get('TRUSS_BUN_EXECUTABLE',shutil.which('bun') or 'bun')
        self.install()
        initialize,query_originals = self.source_inputs()
        closure = json.loads(initialize)['sources']['closure']
        modules, documents = [], []
        for entry in closure['documents']:
            doc = entry['document'];raw = json.dumps(doc,separators=(',',':'),ensure_ascii=False)
            revision = next(p['revision'] for p in closure['pins'] if p['documentId']==doc['id'])
            modules.append({'pin':{'documentId':doc['id'],'revision':revision,'umfVersion':doc['umf'],'sha256':sha256(raw.encode()).hexdigest()},'documentJson':raw})
            documents.append(CatalogDocument(doc['id'],revision,raw.encode()))
        c,h,a,t = self.consumer()
        prepared = a.prepare_catalog(tuple(documents),source_version='0.10.0',bun_executable=bun)
        self.assertIsInstance(a.accept_in_transaction(t,prepared,request_key='subject-model'),Ok,str(h._custody.last_attempt.error))
        h.detach();c.commit()
        self.admin.execute('CREATE ROLE subject_reader;CREATE ROLE subject_writer;CREATE ROLE subject_outsider LOGIN')
        for role in ('subject_reader','subject_writer','subject_outsider'):
            self.addCleanup(self.admin.execute,'DROP OWNED BY '+role+';DROP ROLE '+role)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        from truss import create_reference_assembly,CatalogRuntimeConfiguration
        a = create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.assertIsInstance(a.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('domain','m','subject_reader','subject_writer'),)),Ok)
        self.host.detach();self.admin.commit();self.admin.execute('GRANT subject_writer TO consumer WITH SET FALSE')
        c,h,a,t = self.consumer()
        view = a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
        subject = next(d.reference for d in view.definitions if d.reference.kind=='type' and d.reference.authored_identity=='Staff')
        context = a.group_context_in_transaction(t).value
        result = a.apply_in_transaction(t,context.input((CreateObject(type_definition_pin=subject.definition_pin,
            values=(AuthoredValue(name='staffId',value=TextValue(kind='string',text='alice')),),
            ownership=RootlessOwnership(),alias='subject'),),MapValue(entries=())),RequestNone(),documents=tuple(documents),bun_executable=bun)
        self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        h.detach();c.commit()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        stored = register_current_query_sources_in_transaction(self.host,self.tx,initialize_bytes=initialize,
            accepted_request_bytes=json.dumps({'modules':modules},separators=(',',':')).encode(),query_originals=query_originals)
        self.assertIsInstance(stored,Ok,str(self.host._custody.last_attempt.error))
        missing = register_current_query_subjects_in_transaction(self.host,self.tx,bindings=(('consumer','missing'),))
        self.assertIsInstance(missing,Error)
        enrolled = register_current_query_subjects_in_transaction(self.host,self.tx,bindings=(('consumer','alice'),))
        self.assertIsInstance(enrolled,Ok,str(self.host._custody.last_attempt.error))
        self.host.detach();self.admin.commit()
        c,h,a,t = self.consumer()
        observed = observe_current_query_subject_in_transaction(h,t,enrolled.value,bun_executable=bun)
        self.assertIsInstance(observed,Ok,str(h._custody.last_attempt.error))
        self.current_subject_observation=observed.value
        self.current_subject_registration=enrolled.value
        self.current_source_documents=tuple(documents)
        self.assertEqual(observed.value.key,'alice')
        for changed in (replace(enrolled.value,identity=('m','Project','pk')),
                        replace(enrolled.value,original_document=enrolled.value.original_document+b' ')):
            with self.subTest(codec=changed.identity),patch('truss._current_query_subjects.encode_string_key_tuples') as encoder:
                refused = observe_current_query_subject_in_transaction(h,t,changed,bun_executable=bun)
                self.assertIsInstance(refused,Error)
                encoder.assert_not_called()
        self.assertEqual(observed.value.source_receipt,stored.value.source_receipt)
        self.assertEqual(observed.value.role_oid,c.execute('SELECT usesysid::text FROM pg_stat_activity WHERE pid=pg_backend_pid()').fetchone()[0])
        receipt = json.loads(observed.value.original_key_receipt)
        self.assertEqual(receipt['values'],[{'string':'alice'}]);self.assertEqual(bytes.fromhex(receipt['bytesHex']),observed.value.tuple_bytes)
        self.assertEqual(c.execute("SELECT has_table_privilege('truss.catalog_subject_map','SELECT'),has_table_privilege('truss.object','SELECT')").fetchone(),(False,False))
        parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']='subject_outsider'
        with psycopg.connect(**parameters,autocommit=True) as outsider:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                outsider.execute('SELECT * FROM truss.current_query_subject_current()')
