# SPDX-License-Identifier: MIT OR Apache-2.0
"""Independent native correspondence for the trusted application value compiler."""
import json,random,unittest
import test_catalog_runtime_native as base
from truss.contracts import TextValue,BooleanValue,NullValue,SequenceValue,MapValue,MapEntry
from truss.groups import AuthoredValue
from truss import _record_schema as mod

def wire(v):
    if type(v) is TextValue:return {'kind':v.kind,'text':v.text}
    if type(v) is BooleanValue:return {'kind':'boolean','value':v.value}
    if type(v) is NullValue:return {'kind':'null'}
    if type(v) is SequenceValue:return {'kind':'sequence','items':[wire(c) for c in v.items]}
    if type(v) is MapValue:return {'kind':'map','entries':[{'key':e.key,'value':wire(e.value)} for e in v.entries]}
    raise TypeError(v)

class RecordSchemaOracleTests(base.PublicCatalogRuntimeTests):
    for n in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[n]=None
    def test_parity(self):
        self.install();cases=[]
        tokens={
          'string':['','abc','é','😇','a\n','a'*4096],
          'integer':['0','-0','1','-1','00','+1','1.0','1e0',' 1','1\n',str(2**63-1),str(2**63),str(-2**63),str(-2**63-1),'9'*400],
          'decimal':['0','-0','00','1','1.0','1.2300','0.001','1e0','1e-9','1e+9','0e99999999999999999999','1e99999999999999999999','.1','1.','1\n','NaN','Infinity'],
          'binary':['','YQ==','YQ','YR==','YWJj','YWJj\n','é','===='],
          'date':['0001-01-01','9999-12-31','2000-02-29','1900-02-29','0000-01-01','2024-04-31','2024-1-01','2024-01-01\n'],
          'timestamp':['2000-02-29T23:59:59Z','1900-02-29T00:00:00Z','0000-01-01T00:00:00Z','9999-12-31t23:59:59.000000000001z','2024-01-01T00:00:00-00:00','2024-01-01T00:00:00+23:59','2024-01-01T00:00:00+24:00','2024-01-01T24:00:00Z','2024-01-01T23:59:60Z','2024-01-01T00:00:00.Z','2024-01-01T00:00:00Z\n']}
        rng=random.Random(60206)
        tokens['decimal'] += [('-' if rng.randrange(2) else '')+str(rng.randrange(100000))+'.'+str(rng.randrange(100000)).zfill(5)+'e'+str(rng.randrange(-12,13)) for _ in range(200)]
        for family,ts in tokens.items():
            facets=[{}]
            if family=='integer':facets+=[{'integerWidth':{'bits':64,'signed':True}}]
            if family=='decimal':facets += [{'precision':p,'scale':s} for p,s in [(1,0),(3,2),(12,2),(30,16)]]
            for f in facets:
                for allow in [False,True]:
                    for value in [*(TextValue(kind=family,text=t) for t in ts),NullValue(),BooleanValue(value=True)]:
                        cases.append({'cell':wire(value),'family':family,'allow':allow,'facets':f,'python':mod._scalar(value,family,f,allow)})
        for allow in [False,True]:
            for value in [BooleanValue(value=True),BooleanValue(value=False),TextValue(kind='string',text='true'),NullValue()]:
                cases.append({'cell':wire(value),'family':'boolean','allow':allow,'facets':{},'python':mod._scalar(value,'boolean',{},allow)})
        rows=self.admin.execute("SELECT (ordinality-1)::int,truss.valid_scalar_property(value->'cell',value->>'family',(value->>'allow')::boolean,value->'facets') FROM jsonb_array_elements(%s::jsonb) WITH ORDINALITY",(json.dumps(cases),)).fetchall()
        mismatches=[{**cases[i],'native':native} for i,native in rows if cases[i]['python'] is not native]
        # Compare synthetic typed rows without changing native validators or data.
        containers=[];pin='a'*64
        leaf={'reference':{'module':'m','element':'leaf'},'declaration':{'kind':'field','cardinality':'one','nullability':'required','scalarType':'string'}}
        for cardinality in ['array','map']:
            prop={'prop_id':1,'name':'items','cardinality':cardinality,'nullability':'required','scalar_type':None,'home':'json','facets':{},'item':leaf}
            schema=mod.compile_records([{'typeId':'1','definitionPin':pin,'properties':[prop]}])
            vals=[NullValue(),TextValue(kind='string',text='bad')]
            for size in [0,1,1024,1025,4096]:
                if cardinality=='array':vals.append(SequenceValue(items=tuple(TextValue(kind='string',text='x') for _ in range(size))))
                else:vals.append(MapValue(entries=tuple(MapEntry(key=str(i),value=TextValue(kind='string',text='x')) for i in range(size))))
            if cardinality=='map':vals.append(MapValue(entries=(MapEntry(key='a',value=TextValue(kind='string',text='x')),MapEntry(key='a',value=TextValue(kind='string',text='y')))))
            for value in vals:
                predicted=schema.validate_values('1',pin,(AuthoredValue(name='items',value=value),)).valid
                containers.append({'cell':wire(value),'property':prop,'python':predicted})
        # Original recursive declarations exercise all admitted levels without
        # flattening the value or inferring a missing item definition.
        for depth in (1,2,8,32):
            nodes=[]
            for level in range(depth):
                declaration={'kind':'field','nullability':'required'}
                if level==depth-1:declaration.update(cardinality='one',scalarType='string')
                else:declaration.update(cardinality='array' if level%2 else 'map',itemType={'module':'m','element':'item'+str(level+1)})
                nodes.append({'reference':{'module':'m','element':'item'+str(level)},'declaration':declaration})
            item={**nodes[0],'descendants':nodes[1:]}
            prop={'prop_id':1,'name':'items','cardinality':'array','nullability':'required','scalar_type':None,'home':'json','facets':{},'item':item}
            schema=mod.compile_records([{'typeId':'1','definitionPin':pin,'properties':[prop]}])
            value=TextValue(kind='string',text='leaf')
            for node in reversed(nodes[:-1]):
                value=SequenceValue(items=(value,)) if node['declaration']['cardinality']=='array' else MapValue(entries=(MapEntry(key='key',value=value),))
            value=SequenceValue(items=(value,))
            containers.append({'cell':wire(value),'property':prop,'python':schema.validate_values('1',pin,(AuthoredValue(name='items',value=value),)).valid})
        # Each array respects 1,024 members; the whole value crosses 4,096 nodes.
        branch={'reference':{'module':'m','element':'branch'},'declaration':{'kind':'field','cardinality':'array','nullability':'required','itemType':leaf['reference']},'descendants':[leaf]}
        prop={'prop_id':1,'name':'items','cardinality':'array','nullability':'required','scalar_type':None,'home':'json','facets':{},'item':branch}
        schema=mod.compile_records([{'typeId':'1','definitionPin':pin,'properties':[prop]}])
        for leaves in (1022,1023):
            child=SequenceValue(items=tuple(TextValue(kind='string',text='x') for _ in range(leaves)))
            value=SequenceValue(items=(child,)*4)
            containers.append({'cell':wire(value),'property':prop,'python':schema.validate_values('1',pin,(AuthoredValue(name='items',value=value),)).valid})
        # Each independently admitted value has the ordinary SQL deadline. Do
        # not combine the entire correctness corpus into one timed operation;
        # identify the exact input if one native validator call times out.
        def cell_nodes(cell):
            kind=cell.get('kind')
            if kind=='sequence':return 1+sum(cell_nodes(item) for item in cell['items'])
            if kind=='map':return 1+sum(1+cell_nodes(entry['value']) for entry in cell['entries'])
            return 1
        rows=[]
        for i,case in enumerate(containers):
            cell=case['cell'];members=len(cell.get('items',cell.get('entries',[])))
            with self.subTest(container_case=i,cardinality=case['property']['cardinality'],
                    members=members,cell_nodes=cell_nodes(cell),cell_bytes=len(json.dumps(cell))):
                native=self.admin.execute(
                    'SELECT truss.valid_property_value(%s::jsonb,jsonb_populate_record(NULL::truss.prop_def,%s::jsonb))',
                    (json.dumps(cell),json.dumps(case['property']))).fetchone()[0]
                rows.append((i,native))
        cm=[{'case':i,'cardinality':containers[i]['property']['cardinality'],'members':len(containers[i]['cell'].get('items',containers[i]['cell'].get('entries',[]))),'python':containers[i]['python'],'native':native} for i,native in rows if containers[i]['python'] is not native]
        self.assertFalse(cm,cm)

        self.assertFalse(mismatches,mismatches)

    def test_prepared_known_and_retained_maps_match_native_canonical_cells(self):
        self.install();pin='a'*64
        leaf={'reference':{'module':'m','element':'leaf'},'declaration':{'kind':'field','cardinality':'one','nullability':'required','scalarType':'string'}}
        prop={'prop_id':1,'name':'known','cardinality':'map','nullability':'required','scalar_type':None,'home':'json','facets':{},'item':leaf}
        schema=mod.compile_records([{'typeId':'1','definitionPin':pin,'properties':[prop]}])
        value=MapValue(entries=tuple(MapEntry(key=k,value=TextValue(kind='string',text=k)) for k in ('z','😇','é','a','')))
        patch=schema.prepare_patch('1',pin,(AuthoredValue(name='known',value=value),AuthoredValue(name='future',value=value)),mode='create')
        self.assertTrue(patch.eligible,patch.violations)
        native=self.admin.execute('SELECT truss.canonical_flat_cell(%s::jsonb)',(json.dumps(wire(value)),)).fetchone()[0]
        projected=patch.wire_payload()
        self.assertEqual(projected['propsSet']['1'],native)
        self.assertEqual(projected['retainedSet']['future'],native)
        projected['propsSet']['1']['entries'][0]['value']['text']='changed-copy'
        self.assertEqual(patch.wire_payload()['propsSet']['1'],native)
        self.assertEqual(tuple(entry.key for entry in value.entries),('z','😇','é','a',''))

if __name__ == '__main__':unittest.main()
