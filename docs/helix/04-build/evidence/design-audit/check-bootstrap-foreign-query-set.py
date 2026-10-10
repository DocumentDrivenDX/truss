"""Six fixed masked draft source/alias/nullability checks, never native qualification."""
from pathlib import Path
import copy, hashlib, json
ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
MANIFEST = ROOT / 'docs/helix/02-design/contracts/bindings/bootstrap-foreign-query-set-v0.1.proposal.json'
EXPECTED = {
 'foreign-table-header': ['adjunct_catalog_class_oid','relation_oid','server_oid'],
 'foreign-server-header': ['catalog_class_oid','server_oid','server_name','owner_oid','wrapper_oid','declared_server_type','declared_server_version','acl_native_text','acl_native_dimensions'],
 'foreign-wrapper-header': ['catalog_class_oid','wrapper_oid','wrapper_name','owner_oid','handler_oid','validator_oid','acl_native_text','acl_native_dimensions'],
 **{f'foreign-{kind}-options':['catalog_class_oid','original_object_oid','options_native_text','options_native_dimensions'] for kind in ['table','server','wrapper']}}
NULLABLE = {'declared_server_type','declared_server_version','acl_native_text','acl_native_dimensions','options_native_text','options_native_dimensions'}
# Optional wrapper callbacks admit original zero; transport remains nonnull.
def require(ok, message):
 if not ok: raise ValueError(message)
def verify(manifest):
 require(manifest['interfaceVersion']=='truss-bootstrap-foreign-query-set/0.1.0','version')
 require(manifest['parameterGrammar']=={'type':'pg_catalog.oid[]','dimensions':1,'lowerBound':1,'countInclusive':[1,256],'nonzero':True,'unique':True,'nullItems':False},'parameters')
 entries=manifest['entries']; require(len(entries)==6 and {e['query'] for e in entries}==set(EXPECTED),'fixed query inventory')
 for e in entries:
  n=e['query'];require([c['name'] for c in e['columns']]==EXPECTED[n],'fixed columns')
  for c in e['columns']:
   require(c['nullable']==(c['name'] in NULLABLE),'nullable');require(c['transport']=='original native text' and c['meaning'].strip(),'carrier')
  require(e['disclosure']==('separate explicit options authorization before materialization' if n.endswith('options') else 'header fields only; options unobserved and no whole-row JSON'),'disclosure')
  for key in ['source','archive','export']:
   path=ROOT/e[key];require(path.is_relative_to(ROOT) and '..' not in Path(e[key]).parts,'path');require(hashlib.sha256(path.read_bytes()).hexdigest()==e[key+'Sha256'],'source pin')
  model=json.loads((ROOT/e['archive']).read_text());ext=model['modules'][0]['elements'][0]['extensions']['umf.postgresql'];require(ext['source']==(ROOT/e['source']).read_text(),'original archive source')
  stmts=ext['root']['members']['stmts']['items'];require(len(stmts)==1,'one statement');targets=stmts[0]['members']['stmt']['members']['SelectStmt']['members']['targetList']['items'];aliases=[t['members']['ResTarget']['members']['name']['value'] for t in targets];require(aliases==EXPECTED[n],'original AST aliases')
 return True
if __name__=='__main__':
 original=json.loads(MANIFEST.read_text());verify(original)
 def remove(d): d['entries'].pop()
 def duplicate(d): d['entries'][-1]=copy.deepcopy(d['entries'][0])
 def reorder(d): d['entries'][0]['columns'].reverse()
 def nullability(d): d['entries'][0]['columns'][0]['nullable']=True
 def pin(d): d['entries'][0]['sourceSha256']='0'*64
 def disclosure(d): d['entries'][1]['disclosure']='automatic'
 def params(d): d['parameterGrammar']['nullItems']=True
 def blank(d): d['entries'][0]['columns'][0]['meaning']=''
 controls=[]
 for mutate in [remove,duplicate,reorder,nullability,pin,disclosure,params,blank]:
  changed=copy.deepcopy(original);mutate(changed)
  try: verify(changed)
  except (ValueError,KeyError,TypeError): controls.append({'control':mutate.__name__,'refused':True})
  else: raise RuntimeError('corruption accepted: '+mutate.__name__)
 result={'scope':'fixed six source/AST aliases, field/nullability/disclosure declarations and eight manifest corruption refusals only; no native grammar, resource, privilege, semantics or support qualification','queries':6,'controls':controls,'status':'pass','manifestSha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),'checkerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (HERE/'bootstrap-foreign-query-set-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'queries':6,'controls':len(controls),'status':'pass'}))
