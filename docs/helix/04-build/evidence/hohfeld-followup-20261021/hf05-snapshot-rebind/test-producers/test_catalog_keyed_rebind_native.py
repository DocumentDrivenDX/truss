# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public registration of a required retained field and its alternate key."""
import json, os
from dataclasses import replace
from truss import CatalogDocument, Ok, CatalogRegistration, ObjectFound, QueryRows, HistoryEntity, HistoricalRecord
from truss.contracts import TextValue
from truss.groups import AuthoredValue
import test_catalog_key_backfill_native as base

class CatalogKeyedRebindTests(base.CatalogKeyBackfillTests):
    def create(self,label='one',value='value',alias='item',document='adoc',record='A'):
        operation=super().create(label=label,value='original-'+label,alias=alias,document=document,record=record)
        return replace(operation,values=operation.values+(
            AuthoredValue(name='giftCode',value=TextValue(kind='string',text=value)),))
    def with_key(self):
        original=next(d for d in self.documents if d.document_id=='adoc')
        source=json.loads(original.content);module=source['modules'][0]
        module['elements'].append({'id':'giftCode','name':'giftCode','kind':'field',
            'cardinality':'one','nullability':'required','scalarType':'string','extensions':{}})
        record=next(e for e in module['elements'] if e['id']=='A')
        record['members'].append({'module':'m','element':'giftCode'})
        record['keys'].append({'id':'a-backfill','name':'backfill',
            'fields':[{'module':'m','element':'giftCode'}],'primary':False})
        return CatalogDocument('adoc','r2',json.dumps(source).encode())
    def register(self,a,t):
        catalog=a.catalog(a.catalog_selection).capability
        prepared=catalog.prepare_catalog((self.with_key(),),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        return catalog.accept_in_transaction(t,prepared,request_key='new-alternate-key',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))

    # The inherited duplicate workflow also proves that failed acceptance leaves
    # the original revision selected. The successful workflow differs because
    # the rebind changes the object version and declared query field.
    def test_register_existing_objects_lookup_and_query(self):
        identities=self.seed(('first','second'));c,h,a,t=self.consumer()
        accepted=self.register(a,t)
        self.assertIsInstance(accepted,Ok,repr(accepted))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        report=json.loads(accepted.value.report_bytes)
        self.assertEqual(report['effects'],{'reboundObjects':2,'keyBackfills':2})
        self.assertNotIn('rebinds',report)
        found=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-backfill',values=('first',),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(found.value,ObjectFound,repr(found))
        self.assertEqual(found.value.object.id,int(identities[0].id))
        self.assertEqual(found.value.object.version,2)
        query=a.query_in_transaction(t,sql='SELECT a."giftCode" FROM "A" a ORDER BY a."giftCode"',document_ids=('adoc',))
        self.assertIsInstance(query.value,QueryRows,repr(query))
        self.assertEqual(query.value.rows,(('first',),('second',)))
        h.detach();c.commit()
        c,h,a,t=self.consumer()
        history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identities[0].id)),version=2)
        self.assertIsInstance(history.value,HistoricalRecord,repr(history))
        h.detach();c.rollback()
