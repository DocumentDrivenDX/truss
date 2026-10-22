# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public cursor composition from an original current native-binding request."""
import json
from unittest.mock import patch
import weft
from truss import Ok,QueryPage
from truss.groups import GroupSuccess
from truss.query_stream import QueryStreamRefused
import test_compiled_query_native as fixtures

class QueryStreamABI12Tests(fixtures.CompiledQueryTests):
    for _name in tuple(n for n in dir(fixtures.CompiledQueryTests) if n.startswith('test_')):locals()[_name]=None

    def original(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.assertIsInstance(self.run_group(a,t,tuple(self.create(label=str(i),value='same',alias='row'+str(i)) for i in range(3)))[0],GroupSuccess)
        from truss._query_runtime import compile_response
        captured=[]
        def capture(compiler,request,*args):captured.append(json.loads(request));return compile_response(compiler,request,*args)
        with patch('truss._query_runtime.compile_response',side_effect=capture):
            page=a.query_page_in_transaction(t,sql='SELECT a."A-label" FROM "A" a WHERE a."A-value"=:wanted',document_ids=('adoc',),parameters={'wanted':'same'},limit=2,maximum_scan_rows=10)
        self.assertIsInstance(page,Ok,repr(page));self.assertIsInstance(page.value,QueryPage,repr(page))
        original=weft.compile_engine_page_json(json.dumps({'version':'weft.engine-page/0.1','compiler':'truss-runtime','request':captured[-1],'pageSize':2}))
        self.assertEqual(json.loads(original)['status'],'compiled',original)
        return c,h,a,t,original

    def test_actual_selected_cursor_decodes_all_batches_and_descriptors(self):
        c,h,a,t,original=self.original();seen=[]
        handle=a.query_stream_open_in_transaction(t,engine_program=original,parameters={'wanted':'same'})
        def validate(rows):seen.append(rows.column_descriptors);return rows.rows
        first=a.query_stream_fetch_in_transaction(t,handle,count=2,validate=validate)
        second=a.query_stream_fetch_in_transaction(t,handle,count=2,validate=validate)
        self.assertEqual(first.items+second.items,(('0',),('1',),('2',)));self.assertFalse(first.exhausted);self.assertTrue(second.exhausted)
        self.assertTrue(all(len(columns)==1 and columns[0].output_name=='A-label' for columns in seen))
        a.query_stream_close_in_transaction(t,handle)

    def test_cursor_current_person_revocation_preserves_caller_work(self):
        c,h,a,t,original=self.original();c.execute('CREATE TEMP TABLE prior(value int)');c.execute('INSERT INTO prior VALUES(9)')
        handle=a.query_stream_open_in_transaction(t,engine_program=original,parameters={'wanted':'same'})
        self.admin.execute('REVOKE group_writer FROM consumer')
        with self.assertRaises(QueryStreamRefused):a.query_stream_fetch_in_transaction(t,handle,count=2,validate=lambda rows:rows.rows)
        self.assertEqual(c.execute('SELECT * FROM prior').fetchall(),[(9,)])
