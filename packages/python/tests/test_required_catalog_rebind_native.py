# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic required-field rebinding through the public assembly."""
import os
from dataclasses import replace
from truss import Ok,CatalogAcceptanceRefused
from truss.contracts import MapValue,NullValue,SequenceValue
from truss.groups import AuthoredValue,GroupSuccess
import test_catalog_rebind_native as prior

class RequiredCatalogRebindTests(prior.CatalogRebindTests):
    test_create_and_register_in_one_host_transaction=None
    test_invalid_candidate_refuses_without_changing_data=None
    def revised(self, original):
        import json
        from truss import CatalogDocument
        document=super().revised(original);source=json.loads(document.content)
        for field in source['modules'][0]['elements']:
            if field['id'] in ('giftWrap','giftFlags'):field['nullability']='required'
        return CatalogDocument(document.document_id,document.document_revision,json.dumps(source).encode())
    def test_missing_null_and_empty_container_counts(self):
        c,h,a,t=self.ready(self.fields)
        first=replace(self.create(label='one',value='one',alias='one'),values=self.create(label='one',value='one').values+(
            AuthoredValue(name='giftWrap',value=NullValue()),AuthoredValue(name='giftFlags',value=SequenceValue(items=()))))
        second=self.create(label='two',value='two',alias='two')
        context=a.group_context_in_transaction(t).value
        self.assertIsInstance(self.apply(a,t,context.input((first,second),MapValue(entries=())),context.request('required-candidates')),GroupSuccess)
        h.detach();c.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        document=self.revised(next(d for d in self.documents if d.document_id=='adoc'))
        c,h,a,t=self.consumer();prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        refused=a.accept_in_transaction(t,prepared,request_key='required-missing')
        self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,CatalogAcceptanceRefused,repr(refused))
        self.assertEqual({(v.field_id,v.rule):v.affected_object_count for v in refused.value.violations},
                         {('giftWrap','property.required'):2,('giftFlags','property.required'):1})
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT ver FROM truss.object ORDER BY id').fetchall(),[(1,),(1,)])
