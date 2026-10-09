"""Authored bounded layout delta; refuses any additional native source change."""
from pathlib import Path
import copy,hashlib,json,sys
root=Path(__file__).resolve().parents[3]
def load(p):return json.loads((root/p).read_text())
def digest(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
a='04-build/evidence/design-audit/core-refresh-0.12.native-ast.json';b='04-build/evidence/design-audit/core-refresh-0.15.native-ast.json'
x=load(a);y=load(b);assert len(x)==106 and len(y)==109
assert [i for i in range(106) if x[i]!=y[i]]==[1,76]
assert list(x[1]['stmt'])==list(y[1]['stmt'])==['CommentStmt']
expected_comment=copy.deepcopy(x[1]);expected_comment['stmt']['CommentStmt']['comment']=y[1]['stmt']['CommentStmt']['comment'];assert expected_comment==y[1]
oldtable=x[76]['stmt']['CreateStmt'];newtable=y[76]['stmt']['CreateStmt']
assert oldtable['relation']==newtable['relation'] and newtable['relation']['relname']=='installation_archive'
assert {k:v for k,v in oldtable.items() if k!='tableElts'}=={k:v for k,v in newtable.items() if k!='tableElts'}
changes=[i for i,(old,new) in enumerate(zip(oldtable['tableElts'],newtable['tableElts'])) if old!=new]
assert len(oldtable['tableElts'])==len(newtable['tableElts']) and len(changes)==1
changed=changes[0];column=newtable['tableElts'][changed]['ColumnDef'];assert column['colname']=='artifact_identity_sha256'
assert [c['Constraint']['contype'] for c in column['constraints']]==['CONSTR_NOTNULL','CONSTR_CHECK']
assert {k:v for k,v in column['typeName'].items() if k!='location'}=={k:v for k,v in oldtable['tableElts'][changed]['ColumnDef']['typeName'].items() if k!='location'}
assert column.get('collClause')==oldtable['tableElts'][changed]['ColumnDef'].get('collClause')
assert column['constraints'][1]['Constraint']['conname']=='installation_archive_identity_digest_exact'
cmds=[]
for node in y[106:]:
 stmt=node['stmt']['AlterTableStmt'];assert stmt['relation']['schemaname']=='truss' and stmt['relation']['relname']=='prop_def' and len(stmt['cmds'])==1
 cmds.append(stmt['cmds'][0]['AlterTableCmd'])
assert [c['subtype'] for c in cmds]==['AT_AddColumn','AT_DropConstraint','AT_AddConstraint']
added=cmds[0]['def']['ColumnDef'];assert added['colname']=='declaration_module'
assert [n['String']['sval'] for n in added['typeName']['names']]==['text']
assert [n['String']['sval'] for n in added['collClause']['collname']]==['pg_catalog','C']
assert [c['Constraint']['contype'] for c in added['constraints']]==['CONSTR_NOTNULL','CONSTR_CHECK']
assert cmds[1]['name']=='prop_def_type_id_element_key' and cmds[1]['behavior']=='DROP_RESTRICT'
unique=cmds[2]['def']['Constraint'];assert unique['conname']=='prop_def_qualified_field' and unique['contype']=='CONSTR_UNIQUE'
assert [s['String']['sval'] for s in unique['keys']]==['type_id','declaration_module','element']
source='02-design/models/truss-layout-qualified-property-0.15.proposal.umf.json';prior='02-design/models/truss-layout-core-structural-0.2.proposal.umf.json'
model=load(source);module=copy.deepcopy(next(m for m in load(prior)['modules'] if m['id']=='truss-layout'))
field=next(e for e in module['elements'] if e['id']=='installation_archive.artifact_identity_sha256')
field['nullability']='required';meta=field['extensions']['truss.layout.native'];meta.update({'sourcePointer':f'/76/stmt/CreateStmt/tableElts/{changed}/ColumnDef','constraints':column['constraints'],'nativeType':column['typeName'],'collation':column.get('collClause')})
ref=lambda e:{'module':module['id'],'element':e}
newid='prop_def.declaration_module'
module['elements'].append({'id':newid,'name':'declaration_module','kind':'field','scalarType':'string','cardinality':'one','nullability':'required','extensions':{'truss.layout.native':{'sourcePointer':'/106/stmt/AlterTableStmt/cmds/0/AlterTableCmd/def/ColumnDef','nativeType':added['typeName'],'constraints':added['constraints'],'collation':added.get('collClause'),'sqlNullMeaning':'retained-native-constraints; not core absence'}}})
record=next(e for e in module['elements'] if e['id']=='prop_def');record['members'].append(ref(newid));record['references'].append({'role':'member',**ref(newid)})
oldkeys=[k for k in record['keys'] if [f['element'] for f in k['fields']]==['prop_def.type_id','prop_def.element']];assert len(oldkeys)==1
record['keys'].remove(oldkeys[0]);record['keys'].append({'id':unique['conname'],'name':unique['conname'],'fields':[ref('prop_def.'+s['String']['sval']) for s in unique['keys']],'primary':False})
model['umf']='0.7.0';model['id']='truss-layout-core-structural-0.3-current-review';model['modules'].append(module)
model.setdefault('vocabularies',{})['truss.layout.native']={'version':'0.1.0'}
model.setdefault('extensions',{})['truss.layout.native']={'sourceModel':source,'sourceSha256':digest(source),'structuralSource':prior,'structuralSourceSha256':digest(prior),'nativeAstSha256':digest(b),'scope':'Current 0.15 authored structural mirror with exact native archive; physical-only key/FK semantics remain explicitly uninterpreted. No SQL generation or installed identity adoption.'}
assert len([e for e in module['elements'] if e.get('kind')=='record'])==46 and len([e for e in module['elements'] if e.get('kind')=='field'])==443
assert sum(len(e.get('keys',[])) for e in module['elements'])==48 and len(module['relationships'])==57
out='02-design/models/truss-layout-core-structural-0.3.proposal.umf.json';text=json.dumps(model,separators=(',',':'),ensure_ascii=False)+'\n'
if '--check' in sys.argv:assert (root/out).read_text()==text
else:(root/out).write_text(text)
receipt={'scope':model['extensions']['truss.layout.native']['scope'],'nativeSource':source,'nativeSourceSha256':digest(source),'priorStructuralSource':prior,'priorStructuralSourceSha256':digest(prior),'nativeAstPaths':[a,b],'nativeAstSha256':[digest(a),digest(b)],'changedOriginalStatements':[1,76],'appendedStatements':[106,107,108],'modelPath':out,'modelSha256':hashlib.sha256(text.encode()).hexdigest(),'records':46,'fields':443,'portableKeys':48,'coreRelationships':57,'physicalFkReferences':4}
r=root/'04-build/evidence/design-audit/core-current-refresh-source.json'
if '--check' in sys.argv:assert json.loads(r.read_text())==receipt
else:r.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'records':46,'fields':443,'nativeStatements':109,'scope':'current 0.15 source structural mirror only'}))
