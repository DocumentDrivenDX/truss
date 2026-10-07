"""Private touch source AST correspondence; no native authority or execution."""
import copy, hashlib, json
from pathlib import Path
E=Path('docs/helix/04-build/evidence/design-audit')
def require(ok,msg):
    if not ok: raise ValueError(msg)
def decode(n):
    if n['kind']=='object': return {k:decode(v) for k,v in n['members'].items()}
    if n['kind']=='array': return [decode(v) for v in n['items']]
    if n['kind']=='number': return int(n['value'])
    if n['kind']=='null': return None
    return n['value']
def strip(n):
    if isinstance(n,dict): return {k:strip(v) for k,v in n.items() if k!='location'}
    if isinstance(n,list): return [strip(v) for v in n]
    return n
def load(stem,count):
    r=json.loads((E/(stem+'-source.json')).read_text()); o=r['observations'][0]
    for p,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
        require(hashlib.sha256(Path(o[p]).read_bytes()).hexdigest()==o[h],stem+' '+p+' hash')
    m=json.loads(Path(o['artifactPath']).read_text())
    a=decode(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])['stmts']
    require(len(a)==count,'statement membership')
    return [x['stmt'] for x in a],o
obs,observation_proof=load('row-touch-current-writer-observation',1)
writes,wp=load('row-touch-create-and-seal',2)
advance,ap=load('row-touch-generation-advance',1)
expected=['transaction_id','owner_kind','owner_id','owner_discriminator_id','property_owner_type_id','property_id','dirty_generation','sealed_generation','original_layout_bytes_hex','original_home_bytes_hex','original_owner_property_bytes_hex','original_operation_bytes_hex']
s=obs[0]['SelectStmt']; projection=s['targetList']; identity=s['whereClause']['BoolExpr']['args']
require(len(identity)==6,'complete independently expected six-part identity')
require([x['ResTarget']['name'] for x in projection]==expected,'independent snapshot aliases')
def strings(*names): return [{'String':{'sval':x}} for x in names]
def param(number,typename):
    return {'TypeCast':{'arg':{'ParamRef':{'number':number}},'typeName':{'names':strings('pg_catalog',typename),'typemod':-1}}}
def column(name): return {'ColumnRef':{'fields':strings('t',name)}}
one={'A_Const':{'ival':{'ival':1}}}; null={'A_Const':{'isnull':True}}
first_values=[{'FuncCall':{'funcname':strings('pg_catalog','pg_current_xact_id_if_assigned'),'funcformat':'COERCE_EXPLICIT_CALL'}}]+[param(i,t) for i,t in enumerate(['text','int8','int4','int4','int4'],1)]+[one,null]+[param(i,'bytea') for i in range(6,10)]
def assignment(name,value): return {'ResTarget':{'name':name,'val':value}}
seal_assignments=[assignment('sealed_generation',column('dirty_generation'))]
advance_assignments=[assignment('dirty_generation',{'A_Expr':{'kind':'AEXPR_OP','name':strings('+'),'lexpr':column('dirty_generation'),'rexpr':one}}),assignment('sealed_generation',null),assignment('original_operation_bytes',param(11,'bytea'))]
def call(name,args=None):
    body={'funcname':strings('pg_catalog',name),'funcformat':'COERCE_EXPLICIT_CALL'}
    if args is not None: body['args']=args
    return {'FuncCall':body}
