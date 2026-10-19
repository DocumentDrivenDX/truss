# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public typed relationship-key predicates and projections."""
import os
from decimal import Decimal
from truss import Ok,QueryRows,QueryRelatedKeys,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly
from truss.contracts import TextValue,BooleanValue,MapValue
from truss.groups import CreateObject,CreateEdge,AuthoredValue,RootlessOwnership,AliasObjectReference,NullOrderKey,GroupSuccess
import test_group_create_native as create_tests

class TypedRelationshipKeysTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.7.0'
    def fields(self,source):
        source['umf']=self.source_version;m=source['modules'][0]
        for e in m['elements']:
            if e['kind']=='record':e['name']=e['id']
            elif e['id']=='B-value':e['scalarType']='integer';e['facets']={'integerWidth':{'bits':64,'signed':True}}
            elif e['id']=='B-label':e['scalarType']='decimal';e['facets']={'precision':18,'scale':4}
        b=next(e for e in m['elements'] if e['id']=='B')
        m['elements'].append({'id':'B-active','name':'B-active','kind':'field','scalarType':'boolean','cardinality':'one','nullability':'required','extensions':{}})
        ref={'module':'m','element':'B-active'};b['members'].append(ref);next(k for k in b['keys'] if k.get('primary'))['fields'].append(ref)
        m['relationships'][0]['inverse']='B-A'
    def test_public_typed_predicate_lists_complete_entity_and_readonly(self):
        c,h,a,t=self.ready(self.fields)
        pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        def target(alias,integer,decimal,active):
            return CreateObject(type_definition_pin=self.types[('adoc','B')].definition_pin,values=(AuthoredValue(name='B-value',value=TextValue(kind='integer',text=integer)),AuthoredValue(name='B-label',value=TextValue(kind='decimal',text=decimal)),AuthoredValue(name='B-active',value=BooleanValue(value=active))),ownership=RootlessOwnership(),alias=alias)
        operations=(self.create('one',alias='source'),target('low','-9007199254740993','1.23000',False),target('high','9007199254740993','2.0000',True),CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='source'),target=AliasObjectReference(alias='low'),values=(),order_key=NullOrderKey()),CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='source'),target=AliasObjectReference(alias='high'),values=(),order_key=NullOrderKey()))
        context=a.group_context_in_transaction(t).value
        result=self.apply(a,t,context.input(operations,MapValue(entries=())),context.request('typed-links'));self.assertIsInstance(result,GroupSuccess)
        def query(sql,parameters=None,profile=None):
            result=a.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={} if parameters is None else parameters,read_profile=profile)
            self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,QueryRows,repr(result.value));return result.value
        predicate='SELECT COUNT(*) FROM "A" a WHERE HAS_RELATED(a."A-B",KEY(:i,:d,:b))'
        parameters={'i':-9007199254740993,'d':Decimal('1.2300'),'b':False}
        self.assertEqual(query(predicate,parameters).rows,((1,),))
        bounded='SELECT RELATED_KEYS(a."A-B",1) AS related FROM "A" a'
        expected=QueryRelatedKeys(items=((-9007199254740993,Decimal('1.23000'),False),),truncated=True)
        self.assertEqual(query(bounded).rows,((expected,),));self.assertEqual(str(query(bounded).rows[0][0].items[0][1]),'1.23000')
        complete=query('SELECT a.* FROM "A" a',profile='complete-entity');row=dict(zip(complete.columns,complete.rows[0],strict=True))
        self.assertEqual(row['A-B'],((-9007199254740993,Decimal('1.23000'),False),(9007199254740993,Decimal('2.0000'),True)))
        h.detach();c.commit();c,h,a,t=self.consumer();h.detach();c.execute('SET TRANSACTION READ ONLY')
        h=adopt_psycopg_host(c);self.addCleanup(h.detach);a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction(access_mode='read_only').value
        self.assertEqual(query(predicate,parameters).rows,((1,),));self.assertEqual(query(bounded).rows,((expected,),))
        h.detach();c.rollback()

class TypedRelationshipKeys08Tests(TypedRelationshipKeysTests):
    source_version='0.8.0'
