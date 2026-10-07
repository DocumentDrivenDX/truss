"""Direct mutation masks and SET carriers only; no predicate/native authority proof."""
import copy,hashlib,json
from pathlib import Path
root=Path('docs/helix/02-design/contracts');evidence=Path('docs/helix/04-build/evidence/design-audit')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def strings(n):return [x['members']['String']['members']['sval']['value'] for x in n['items']]
specs=[('feed_finalization_clear_parent','feed_tx',[('finalized_generation','null'),('manifest_bytes','null'),('manifest_sha256','null')]),('feed_finalization_clear_members','feed_member',[('delivery_ordinal','null')]),('feed_finalization_assign','feed_member',[('delivery_ordinal',('5','int8'))]),('feed_finalization_publish','feed_tx',[('finalized_generation',('3','int8')),('manifest_bytes',('4','bytea')),('manifest_sha256',('5','bytea'))])]
statements=[];pins=[]
for family in ['feed-finalization-clear','feed-finalization-assign-publish']:
 receipt=json.loads((evidence/(family+'-source.json')).read_text());obs=receipt['observations'][0]
 for field,hashfield in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(obs[field]).read_bytes()).hexdigest()==obs[hashfield],'original '+field)
 model=json.loads(Path(obs['artifactPath']).read_text());statements.extend([s['members']['stmt']['members']['UpdateStmt']['members'] for s in model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items']]);pins.append({k:obs[k] for k in ['path','sourceSha256','artifactPath','artifactSha256']})
def returning(n,table):
 alias='t' if table=='feed_tx' else 'm'
 expected=[('source_epoch','direct'),('feed_profile','direct'),('original_writer_xid','text')]+([('membership_generation','text'),('finalized_generation','text'),('manifest_bytes','hex'),('manifest_sha256','hex')] if table=='feed_tx' else [('registration_address','text'),('delivery_ordinal','text')])
 found=[]
 def col(v):
  require(set(v['members'])=={'ColumnRef'},'direct original result column');x=v['members']['ColumnRef']['members'];require(set(x)=={'fields','location'},'closed result column');parts=strings(x['fields']);require(len(parts)==2 and parts[0]==alias,'original result alias');return parts[1]
 for target in n['returningList']['items']:
  t=target['members']['ResTarget']['members'];require(set(t) in [{'val','location'},{'name','val','location'}],'closed returning target');v=t['val'];require(len(v['members'])==1,'single result expression');kind=next(iter(v['members']))
  if kind=='ColumnRef':name=col(v);form='direct'
  elif kind=='TypeCast':
   x=v['members']['TypeCast']['members'];require(set(x)=={'arg','typeName','location'} and strings(x['typeName']['members']['names'])==['pg_catalog','text'],'exact result text cast');name=col(x['arg']);form='text'
  elif kind=='FuncCall':
   x=v['members']['FuncCall']['members'];require(set(x)=={'funcname','args','funcformat','location'} and strings(x['funcname'])==['pg_catalog','encode'] and x['funcformat']['value']=='COERCE_EXPLICIT_CALL','exact result encoder');args=x['args']['items'];require(len(args)==2,'exact encoder arity');name=col(args[0]);literal=args[1]['members']['A_Const']['members'];require(set(literal)=={'sval','location'} and literal['sval']['members']['sval']['value']=='hex','exact result hex format');form='hex'
  else:raise ValueError('unsupported result expression')
  require(t.get('name',{}).get('value',name)==name+('_hex' if form=='hex' else ''),'original returning name');found.append((name,form))
 require(found==expected,'complete ordered returning descriptor')
def verify(items):
 require(len(items)==4,'complete statement membership')
 for n,(label,table,expected) in zip(items,specs):
  require(set(n)=={'relation','targetList','whereClause','returningList'},'closed update statement')
  relation=n['relation']['members'];require(relation['schemaname']['value']=='truss' and relation['relname']['value']==table,'original relation')
  alias='t' if table=='feed_tx' else 'm';require(relation['alias']['members']['aliasname']['value']==alias,'original alias')
  found=[]
  for target in n['targetList']['items']:
   x=target['members']['ResTarget']['members'];require(set(x)=={'name','val','location'},'simple scalar assignment');val=x['val'];kind=next(iter(val['members']))
   if kind=='A_Const':
    a=val['members']['A_Const']['members'];require(set(a)=={'isnull','location'} and a['isnull']['value'] is True,'exact SQL NULL');carrier='null'
   elif kind=='TypeCast':
    a=val['members']['TypeCast']['members'];require(set(a)=={'arg','typeName','location'},'original cast');types=strings(a['typeName']['members']['names']);require(len(types)==2 and types[0]=='pg_catalog','qualified cast');q=a['arg']['members']['ParamRef']['members'];require(set(q)=={'number','location'},'original parameter');carrier=(q['number']['value'],types[1])
   else:raise ValueError('unsupported SET expression')
   found.append((x['name']['value'],carrier))
  require(found==expected,label+' original direct mutation mask/carriers');returning(n,table)
verify(statements);controls=[]
for label,mutation in [('counter mutation',lambda x:x[0]['targetList']['items'][0]['members']['ResTarget']['members']['name'].update(value='membership_generation')),('original clock mutation',lambda x:x[1]['targetList']['items'][0]['members']['ResTarget']['members']['name'].update(value='original_write_at')),('duplicated assignment',lambda x:x[0]['targetList']['items'].append(copy.deepcopy(x[0]['targetList']['items'][0]))),('wrong ordinal slot',lambda x:x[2]['targetList']['items'][0]['members']['ResTarget']['members']['val']['members']['TypeCast']['members']['arg']['members']['ParamRef']['members']['number'].update(value='4')),('swapped manifest slots',lambda x:x[3]['targetList']['items'][1]['members']['ResTarget']['members']['val']['members']['TypeCast']['members']['arg']['members']['ParamRef']['members']['number'].update(value='5')),('added FROM modifier',lambda x:x[0].update(fromClause={} ))]:
 x=copy.deepcopy(statements);mutation(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
for label,mutation in [('reordered result columns',lambda x:x[0]['returningList']['items'].reverse()),('omitted returned address',lambda x:x[1]['returningList']['items'].pop(3)),('forged returned alias',lambda x:x[3]['returningList']['items'][-1]['members']['ResTarget']['members']['name'].update(value='manifest_bytes_hex'))]:
 x=copy.deepcopy(statements);mutation(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
r={'scope':'Four original direct UPDATE mutation masks, statement-local SET null/parameter/cast carriers and complete ordered RETURNING source projections. Predicates have separate evidence; native descriptors/null behavior, functions/trigger side effects, original authority/resources/native parity remain unqualified.','sourcePins':pins,'statements':4,'controls':controls,'nativeExecution':False,'complete':False}
(evidence/'feed-finalization-masks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'statements':4,'refusals':len(controls),'nativeExecution':False}))
