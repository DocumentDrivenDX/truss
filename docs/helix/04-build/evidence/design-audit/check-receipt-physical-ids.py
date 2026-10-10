"""Authored candidate allocation/capture correspondence only; no native closure."""
import copy, hashlib, json
from pathlib import Path
manifest_path = Path('docs/helix/02-design/models/truss-receipt-candidate.physical-ids.draft.json')
source_path = Path('docs/helix/02-design/contracts/request-receipt-layout-v0.1.draft.sql')
manifest = json.loads(manifest_path.read_text())
baseline = json.loads(Path('docs/helix/02-design/models/truss-layout-0.2.physical-ids.draft.json').read_text())
def field(node, key):
    value = node.get('members', {}).get(key)
    if not value or value.get('kind') != 'string': raise ValueError('missing original string '+key)
    return value['value']
def validate(value):
    errors=[]
    entries=value['entries']; by_id={e['entryId']:e for e in entries}
    if len(by_id)!=len(entries): errors.append('duplicate authored IDs')
    if set(by_id)&{e['entryId'] for e in baseline['entries']}: errors.append('baseline ID collision')
    if value.get('complete') is not False: errors.append('overclaimed complete closure')
    if value['sourceSha256']!=hashlib.sha256(source_path.read_bytes()).hexdigest(): errors.append('source hash drift')
    for e in entries:
        try:
            locator=e['capturedModelLocator']; raw=Path(locator['modelPath']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=locator['modelSha256']: raise ValueError('model hash drift')
            node=json.loads(raw)
            for part in locator['jsonPointer'].split('/')[1:]:
                part=part.replace('~1','/').replace('~0','~')
                node=node[int(part)] if isinstance(node,list) else node[part]
            kind=e['objectKind']; identity=e['nativeIdentity']
            if node.get('kind')!='object': raise ValueError('not native object')
            if kind=='column':
                if field(node,'colname')!=identity['name']: raise ValueError('wrong column')
                parent=by_id[e['parentEntryId']]
                if parent['objectKind']!='table' or parent['nativeIdentity']!={'schema':identity['schema'],'name':identity['table']}: raise ValueError('wrong parent ownership')
                parent_pointer=parent['capturedModelLocator']['jsonPointer']
                if not locator['jsonPointer'].startswith(parent_pointer+'/members/tableElts/items/'): raise ValueError('column outside parent capture')
            elif kind=='index' and e.get('origin')=='implicit-primary-index':
                constraint=by_id[e['parentConstraintEntryId']]
                if constraint['objectKind']!='constraint' or constraint['nativeIdentity']['kind']!='CONSTR_PRIMARY': raise ValueError('implicit index lacks primary constraint owner')
                if constraint['parentEntryId']!=e['parentEntryId'] or constraint['capturedModelLocator']!=locator: raise ValueError('implicit index creating source/parent drift')
                if identity!={'schema':constraint['nativeIdentity']['schema'],'table':constraint['nativeIdentity']['table'],'name':None}: raise ValueError('invented implicit index binding')
                if e['nativeNameResolution']!='unresolved-catalog-binding' or field(node,'contype')!='CONSTR_PRIMARY': raise ValueError('unqualified implicit index resolution')
                if e['expectedSemantics']['method']!='btree' or e['expectedSemantics']['unique'] is not True: raise ValueError('wrong implicit primary index semantics')
            elif kind=='constraint':
                parent=by_id[e['parentEntryId']]
                if parent['objectKind']!='table' or parent['nativeIdentity']!={'schema':identity['schema'],'name':identity['table']}: raise ValueError('wrong constraint table owner')
                parent_pointer=parent['capturedModelLocator']['jsonPointer']
                if not locator['jsonPointer'].startswith(parent_pointer+'/members/tableElts/items/'): raise ValueError('constraint outside table capture')
                if field(node,'contype')!=identity['kind']: raise ValueError('wrong native constraint kind')
                original_name=node['members'].get('conname',{}).get('value')
                if original_name!=identity['name']: raise ValueError('wrong native constraint name')
                if e['nativeNameResolution']!=('explicit-source' if original_name else 'unresolved-generated-name'): raise ValueError('invented native name resolution')
                marker='/members/ColumnDef/members/constraints/items/'
                if marker in locator['jsonPointer']:
                    ancestor=json.loads(raw)
                    cp=locator['jsonPointer'].split(marker)[0]+'/members/ColumnDef'
                    for part in cp.split('/')[1:]: ancestor=ancestor[int(part)] if isinstance(ancestor,list) else ancestor[part]
                    if field(ancestor,'colname')!=identity.get('column'): raise ValueError('wrong constraint column owner')
                elif 'column' in identity: raise ValueError('invented column owner')
            else:
                relation=node['members']['sequence' if kind=='sequence' else 'relation']
                if field(relation,'schemaname')!=identity['schema']: raise ValueError('wrong schema')
                if kind=='index':
                    if field(node,'idxname')!=identity['name'] or field(relation,'relname')!=identity['table']: raise ValueError('wrong index owner/name')
                elif kind in ('table','sequence'):
                    if field(relation,'relname')!=identity['name']: raise ValueError('wrong native name')
                else: raise ValueError('unknown allocation kind')
        except (ValueError,KeyError,IndexError,TypeError) as error: errors.append(e['entryId']+': '+str(error))
    return errors
failures=validate(manifest)
controls=[]
def reject(name, mutate):
    value=copy.deepcopy(manifest);mutate(value)
    controls.append(name)
    if not validate(value): failures.append('negative control admitted: '+name)
reject('duplicate ID',lambda v:v['entries'].append(copy.deepcopy(v['entries'][0])))
reject('wrong native schema',lambda v:v['entries'][0]['nativeIdentity'].update(schema='other'))
reject('wrong source hash',lambda v:v.update(sourceSha256='0'*64))
reject('wrong model hash',lambda v:v['entries'][0]['capturedModelLocator'].update(modelSha256='0'*64))
reject('overclaimed complete',lambda v:v.update(complete=True))
column_index=next(i for i,e in enumerate(manifest['entries']) if e['objectKind']=='column')
reject('missing parent',lambda v:v['entries'][column_index].update(parentEntryId='missing'))
reject('wrong native column pointer',lambda v:v['entries'][column_index]['capturedModelLocator'].update(jsonPointer=v['entries'][0]['capturedModelLocator']['jsonPointer']))
constraint_index=next(i for i,e in enumerate(manifest['entries']) if e['objectKind']=='constraint')
reject('wrong constraint kind',lambda v:v['entries'][constraint_index]['nativeIdentity'].update(kind='CONSTR_UNIQUE'))
reject('invented constraint native name',lambda v:v['entries'][constraint_index]['nativeIdentity'].update(name='invented'))
reject('invented constraint name resolution',lambda v:v['entries'][constraint_index].update(nativeNameResolution='qualified-native'))
implicit_index=next(i for i,e in enumerate(manifest['entries']) if e.get('origin')=='implicit-primary-index')
reject('missing implicit index creator',lambda v:v['entries'][implicit_index].update(parentConstraintEntryId='missing'))
reject('invented implicit index name',lambda v:v['entries'][implicit_index]['nativeIdentity'].update(name='guessed'))
reject('wrong implicit uniqueness',lambda v:v['entries'][implicit_index]['expectedSemantics'].update(unique=False))
receipt={'scope':'Candidate authored ID, exact source/model hash, tagged native node and parent correspondence only; native definitions/implicit objects/full allocation/exporter closure unqualified','entries':len(manifest['entries']),'negativeControls':controls,'failures':failures}
Path('docs/helix/04-build/evidence/design-audit/receipt-physical-ids.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));raise SystemExit(bool(failures))
