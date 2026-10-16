"""Deterministic schemas and values for the practical Truss stress matrix."""
import json
from pathlib import Path

MATRIX=Path(__file__).resolve().parents[1]/'docs/helix/03-test/performance/workloads.json'

def workloads():
    return {case['id']:case for case in json.loads(MATRIX.read_text())['cases']}

# Keep potential indexed columns identical across nominal and index-heavy cases.
INDEX_CANDIDATE_FIELDS=max(case['indexedPropertiesPerType'] for case in workloads().values())

def schema(case):
    elements=[];relationships=[]
    for t in range(case['types']):
        record='R'+str(t);members=[]
        for p in range(case['fieldsPerType']):
            identity=record+'.p'+str(p)
            field={'id':identity,'name':'p'+str(p),'kind':'field','cardinality':'one','nullability':'required','extensions':{}}
            family='string'
            if case['shape']!='scalar' and p>=max(INDEX_CANDIDATE_FIELDS,case['indexedPropertiesPerType']):
                family=('integer','decimal','boolean','string')[(p-8)%4]
            field['scalarType']=family
            if family=='decimal':field['facets']={'precision':18,'scale':4}
            if p==case['fieldsPerType']-1 and case['shape']=='mixed-nested':
                field.pop('scalarType');field.pop('facets',None)
                field.update(cardinality='map',itemType={'module':'m','element':record+'.items'})
                elements.extend([
                    {'id':record+'.items','name':record+'.items','kind':'field','cardinality':'array','nullability':'required','itemType':{'module':'m','element':record+'.decimal'},'extensions':{}},
                    {'id':record+'.decimal','name':record+'.decimal','kind':'field','cardinality':'one','nullability':'required','scalarType':'decimal','facets':{'precision':18,'scale':4},'extensions':{}}])
            elif p>=max(INDEX_CANDIDATE_FIELDS,case['indexedPropertiesPerType']) and p%7==6:field['nullability']='absent-allowed'
            elements.append(field);members.append({'module':'m','element':identity})
        keys=[{'id':'key'+str(p),'name':'key'+str(p),'fields':[members[p]],'primary':p==0} for p in range(case['indexedPropertiesPerType'])]
        elements.append({'id':record,'name':record,'kind':'record','members':members,'keys':keys,'extensions':{}})
        relationships.append({'id':record+'.link','name':record+'.link','source':[{'module':'m','element':record}],
            'target':[{'module':'m','element':record,'key':'key0'}],'sourceMultiplicity':{'min':0,'max':'*'},'targetMultiplicity':{'min':0,'max':'*'},'targetLifecycle':'independent','directed':True,'extensions':{}})
    return {'umf':'0.7.0','id':'perf-'+case['id'],'vocabularies':{},'extensions':{},
            'modules':[{'id':'m','namespace':'m','elements':elements,'relationships':relationships,'extensions':{}}]}

def values(case,row):
    from truss.contracts import TextValue,BooleanValue,MapValue,MapEntry,SequenceValue
    from truss.groups import AuthoredValue
    result=[]
    for p in range(case['fieldsPerType']):
        if p>=max(INDEX_CANDIDATE_FIELDS,case['indexedPropertiesPerType']) and p%7==6 and row%3==0:continue
        family='string'
        if case['shape']!='scalar' and p>=max(INDEX_CANDIDATE_FIELDS,case['indexedPropertiesPerType']):family=('integer','decimal','boolean','string')[(p-8)%4]
        if p==case['fieldsPerType']-1 and case['shape']=='mixed-nested':
            value=MapValue(entries=(MapEntry(key='items',value=SequenceValue(items=tuple(TextValue(kind='decimal',text=str(row+j)+'.2300') for j in range(3)))),))
        elif family=='boolean':value=BooleanValue(value=bool(row%2))
        elif family in ('integer','decimal'):value=TextValue(kind=family,text=str(row)+('.2300' if family=='decimal' else ''))
        else:value=TextValue(kind='string',text=('Record '+str(row)) if p==1 else ('p'+str(p)+'-'+str(row)))
        result.append(AuthoredValue(name='p'+str(p),value=value))
    return tuple(result)

def edges(case):
    """Unique same-type pairs; the skew case concentrates source fanout."""
    groups=[list(range(t,case['nodes'],case['types'])) for t in range(case['types'])]
    for ordinal in range(case['edges']):
        t=ordinal%case['types'];rows=groups[t];n=len(rows)
        if n<2:raise ValueError('Edge workload requires at least two nodes per type')
        local=ordinal//case['types']
        if case['distribution']=='95_percent_edges_on_1_percent_nodes':
            hot=max(1,n//100);hot_total=(case['edges']//case['types'])*95//100
            if local<hot_total:
                source=local%hot;target=(local//hot+source+1)%n
            else:
                cold=local-hot_total;source=hot+cold%(n-hot);target=(cold//(n-hot)+source+1)%n
        else:source=local%n;target=(local//n+source+1)%n
        yield t,rows[source],rows[target]
