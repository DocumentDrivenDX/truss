# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic actual PG18 original-source storage, not current-query permission."""
from hashlib import sha256
import json
import os
import shutil
from pathlib import Path
import struct
import psycopg
from truss import Ok, Error, CatalogDocument, adopt_psycopg_host
from truss._current_query_sources import (register_current_query_sources_in_transaction,
    capture_current_query_sources_with_cursor)
import test_catalog_runtime_native as catalog


class CurrentQuerySourcesNativeTests(catalog.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(catalog.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name] = None

    def test_registered_originals_survive_commit_and_refuse_changed_archive(self):
        self.install()
        initialize = (Path(__file__).parent/'fixtures/current-query-initialize.json').read_bytes()
        envelope = json.loads(initialize)
        closure = envelope['sources']['closure']
        modules = []
        documents = []
        for entry in closure['documents']:
            document = entry['document']
            original = json.dumps(document, separators=(',', ':'), ensure_ascii=False)
            revision = next(p['revision'] for p in closure['pins'] if p['documentId'] == document['id'])
            modules.append({'pin':{'documentId':document['id'], 'revision':revision,
                                   'umfVersion':document['umf'], 'sha256':sha256(original.encode()).hexdigest()},
                            'documentJson':original})
            documents.append(CatalogDocument(document['id'], revision, original.encode()))
        connection, host, assembly, tx = self.consumer()
        prepared = assembly.prepare_catalog(tuple(documents), source_version='0.10.0', bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', shutil.which('bun') or 'bun'))
        accepted = assembly.accept_in_transaction(tx, prepared, request_key='current-source-catalog')
        self.assertIsInstance(accepted, Ok, str(host._custody.last_attempt.error))
        host.detach(); connection.commit()
        self.admin.execute('BEGIN')
        self.host = adopt_psycopg_host(self.admin, operation_timeout_ms=30000)
        self.tx = self.host.adopt_transaction().value
        request = json.dumps({'modules':modules}, separators=(',', ':')).encode()
        registered = register_current_query_sources_in_transaction(self.host, self.tx,
            initialize_bytes=initialize, accepted_request_bytes=request)
        self.assertIsInstance(registered, Ok, str(self.host._custody.last_attempt.error))
        self.assertEqual(registered.value.source_receipt, sha256(struct.pack('>I',len(initialize))+initialize).hexdigest())
        self.assertEqual(registered.value.accepted_revision, '1')
        self.host.detach(); self.admin.commit()
        self.admin.execute('BEGIN')
        self.host = adopt_psycopg_host(self.admin, operation_timeout_ms=30000)
        self.tx = self.host.adopt_transaction().value
        captured = self.host._run_operation(self.tx, lambda cursor, _:capture_current_query_sources_with_cursor(cursor))
        self.assertIsInstance(captured, Ok, str(self.host._custody.last_attempt.error))
        self.assertEqual(captured.value.initialize_bytes, initialize)
        self.assertEqual(captured.value.accepted_request_bytes, request)
        self.assertEqual(captured.value.source_receipt, registered.value.source_receipt)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_current').fetchone(), (0,))
        self.assertEqual(self.admin.execute("SELECT has_table_privilege('consumer','truss.installation_archive','SELECT')").fetchone(), (False,))
        # Actual generated content hashes change, but the original marker binds
        # the entire archive and must refuse this replacement.
        self.admin.execute("UPDATE truss.installation_archive SET artifact_bytes=artifact_bytes||decode('20','hex') WHERE artifact_identity='current-query:initialize'")
        changed = self.host._run_operation(self.tx, lambda cursor, _:capture_current_query_sources_with_cursor(cursor))
        self.assertIsInstance(changed, Error)
        self.assertIn('release and assessment', str(self.host._custody.last_attempt.error))