def op(name,left,right): return {'A_Expr':{'kind':'AEXPR_OP','name':strings(name),'lexpr':left,'rexpr':right}}
def nonnull(arg): return {'NullTest':{'arg':arg,'nulltesttype':'IS_NOT_NULL'}}
def conjunction(args): return {'BoolExpr':{'boolop':'AND_EXPR','args':args}}
zero={'A_Const':{'ival':{}}}
xid=call('pg_current_xact_id_if_assigned')
identity_expected=[op('=',column('transaction_id'),xid),op('=',column('owner_kind'),{'CollateClause':{'arg':param(1,'text'),'collname':strings('pg_catalog','C')}})]+[op('=',column(name),param(i,type_name)) for i,name,type_name in [(2,'owner_id','int8'),(3,'owner_discriminator_id','int4'),(4,'property_owner_type_id','int4'),(5,'property_id','int4')]]
require(strip(identity)==identity_expected,'independent actual-xid and complete owner/property identity')
def verify_lookup(statement):
    require(set(statement)=={'fromClause','limitOption','op','targetList','whereClause'},'closed lookup modifiers')
    require(statement['limitOption']=='LIMIT_OPTION_DEFAULT' and statement['op']=='SETOP_NONE','ordinary full lookup')
    require(len(statement['fromClause'])==1 and set(statement['fromClause'][0])=={'RangeVar'},'single native lookup relation')
    relation=strip(statement['fromClause'][0]['RangeVar'])
    require(relation=={'schemaname':'truss','relname':'row_home_touch','inh':True,'relpersistence':'p','alias':{'aliasname':'t'}},'independent native lookup relation')
    require(strip(statement['whereClause'])==conjunction(identity_expected),'complete independently expected lookup predicate')
    require(strip(statement['targetList'])==strip(projection),'complete ordered original lookup projection')
verify_lookup(s)
custody=[op('=',column(name),param(i,'bytea')) for i,name in [(7,'original_layout_bytes'),(8,'original_home_bytes'),(9,'original_owner_property_bytes'),(10,'original_operation_bytes')]]
generation=[op('=',column('dirty_generation'),param(6,'int8')),op('>',column('dirty_generation'),zero)]
first_predicates=[nonnull(xid)]
for i in range(6,10): first_predicates += [nonnull(param(i,'bytea')),op('>',call('octet_length',[param(i,'bytea')]),zero)]
seal_predicates=identity_expected+generation+custody
advance_predicates=identity_expected+generation+[op('<',column('dirty_generation'),{'A_Const':{'fval':{'fval':'9223372036854775807'}}})]+custody+[nonnull(param(11,'bytea')),op('>',call('octet_length',[param(11,'bytea')]),zero)]
def verify(c):
    require(len(c)==3,'effect membership')
    require([set(x) for x in c]==[{'InsertStmt'},{'UpdateStmt'},{'UpdateStmt'}],'effect kinds')
    insert=c[0]['InsertStmt']; source=insert['selectStmt']['SelectStmt']
    require(set(insert)=={'cols','override','relation','returningList','selectStmt'},'closed insert modifiers')
    require(insert['override']=='OVERRIDING_NOT_SET','no identity override')
    require(set(insert['selectStmt'])=={'SelectStmt'},'single insert source')
    require(set(source)=={'limitOption','op','targetList','whereClause'},'closed source modifiers')
    require(source['limitOption']=='LIMIT_OPTION_DEFAULT' and source['op']=='SETOP_NONE','ordinary unlimited insert source')
    for statement in c[1:]:
        require(set(statement['UpdateStmt'])=={'relation','returningList','targetList','whereClause'},'closed update modifiers')
    for stmt in c:
        body=next(iter(stmt.values()))
        require(strip(body['relation'])==strip(s['fromClause'][0]['RangeVar']),'original relation')
        require(strip(body['returningList'])==strip(projection),'full ordered snapshot projection')
    for stmt in c[1:]:
        args=stmt['UpdateStmt']['whereClause']['BoolExpr']['args']
        require(len(args)>6 and strip(args[:6])==strip(identity),'exact six-part actual-xid identity prefix')
    cols=[x['ResTarget']['name'] for x in c[0]['InsertStmt']['cols']]
    require(cols==[x.removesuffix('_hex') for x in expected],'complete independent insert columns')
    require('onConflictClause' not in c[0]['InsertStmt'],'no upsert')
    values=c[0]['InsertStmt']['selectStmt']['SelectStmt']['targetList']
    require(strip([v['ResTarget']['val'] for v in values])==first_values,'independent first-touch initialization and original carriers')
    require(strip(c[1]['UpdateStmt']['targetList'])==seal_assignments,'seal only current dirty generation')
    require(strip(c[2]['UpdateStmt']['targetList'])==advance_assignments,'advance once, invalidate seal, replace complete original operation custody')
    require(strip(c[0]['InsertStmt']['selectStmt']['SelectStmt']['whereClause'])==conjunction(first_predicates),'complete first-touch actual-xid/nonempty-custody checks')
    require(strip(c[1]['UpdateStmt']['whereClause'])==conjunction(seal_predicates),'complete seal generation/custody checks')
    require(strip(c[2]['UpdateStmt']['whereClause'])==conjunction(advance_predicates),'complete advance bounded-generation/original-next-custody checks')
