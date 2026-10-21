# SPDX-License-Identifier: MIT OR Apache-2.0
"""Measured public-call budgets, separate from adoption and host settlement."""
import json
import os
from pathlib import Path
import platform
import time
import psycopg
from unittest.mock import patch
from truss import Ok,QueryRows,QueryCatalogRead,ObjectFound,ObjectPage
from truss.contracts import MapValue
from truss.groups import GroupSuccess,RequestNone,CreateEdge,AliasObjectReference,NullOrderKey
import test_object_mutations_native as base


class HohfeldStatementBudgetTests(base.ObjectMutationTests):
    for name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')):locals()[name]=None

    def test_public_operation_statement_and_round_trip_budgets(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        created=self.run_group(assembly,tx,tuple(self.create(label=f'row-{i}',alias=f'row-{i}') for i in range(51)),'budget-seed')[0]
        self.assertIsInstance(created,GroupSuccess)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        relationship=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value
        context=assembly.group_context_in_transaction(tx).value
        source=self.documents[0].content
        conditional=assembly.reader_catalog_if_changed_in_transaction(tx).value
        sql='SELECT a.* FROM "A" a WHERE a."A-label"=:label'
        arguments=dict(sql=sql,document_ids=('adoc',),parameters={'label':'row-0'},read_profile='complete-entity')
        self.assertIsInstance(assembly.query_in_transaction(tx,**arguments).value,QueryRows)
        self.assertIsInstance(assembly.query_with_catalog_in_transaction(tx,**arguments,catalog_validator=conditional.validator).value,QueryCatalogRead)
        rows=[]
        original_execute=psycopg.Cursor.execute;original_wait=connection.wait
        statements=[];waits=[]
        def executed(cursor,query,*args,**kwargs):
            statements.append(str(query));return original_execute(cursor,query,*args,**kwargs)
        def waited(*args,**kwargs):
            waits.append(None);return original_wait(*args,**kwargs)
        counted=patch.object(psycopg.Cursor,'execute',new=executed);counted.start();connection.wait=waited
        def measure(name,operation,check):
            statements.clear();waits.clear();start=time.perf_counter()
            result=operation();elapsed=time.perf_counter()-start
            self.assertIsInstance(result,Ok,repr(result));check(result.value)
            rows.append({'operation':name,'executeCalls':len(statements),'driverWaitCalls':len(waits),
                'seconds':elapsed,'sql':list(statements)})
        try:
            measure('read_by_business_key',lambda:assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','row-0'),original_document=source),lambda value:self.assertIsInstance(value,ObjectFound))
            measure('list_page_51',lambda:assembly.page_objects_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',limit=51),lambda value:self.assertEqual(len(value.objects),51))
            measure('type_enumeration',lambda:assembly.reader_catalog_in_transaction(tx),lambda value:self.assertEqual(len(value.modules),1))
            measure('conditional_catalog_hit',lambda:assembly.reader_catalog_if_changed_in_transaction(tx,validator=conditional.validator),lambda value:self.assertEqual(value.validator,conditional.validator))
            measure('prepare_group',lambda:assembly.prepare_group_in_transaction(tx,records=(('adoc','m','A'),('adoc','m','B')),relationships=(('adoc','m','A-B'),)),lambda value:self.assertIsNotNone(value))
            measure('compiled_singleton_complete_entity',lambda:assembly.query_in_transaction(tx,**arguments),lambda value:self.assertEqual(len(value.rows),1))
            measure('combined_catalog_source_singleton',lambda:assembly.query_with_catalog_in_transaction(tx,**arguments,catalog_validator=conditional.validator),lambda value:self.assertEqual(len(value.result.rows),1))
            single=context.input((self.create(label='single',alias='single'),),MapValue(entries=()))
            measure('single_effect_apply',lambda:assembly.apply_in_transaction(tx,single,RequestNone(),documents=self.documents),lambda value:self.assertIsInstance(value,GroupSuccess))
            # Measure the group as the first write in its own adopted caller
            # transaction, rather than borrowing the single write's warm state.
            connection.wait=original_wait;host.detach();connection.commit()
            connection,host,assembly,tx=self.consumer()
            context=assembly.group_context_in_transaction(tx).value
            original_wait=connection.wait;connection.wait=waited
            operations=(self.create(label='group-A',alias='A'),self.create(label='group-B',alias='B',record='B'),
                CreateEdge(relationship_definition_pin=relationship.definition_pin,source=AliasObjectReference(alias='A'),target=AliasObjectReference(alias='B'),values=(),order_key=NullOrderKey()))
            group=context.input(operations,MapValue(entries=()))
            measure('three_effect_apply',lambda:assembly.apply_in_transaction(tx,group,RequestNone(),documents=self.documents),lambda value:self.assertIsInstance(value,GroupSuccess))
        finally:
            counted.stop();connection.wait=original_wait
        for row in rows:
            expected=11 if row['operation'] in ('compiled_singleton_complete_entity','combined_catalog_source_singleton') else 4 if row['operation']=='single_effect_apply' else 3
            self.assertEqual(row['executeCalls'],expected,row['operation'])
        receipt={'scope':'warm local caller connections; writes each first in a separate adopted transaction; one named UMF0.10 document seeded with 51 rootless two-field Records; public API submissions and driver waits; server-internal statements excluded; fixture setup/warmup and settlement excluded',
            'platform':platform.platform(),'python':platform.python_version(),'load':os.getloadavg(),'rows':rows,
            'hostCosts':{'adoption':'not included; transaction already adopted','transactionSetup':'host-supplied; not included','settlement':'host-supplied; not included','connectionAcquisition':'warm existing connection; none'}}
        if os.environ.get('TRUSS_STATEMENT_BUDGET_RECEIPT'):
            Path(os.environ['TRUSS_STATEMENT_BUDGET_RECEIPT']).write_text(json.dumps(receipt,indent=2)+'\n')
        print('HOHFELD_STATEMENT_BUDGETS='+json.dumps([{k:v for k,v in row.items() if k!='sql'} for row in rows]))
