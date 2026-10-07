"""Archived AST projection controls only; no native descriptor or execution evidence."""
import copy,hashlib,json
from pathlib import Path

def require(condition,message):
    if not condition: raise ValueError(message)
def unwrap(node):
    kind=node['kind']
    if kind=='object': return {k:unwrap(v) for k,v in node['members'].items()}
    if kind=='array': return [unwrap(v) for v in node['items']]
    if kind=='number': return int(node['value'])
    if kind in ('string','boolean'): return node['value']
    if kind=='null': return None
    raise ValueError('unsupported AST carrier kind '+kind)
def find(node,key):
    if isinstance(node,dict):
        for k,v in node.items():
            if k==key: yield v
            yield from find(v,key)
    elif isinstance(node,list):
        for v in node: yield from find(v,key)
def check_statement(stmt,names,relation,alias,ordinal,retained):
    require([x['ResTarget']['name'] for x in stmt['targetList']]==names,'projection order/inventory')
    homes=list(find(stmt['fromClause'],'RangeVar'))
    require(len(homes)==1 and homes[0]['schemaname']=='truss' and homes[0]['relname']==relation,'relation home')
    params=list(find(stmt['whereClause'],'ParamRef'))
    require([p['number'] for p in params]==[1,2],'original typed parameter inventory')
    types=list(find(stmt['whereClause'],'typeName'))
    require([[s['String']['sval'] for s in t['names']] for t in types]==[['pg_catalog','int8'],['pg_catalog','int4']],'parameter domains')
    require(stmt['limitCount']['A_Const']['ival']['ival']==2,'duplicate-header diagnostic limit')
    targets=[x['ResTarget'] for x in stmt['targetList'] if x['ResTarget']['name']=='retained_text']
    if targets:
        refs=list(find(targets[0],'ColumnRef'))
        require([[s['String']['sval'] for s in r['fields']] for r in refs]==[[alias,'retained']],'retained home')
    require(bool(targets)==(ordinal==0 or retained),'no fabricated baseline edge retained home')
    require(set(stmt)=={'targetList','fromClause','whereClause','limitCount','limitOption','op'},'unexpected query clauses')
    require(stmt['op']=='SETOP_NONE' and stmt['limitOption']=='LIMIT_OPTION_COUNT','unexpected query operation')
    require(homes[0]['alias']['aliasname']==alias,'relation alias')
    conjunction=stmt['whereClause']['BoolExpr']
    require(conjunction['boolop']=='AND_EXPR' and len(conjunction['args'])==2,'exact predicate conjunction')
    for argument,column,number in zip(conjunction['args'],['id','type_id' if ordinal==0 else 'rel_type_id'],[1,2]):
        comparison=argument['A_Expr']
        require(comparison['kind']=='AEXPR_OP' and comparison['name']==[{'String':{'sval':'='}}],'identity equality operator')
        require([x['String']['sval'] for x in comparison['lexpr']['ColumnRef']['fields']]==[alias,column],'identity predicate column')
        require(comparison['rexpr']['TypeCast']['arg']['ParamRef']['number']==number,'identity parameter association')

object_names=['record_id','record_type_id','root_id','root_type_id','record_version','catalog_revision','created_at_text','updated_at_text','properties_text','retained_text','date_style','time_zone']
edge_names=['record_id','record_type_id','source_id','source_type_id','target_id','target_type_id','order_key','record_version','catalog_revision','created_at_text','updated_at_text','properties_text','date_style','time_zone']
results=[]
negative_controls=[]
for family,retained in [('private-record-metadata-observation',False),('private-record-metadata-retained-observation',True)]:
    stem=Path('docs/helix/02-design/contracts')/(family+'-v0.1.proposal')
    artifact=Path(str(stem)+'.umf.json')
    model=json.loads(artifact.read_text())
    tree=unwrap(model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
    statements=list(find(tree,'SelectStmt'))
    require(len(statements)==2,'exact statement inventory')
    expected_edge=edge_names.copy()
    if retained: expected_edge.insert(expected_edge.index('date_style'),'retained_text')
    for ordinal,(stmt,names,relation,alias) in enumerate(zip(statements,[object_names,expected_edge],['object','edge'],['o','e'])):
        check_statement(stmt,names,relation,alias,ordinal,retained)
    for case in ['wrong_identity_column','reversed_parameter','wrong_operator','extra_predicate','missing_retained_projection']:
        bad=copy.deepcopy(statements[0])
        args=bad['whereClause']['BoolExpr']['args']
        if case=='wrong_identity_column': args[0]['A_Expr']['lexpr']['ColumnRef']['fields'][1]['String']['sval']='root_id'
        if case=='reversed_parameter': args[0]['A_Expr']['rexpr']['TypeCast']['arg']['ParamRef']['number']=2
        if case=='wrong_operator': args[0]['A_Expr']['name'][0]['String']['sval']='>'
        if case=='extra_predicate': args.append(copy.deepcopy(args[0]))
        if case=='missing_retained_projection': bad['targetList']=[x for x in bad['targetList'] if x['ResTarget']['name']!='retained_text']
        try: check_statement(bad,object_names,'object','o',0,retained)
        except (ValueError,KeyError): negative_controls.append({'family':family,'case':case,'refused':True})
        else: raise ValueError('corruption accepted: '+case)
    receipt=json.loads(Path('docs/helix/04-build/evidence/design-audit',family+'-source.json').read_text())['observations'][0]
    for path_key,hash_key in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
        require(hashlib.sha256(Path(receipt[path_key]).read_bytes()).hexdigest()==receipt[hash_key],'stale source receipt')
    results.append({'family':family,'objectColumns':12,'edgeColumns':15 if retained else 14,'passed':True})
print(json.dumps({'scope':'archived source AST projection/domain/limit/home and receipt-hash checks only','nativeExecuted':False,'results':results,'negativeControls':negative_controls},indent=2))