candidate=writes+advance;verify(candidate)
controls=[]
for name,mutate in [('relation substitution',lambda c:c[1]['UpdateStmt']['relation'].update(relname='object')),
 ('missing returned field',lambda c:c[0]['InsertStmt']['returningList'].pop()),
 ('reordered snapshot',lambda c:c[2]['UpdateStmt']['returningList'].reverse()),
 ('lost identity component',lambda c:c[1]['UpdateStmt']['whereClause']['BoolExpr']['args'].pop(4)),
 ('first generation altered',lambda c:c[0]['InsertStmt']['selectStmt']['SelectStmt']['targetList'][6]['ResTarget'].update(val={'A_Const':{'ival':{'ival':2}}})),
 ('carrier source substituted',lambda c:c[0]['InsertStmt']['selectStmt']['SelectStmt']['targetList'][8]['ResTarget']['val']['TypeCast']['arg']['ParamRef'].update(number=7)),
 ('seal assignment removed',lambda c:c[1]['UpdateStmt']['targetList'].clear()),
 ('advance seal retained',lambda c:c[2]['UpdateStmt']['targetList'].pop(1)),
 ('lost upper generation bound',lambda c:c[2]['UpdateStmt']['whereClause']['BoolExpr']['args'].pop(8)),
 ('lost original custody comparison',lambda c:c[1]['UpdateStmt']['whereClause']['BoolExpr']['args'].pop()),
 ('lost nonempty next custody',lambda c:c[2]['UpdateStmt']['whereClause']['BoolExpr']['args'].pop()),
 ('lost first-touch xid prerequisite',lambda c:c[0]['InsertStmt']['selectStmt']['SelectStmt']['whereClause']['BoolExpr']['args'].pop(0)),
 ('unexpected update FROM',lambda c:c[1]['UpdateStmt'].update(fromClause=[])),
 ('unexpected write CTE',lambda c:c[2]['UpdateStmt'].update(withClause={})),
 ('unexpected insert source LIMIT',lambda c:c[0]['InsertStmt']['selectStmt']['SelectStmt'].update(limitCount=one)),
 ('unexpected conflict path',lambda c:c[0]['InsertStmt'].update(onConflictClause={})),
 ('identity override',lambda c:c[0]['InsertStmt'].update(override='OVERRIDING_SYSTEM_VALUE')),
 ('wrong insert column',lambda c:c[0]['InsertStmt']['cols'][4]['ResTarget'].update(name='property_id'))]:
    c=copy.deepcopy(candidate);mutate(c)
    try:verify(c)
    except ValueError:controls.append({'case':name,'refused':True})
    else:raise ValueError('accepted '+name)
for name,mutate in [('lookup LIMIT hides matches',lambda x:x.update(limitCount=one)),('lookup joins suppress rows',lambda x:x['fromClause'].append(copy.deepcopy(x['fromClause'][0]))),('lookup extra predicate',lambda x:x['whereClause']['BoolExpr']['args'].append(nonnull(column('sealed_generation'))))]:
    x=copy.deepcopy(s);mutate(x)
    try:verify_lookup(x)
    except ValueError:controls.append({'case':name,'refused':True})
    else:raise ValueError('accepted '+name)
r={'scope':'Original source/archive/export hash consistency, three effect projections and two update identity prefixes against current-writer observation plus independently named insert columns, initialization, complete write assignment masks and independently constructed complete effect predicates and closed statement modifiers plus complete independently expected lookup shape and predicate. Does not validate source interpretation, original authority, native parameter/completion, savepoints, concurrency or execution.','originalSources':[observation_proof,wp,ap],'effectStatements':3,'returnedFields':12,'identityComponents':6,'controls':controls,'nativeExecution':False}
(E/'touch-runtime-parity.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'effectStatements':3,'identityChecks':2,'returnedFields':12,'refusals':len(controls),'nativeExecution':False}))
