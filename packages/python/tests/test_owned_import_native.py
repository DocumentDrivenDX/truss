# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic atomic owned aggregate import through the public capability."""
import base64
from dataclasses import replace
from hashlib import sha256
import json
from truss import Ok,ObjectFound,EdgeFound,HistoryEntity,ImportSourceFound,QueryRows
from truss.contracts import MapValue,MapEntry,TextValue,ExactArtifact
from truss.groups import NullOrderKey,OwnedOwnership
from truss.imports import ImportReported,ImportCreated,ImportSkipped,ImportRejected
import test_owned_objects_native as base

class OwnedImportTests(base.OwnedObjectTests):
    for _name in tuple(n for n in dir(base.OwnedObjectTests) if n.startswith('test_')):locals()[_name]=None

    def capability(self,assembly):
        return assembly.imports(assembly.import_selection,documents=self.documents).capability

    def aggregate(self,cap,tx,prefix):
        def source(label):return MapValue(entries=(MapEntry(key='author',value=TextValue(kind='string',text=label)),))
        root=cap.owned_object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',
            values=self.create(label=prefix+'-root',value=prefix+'-root').values,source=source('root-source'))
        self.assertIsInstance(root,Ok,repr(root))
        child=cap.owned_object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',
            values=self.create(label=prefix+'-child',value=prefix+'-child').values,root=root.value.identity,source=source('child-source'))
        self.assertIsInstance(child,Ok,repr(child))
        edge=cap.owned_edge_import_record_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='children',
            source_endpoint=root.value.identity,target_endpoint=child.value.identity,values=(),order_key=NullOrderKey(),source=source('edge-source'))
        self.assertIsInstance(edge,Ok,repr(edge))
        return root.value,child.value,edge.value

    @staticmethod
    def invalid_payload(record):
        raw=b'not valid JSON';digest=sha256(raw).hexdigest()
        return replace(record,payload=ExactArtifact(identity=digest,sha256=digest,bytes_base64=base64.b64encode(raw).decode()))

    def test_import_commit_reopen_sources_and_invalid_replacement_retry(self):
        connection,host,assembly,tx=self.ready(self.owned_model,document_ids=('adoc',))
        cap=self.capability(assembly);context=cap.owned_import_context_in_transaction(tx).value
        records=self.aggregate(cap,tx,'one')
        result=cap.import_in_transaction(tx,context.input(records,load_id='original',asserted_origin=MapValue(entries=())))
        self.assertIsInstance(result,ImportReported,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertTrue(all(isinstance(o,ImportCreated) for o in result.report.outcomes))
        self.assertEqual(result.report.counts.created_pending,'3');self.assertEqual(len(result.report.batches),1)
        identities=tuple(o.identity for o in result.report.outcomes)
        host.detach();connection.commit()
        rows=self.admin.execute('SELECT group_attempt_id,operation_index FROM truss.runtime_import_source ORDER BY operation_index').fetchall()
        self.assertEqual(len({r[0] for r in rows}),1);self.assertEqual([r[1] for r in rows],[0,1,2])
        connection,host,assembly,tx=self.consumer()
        child=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identities[1].id))
        self.assertIsInstance(child,Ok,repr(child));self.assertIsInstance(child.value,ObjectFound)
        self.assertIsInstance(child.value.object.ownership,OwnedOwnership)
        self.assertEqual(child.value.object.ownership.root.identity,identities[0])
        edge=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='children',edge_id=int(identities[2].id))
        self.assertIsInstance(edge,Ok,repr(edge));self.assertIsInstance(edge.value,EdgeFound)
        self.assertEqual(edge.value.edge.source,identities[0]);self.assertEqual(edge.value.edge.target,identities[1])
        complete=assembly.query_in_transaction(tx,sql='SELECT a.* FROM "A" a ORDER BY a."A-label"',
            document_ids=('adoc',),read_profile='complete-entity')
        self.assertIsInstance(complete,Ok,repr(complete)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(complete.value,QueryRows)
        projected=[dict(zip(complete.value.columns,row,strict=True)) for row in complete.value.rows]
        self.assertEqual(len(projected),2)
        attribution={row['A-label']:(row['_created_by'],row['_updated_by'],row['_original_author'],row['_load_id']) for row in projected}
        self.assertEqual(attribution,{
            'one-root':('consumer','consumer','root-source','original'),
            'one-child':('consumer','consumer','child-source','original')})
        expected_sources=({'author':'root-source'},{'author':'child-source'},{'author':'edge-source'})
        for index,identity in enumerate(identities):
            found=assembly.lookup_import_source_in_transaction(tx,entity=HistoryEntity(kind='edge' if index==2 else 'object',document_id='adoc',module_id='m',definition_id='children' if index==2 else 'A',id=int(identity.id)))
            self.assertIsInstance(found,Ok,repr(found));self.assertIsInstance(found.value,ImportSourceFound)
            self.assertEqual(found.value.load_id,'original')
            self.assertEqual(json.loads(found.value.content)['source'],expected_sources[index])
        cap=self.capability(assembly);context=cap.owned_import_context_in_transaction(tx).value
        retry=cap.import_in_transaction(tx,context.input(tuple(self.invalid_payload(r) for r in records),load_id='replacement',asserted_origin=MapValue(entries=())))
        self.assertIsInstance(retry,ImportReported,repr(retry)+' '+str(host._custody.last_attempt.error))
        self.assertTrue(all(isinstance(o,ImportSkipped) for o in retry.report.outcomes))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT load_id FROM truss.record_source ORDER BY entity_id').fetchall(),[('original',)]*3)

    def test_bad_dependent_record_rejects_entire_new_aggregate(self):
        connection,host,assembly,tx=self.ready(self.owned_model,document_ids=('adoc',))
        cap=self.capability(assembly);context=cap.owned_import_context_in_transaction(tx).value
        records=self.aggregate(cap,tx,'bad')
        records=records[:2]+(self.invalid_payload(records[2]),)
        connection.execute('CREATE TEMP TABLE prior_import_work(value text);INSERT INTO prior_import_work VALUES(\'kept\')')
        result=cap.import_in_transaction(tx,context.input(records,load_id='bad',asserted_origin=MapValue(entries=())))
        self.assertIsInstance(result,ImportReported,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertTrue(all(isinstance(o,ImportRejected) for o in result.report.outcomes))
        self.assertEqual(result.report.counts.rejected,'3')
        self.assertEqual(connection.execute('TABLE prior_import_work').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','edge','record_source','runtime_import_source','runtime_object_attempt','runtime_owned_operation'):
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.'+table).fetchone(),(0,),table)

    def test_engine_owned_aggregate_commits_as_one_batch(self):
        import os,psycopg
        from truss import run_import_batches
        connection,host,assembly,tx=self.ready(self.owned_model,document_ids=('adoc',))
        cap=self.capability(assembly);context=cap.owned_import_context_in_transaction(tx).value
        records=self.aggregate(cap,tx,'engine')
        input=context.input(records,load_id='engine-owned',asserted_origin=MapValue(entries=()))
        params=psycopg.conninfo.conninfo_to_dict(self.runtime.info.connection_uri);params['user']='consumer'
        host.detach();connection.rollback()
        result=run_import_batches(input,connection_info=psycopg.conninfo.make_conninfo(**params),documents=self.documents,
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'),statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.assertIsInstance(result,ImportReported,repr(result))
        self.assertEqual(result.report.execution,'engine_owned')
        self.assertEqual(result.report.counts.created_committed,'3')
        self.assertEqual(result.report.counts.created_pending,'0')
        self.assertEqual([b.disposition for b in result.report.batches],['committed'])
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT operation_index FROM truss.runtime_import_source ORDER BY operation_index').fetchall(),[(0,),(1,),(2,)])

    def test_second_source_failure_rolls_back_the_applied_aggregate(self):
        from truss.imports import ImportExecutionFailed
        connection,host,assembly,tx=self.ready(self.owned_model,document_ids=('adoc',))
        cap=self.capability(assembly);context=cap.owned_import_context_in_transaction(tx).value
        records=self.aggregate(cap,tx,'source-failure')
        self.admin.execute("CREATE FUNCTION public.reject_second_import_source() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN IF NEW.operation_index=1 THEN RAISE EXCEPTION 'fixture second source failure' USING ERRCODE='P9999';END IF;RETURN NEW;END;$$")
        self.admin.execute('CREATE TRIGGER reject_second_import_source BEFORE INSERT ON truss.runtime_import_source FOR EACH ROW EXECUTE FUNCTION public.reject_second_import_source()')
        self.addCleanup(lambda:self.admin.execute('DROP FUNCTION IF EXISTS public.reject_second_import_source() CASCADE'))
        connection.execute("CREATE TEMP TABLE prior_source_work(value text);INSERT INTO prior_source_work VALUES('kept')")
        result=cap.import_in_transaction(tx,context.input(records,load_id='fault',asserted_origin=MapValue(entries=())))
        self.assertIsInstance(result,ImportExecutionFailed,repr(result))
        self.assertEqual(result.error.sql_state,'P9999',repr(result))
        self.assertEqual(connection.execute('TABLE prior_source_work').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','edge','record_source','runtime_import_source','runtime_object_attempt','runtime_owned_operation'):
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.'+table).fetchone(),(0,),table)
