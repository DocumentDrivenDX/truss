"""Independent explicit declaration expectations only; no native installation proof."""
import copy,hashlib,json
from pathlib import Path
def require(ok,message):
    if not ok: raise ValueError(message)
def names(items): return [i['String']['sval'] for i in items]
parent='truss.row_home_operation';stage='truss.row_home_journal_stage'
expected={parent:['original_writer_xid','operation_ordinal','operation_kind','phase','effect_generation','readiness_generation','sealed_generation','application_generation','original_context_bytes','original_definition_bytes','original_input_bytes','original_prestate_bytes','admitted_candidate_bytes','effect_obligation_bytes','original_group_custody_bytes','application_result_bytes'],stage:['original_writer_xid','operation_ordinal','stage_name','stage_ordinal','effect_generation','body_bytes']}
v=json.loads(Path('docs/helix/04-build/evidence/design-audit/journal-stage-declaration-inventory.json').read_text())
for item in v['inputs']: require(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],'stale source')
def verify(entries):
    require(len(entries)==35 and len({e['id'] for e in entries})==35,'entry count/identity')
    for table,columns in expected.items():
        actual=[e['originalDeclaration'] for e in entries if e['kind']=='column' and e['parent']==table]
        require([c['colname'] for c in actual]==columns,'complete ordered columns')
        if table==stage:
            require(all(any(n['Constraint']['contype']=='CONSTR_NOTNULL' for n in c.get('constraints',[])) for c in actual),'stage NOT NULL')
    constraints={e['id']:e['originalDeclaration'] for e in entries if e['kind']=='constraint'}
    require(names(constraints[parent+'.row_home_operation_pk']['keys'])==['original_writer_xid','operation_ordinal'],'parent key')
    require(names(constraints[stage+'.row_home_journal_stage_pk']['keys'])==['original_writer_xid','operation_ordinal','stage_name','stage_ordinal'],'stage key')
    fk=constraints[stage+'.row_home_journal_stage_operation_fk']
    require(names(fk['fk_attrs'])==names(fk['pk_attrs'])==['original_writer_xid','operation_ordinal'],'typed original parent association')
    require(fk['pktable']['schemaname']=='truss' and fk['pktable']['relname']=='row_home_operation' and fk['fk_del_action']=='r' and fk['initially_valid'] is True,'validated restrictive original FK')
verify(v['entries']);negative=[]
for name in ['missing_original_column','duplicate_identity','reversed_parent_key','substituted_fk_parent','cascade_delete']:
    bad=copy.deepcopy(v['entries'])
    if name=='missing_original_column': del bad[1]
    elif name=='duplicate_identity': bad[1]['id']=bad[0]['id']
    else:
        target=next(e for e in bad if e['id']==(parent+'.row_home_operation_pk' if name=='reversed_parent_key' else stage+'.row_home_journal_stage_operation_fk'))['originalDeclaration']
        if name=='reversed_parent_key': target['keys'].reverse()
        elif name=='substituted_fk_parent': target['pktable']['relname']='another_operation'
        else: target['fk_del_action']='c'
    try: verify(bad)
    except ValueError: negative.append(name)
    else: raise ValueError('missed corruption '+name)
print(json.dumps({'scope':'independent explicit column/key/FK expectations and corruption controls only','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inventorySha256':hashlib.sha256(Path('docs/helix/04-build/evidence/design-audit/journal-stage-declaration-inventory.json').read_bytes()).hexdigest(),'explicitEntries':35,'negativeControls':negative,'nativeExecuted':False,'installationReady':False},indent=2))
