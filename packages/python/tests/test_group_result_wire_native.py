# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native containment after malformed original group-result decoding."""
import json
import os
import shutil
from unittest.mock import patch

import test_group_create_native as group_native
from truss import Error, Ok, _group_runtime
from truss.catalog_runtime import _pin_cursor, _release
from truss.groups import AppliedPending, GroupSuccess


class GroupResultWireNativeContainmentTests(group_native.PublicCreateGroupTests):
    for _name in tuple(name for name in dir(group_native.PublicCreateGroupTests) if name.startswith('test_')):
        locals()[_name] = None

    def test_malformed_native_response_rolls_back_group_and_keeps_prior_host_work(self):
        bun_executable = os.environ.get('TRUSS_BUN_EXECUTABLE', shutil.which('bun') or 'bun')
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        connection.execute('CREATE TEMP TABLE caller_work(value text)')
        connection.execute("INSERT INTO caller_work VALUES ('kept')")
        input_value, request = self.input(assembly, tx)
        original = _group_runtime._result
        captured_attempts = []

        def corrupt_after_native_call(raw, *, request_present):
            native = json.loads(raw)
            native['disposition'] = 'not-a-disposition'
            corrupted = json.dumps(native, ensure_ascii=False, separators=(',', ':')).encode()
            return original(corrupted, request_present=request_present)

        with patch.object(_group_runtime, '_result', side_effect=corrupt_after_native_call):
            manifest, digest, _ = _release()
            failed = _group_runtime.apply_group(host, tx, input_value, request, self.documents,
                manifest, digest, _pin_cursor, bun_executable=bun_executable,
                _attempt_capture=captured_attempts)
        self.assertIsInstance(failed, Error)
        self.assertEqual(failed.error.code, 'invalid_transaction')
        self.assertEqual(captured_attempts, [])
        self.assertEqual(connection.execute('TABLE caller_work').fetchall(), [('kept',)])
        recovered = assembly.apply_in_transaction(tx, input_value, request, documents=self.documents,
            bun_executable=bun_executable)
        self.assertIsInstance(recovered, Ok)
        self.assertIsInstance(recovered.value, GroupSuccess)
        self.assertIsInstance(recovered.value.response, AppliedPending)
        self.assertEqual(connection.execute('SELECT count(*) FROM caller_work').fetchone(), (1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), (0,))
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), (1,))
