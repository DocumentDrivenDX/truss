# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original Weft sources + actual selected consumers + native Subject binding."""
from pathlib import Path
from hashlib import sha256
import json
import weft
from truss import Ok, adopt_psycopg_host, CurrentQueryOriginals, prepare_current_query_originals
from truss._current_query_originals import check_query_originals
from truss._current_query_sources import capture_current_query_sources_with_cursor
import test_current_query_subjects_native as subject


class CurrentQueryFullSourcesNativeTests(subject.CurrentQuerySubjectsNativeTests):
    for name in tuple(n for n in dir(subject.CurrentQuerySubjectsNativeTests) if n.startswith('test_')):
        locals()[name]=None

    def source_inputs(self):
        raw=(Path(__file__).parent/'fixtures/current-query-weft-request.json').read_bytes()
        # Invoke the original real producer; this static archive is not itself
        # a compiler or a permission. Query-specific state is not retained.
        prepared=weft.prepare_application_lineage(raw.decode()).prepare_current_query()
        self.assertEqual(json.loads(prepared.native_request_json())['version'],
                         'weft.current-query.native-input/0.1-candidate')
        request=json.loads(raw);opaque=request['opaqueSources']
        source={row['role']:json.loads(row['utf8']) for row in opaque}
        closure={'pins':[{'documentId':m['pin']['documentId'],'revision':m['pin']['revision']} for m in request['modules']],
                 'documents':[{'revision':m['pin']['revision'],'document':json.loads(m['documentJson'])} for m in request['modules']]}
        initialize=json.dumps({'kind':'initialize','requestId':'initialize','sources':{
            'policy':source['policy'],'catalog':source['catalog'],'ontology':source['ontology'],
            'closure':closure,'associationBindings':[],'extensionSelection':None}},separators=(',',':')).encode()
        original_bytes=json.dumps(opaque,separators=(',',':')).encode()
        self.originals=prepare_current_query_originals(original_bytes)
        self.assertIs(self.originals.opaque_sources_bytes,original_bytes)
        return initialize,self.originals

    def test_full_original_sources_bind_actual_subject_helper(self):
        subject.CurrentQuerySubjectsNativeTests.test_ordinary_session_observes_only_enrolled_subject_and_original_key(self)
        self.admin.execute('BEGIN')
        self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        captured=self.host._run_operation(self.tx,lambda cursor,_:capture_current_query_sources_with_cursor(cursor))
        self.assertIsInstance(captured,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(captured.value.source_profile,'truss-current-query-sources/0.2-candidate')
        self.assertEqual(captured.value.query_originals,self.originals)
        self.assertEqual(len(captured.value.inventory_digest),64)
        self.assertIn("a.inventory_profile='truss-current-query-sources/0.2-candidate'",self.current_subject_registration.helper_source)
        self.assertIn(captured.value.inventory_digest,self.current_subject_registration.helper_source)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(6,))
        changed=json.loads(captured.value.initialize_bytes)
        changed['sources']['closure']['documents'][0]['document']['modules'][0]['elements'][0]['name']='changed'
        with self.assertRaisesRegex(ValueError,'closure document correspondence'):
            check_query_originals(self.originals,json.dumps(changed).encode(),captured.value.accepted_request_bytes)
        changed=json.loads(captured.value.initialize_bytes);changed['sources']['ontology']=[]
        rows=json.loads(self.originals.opaque_sources_bytes)
        row=next(r for r in rows if r['role']=='ontology');row['utf8']='[]';row['sha256']=sha256(b'[]').hexdigest()
        with self.assertRaisesRegex(ValueError,'ontology identity'):
            check_query_originals(CurrentQueryOriginals(json.dumps(rows).encode(),self.originals.consumer_bytes),
                                  json.dumps(changed).encode(),captured.value.accepted_request_bytes)
