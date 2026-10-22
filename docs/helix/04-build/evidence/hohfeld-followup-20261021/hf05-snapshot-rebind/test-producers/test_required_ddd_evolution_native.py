# SPDX-License-Identifier: MIT OR Apache-2.0
"""HF-03 required core/DDD additions under the ordinary catalog writer gate."""
import json
import psycopg
from dataclasses import replace
from truss import CatalogDocument, CatalogRegistration, CatalogAcceptanceRefused, Ok, Error
from truss.groups import GroupSuccess, GroupUnavailable, GroupFailed
from truss.groups import AuthoredValue
from truss.contracts import TextValue
import test_hohfeld_disputes_native as fixtures


class RequiredDDDEvolutionTests(fixtures.HohfeldDisputesNativeTests):
    for _name in tuple(n for n in dir(fixtures.HohfeldDisputesNativeTests) if n.startswith('test_')):
        locals()[_name]=None

    def evolution(self, assembly, *, alter_unknown=False):
        source=json.loads(self.documents[0].content)
        module=source['modules'][0];record=next(e for e in module['elements'] if e['id']=='A')
        record['members'].append({'module':'m','element':'A-required'})
        record['extensions']['umf.ddd']['fields']['A-required']={
            'type':{'kind':'scalar','name':'string'},'cardinality':'one'}
        module['elements'].append({'id':'A-required','name':'A-required','kind':'field',
            'scalarType':'string','nullability':'required','cardinality':'one','extensions':{}})
        if alter_unknown:record['extensions']['x-retained']['future'].append('changed')
        document=CatalogDocument('adoc','required-r2',json.dumps(source).encode())
        return document,assembly.prepare_catalog((document,))

    def ready_required(self):
        c,h,a,t=self.ready(self.ddd,document_ids=('adoc',))
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(
            psycopg.sql.Identifier(self.installation.registrar_role)))
        return c,h,a,t

    def assert_populated_refusal(self,result):
        self.assertIsInstance(result,Ok,repr(result))
        self.assertIsInstance(result.value,CatalogAcceptanceRefused)
        self.assertEqual(len(result.value.violations),1)
        violation=result.value.violations[0]
        self.assertEqual((violation.rule,violation.affected_object_count),('property.required',1))

    def test_empty_record_accepts_exact_paired_required_field_and_unknown_content(self):
        c,h,a,t=self.ready_required();document,prepared=self.evolution(a)
        original=json.loads(self.documents[0].content)['modules'][0]['elements'][0]['extensions']['x-retained']
        result=a.accept_in_transaction(t,prepared,request_key='required-r2')
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,CatalogRegistration)
        self.assertEqual(result.value.revision,2)
        published=a.accepted_document_in_transaction(t,document_id='adoc').value
        self.assertEqual(published.content,document.content)
        self.assertEqual(json.loads(published.content)['modules'][0]['elements'][0]['extensions']['x-retained'],original)
        self.assertTrue(json.loads(published.ddd_validation_bytes)['valid'])
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))

    def test_populated_record_returns_typed_violation_and_preserves_head_data_history(self):
        c,h,a,t=self.ready_required();created,_,_=self.run_group(a,t,(self.create(),),'seed')
        self.assertIsInstance(created,GroupSuccess);h.detach();c.commit();c,h,a,t=self.consumer()
        _,prepared=self.evolution(a);before=self.group_effect_counts()
        self.assert_populated_refusal(a.accept_in_transaction(t,prepared,request_key='required-r2'))
        h.detach();c.commit();self.assertEqual(self.group_effect_counts(),before)
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))

    def test_paired_required_addition_does_not_implicitly_rebind_populated_retained_values(self):
        c,h,a,t=self.ready_required();operation=self.create()
        operation=replace(operation,values=operation.values+(AuthoredValue(name='A-required',value=TextValue(kind='string',text='already-retained')),))
        self.assertIsInstance(self.run_group(a,t,(operation,),'retained-required-seed')[0],GroupSuccess)
        h.detach();c.commit();c,h,a,t=self.consumer();_,prepared=self.evolution(a)
        before=self.admin.execute('SELECT id,type_id,ver,props,retained FROM truss.object ORDER BY id').fetchall()
        self.assert_populated_refusal(a.accept_in_transaction(t,prepared,request_key='required-retained-r2'))
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT id,type_id,ver,props,retained FROM truss.object ORDER BY id').fetchall(),before)
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))

    def test_pending_writer_blocks_acceptance_then_committed_row_refuses_addition(self):
        c,h,a,t=self.ready_required();_,prepared=self.evolution(a)
        created,_,_=self.run_group(a,t,(self.create(),),'racing-writer');self.assertIsInstance(created,GroupSuccess)
        c2,h2,a2,t2=self.consumer();busy=a2.accept_in_transaction(t2,prepared,request_key='racing-required')
        self.assertIsInstance(busy,Error,repr(busy));self.assertEqual(busy.error.sql_state,'55P03')
        h2.detach();c2.rollback();h.detach();c.commit();c3,h3,a3,t3=self.consumer()
        self.assert_populated_refusal(a3.accept_in_transaction(t3,prepared,request_key='racing-required'))
        h3.detach();c3.commit();self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))

    def test_paired_required_addition_does_not_authorize_unknown_extension_change(self):
        c,h,a,t=self.ready_required();_,prepared=self.evolution(a,alter_unknown=True)
        result=a.accept_in_transaction(t,prepared,request_key='unknown-change')
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.catalog_code,'unsupported_profile')
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))

    def test_pending_acceptance_excludes_old_shape_writer_and_stale_pin_after_commit(self):
        c,h,a,t=self.ready_required();old_input,old_request=self.input(a,t)
        document,prepared=self.evolution(a)
        accepted=a.accept_in_transaction(t,prepared,request_key='accept-first')
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration)
        c2,h2,a2,t2=self.consumer()
        blocked=a2.apply_in_transaction(t2,old_input,old_request,documents=self.documents)
        self.assertIsInstance(blocked,Ok,repr(blocked));self.assertIsInstance(blocked.value,GroupUnavailable)
        self.assertEqual(blocked.value.reason,'observation')
        h2.detach();c2.rollback();h.detach();c.commit()
        c3,h3,a3,t3=self.consumer()
        stale=a3.apply_in_transaction(t3,old_input,old_request,documents=self.documents)
        self.assertIsInstance(stale,Ok,repr(stale));self.assertIsInstance(stale.value,GroupFailed)
        h3.detach();c3.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(2,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
