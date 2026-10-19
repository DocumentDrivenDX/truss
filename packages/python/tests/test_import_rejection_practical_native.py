# SPDX-License-Identifier: MIT OR Apache-2.0
"""A secondary-key conflict is a rejected import, not an unsupported profile."""
from truss import Ok
from truss.groups import GroupSuccess
from truss.imports import ImportCreated,ImportRejected
from test_import_runtime_native import ImportRuntimeTests

class ImportRejectionPracticalTests(ImportRuntimeTests):
    for _name in tuple(n for n in dir(ImportRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_secondary_key_conflict_preserves_prior_and_following_records(self):
        connection,host,assembly,tx=self.ready()
        prior,_,_=self.run_group(assembly,tx,(self.create(label='same-label',value='first-value'),),'prior')
        self.assertIsInstance(prior,GroupSuccess)
        context=assembly.import_context_in_transaction(tx).value
        conflicting=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',
            values=self.create(label='same-label',value='second-value').values)
        self.assertIsInstance(conflicting,Ok)
        following=self.record(assembly,tx,label='following')
        report=self.execute(assembly,tx,context,(conflicting.value,following))
        self.assertIsInstance(report.outcomes[0],ImportRejected)
        self.assertEqual(report.outcomes[0].code,'conflict')
        self.assertIsInstance(report.outcomes[1],ImportCreated)
        self.assertEqual((report.counts.rejected,report.counts.created_pending),('1','1'))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))
        connection,host,assembly,tx=self.consumer()
        for identity,label in ((prior.response.semantic.results[0].identity,'same-label'),(report.outcomes[1].identity,'following')):
            found=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
            self.assertIsInstance(found,Ok)
            self.assertEqual(dict(found.value.object.values)['A-label'],label)
        host.detach();connection.rollback()
