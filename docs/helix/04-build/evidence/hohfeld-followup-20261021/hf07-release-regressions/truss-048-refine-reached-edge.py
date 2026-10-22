from pathlib import Path
import json,hashlib,zipfile
from truss._migration_verify import canonical,matches_inventory
root=Path('/Users/erik/Projects/truss/packages/python/src/truss/_migrations');m=json.loads((root/'manifest.json').read_bytes());old=m['target'];oldprofile=json.loads((root/(old+'.json')).read_bytes());edge=next(e for e in m['edges'] if e['target']==old);recipe=json.loads((root/edge['artifact']).read_bytes())
new=json.loads(Path('/private/tmp/truss-runtime074-reached-ny/target.json').read_bytes());utc=json.loads(Path('/private/tmp/truss-runtime074-reached-utc/target.json').read_bytes());assert matches_inventory(utc['inventory'],new)
for category,rows in oldprofile['inventory'].items():
 if category!='routines':assert new['inventory'][category]==rows,category
ar={(r[0],r[1]):r[2] for r in oldprofile['inventory']['routines']};br={(r[0],r[1]):r[2] for r in new['inventory']['routines']};added=set(br)-set(ar);assert len(added)==1 and next(iter(added))[0]=='person_reached';assert all(br[k]==v for k,v in ar.items())
record=Path('/Users/erik/Projects/truss/docs/helix/04-build/evidence/hohfeld-followup-20261021/hf07-release-regressions');record.mkdir(exist_ok=True)
with zipfile.ZipFile(record/'unpublished-2f23-candidate.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ('manifest.json',old+'.json',edge['artifact']):z.write(root/name,name)
key=next(iter(added));recipe['steps'].insert(0,br[key]);signature=key[0]+'('+key[1]+')';recipe['ownership'] += ['ALTER FUNCTION truss.'+signature+' OWNER TO {}','REVOKE ALL ON FUNCTION truss.'+signature+' FROM PUBLIC','GRANT EXECUTE ON FUNCTION truss.'+signature+' TO PUBLIC'];target=new['sha256'];recipe['target']=target;newedge='edge-'+edge['source']+'-'+target+'.json'
(root/(target+'.json')).write_bytes(canonical(new));(root/newedge).write_bytes(canonical(recipe));(root/(old+'.json')).unlink();(root/edge['artifact']).unlink();m['immutableFiles']=[n for n in m['immutableFiles'] if n not in (old+'.json',edge['artifact'])]+[target+'.json',newedge];edge.update(target=target,artifact=newedge);m['target']=target;m['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.json') if p.name!='manifest.json'};(root/'manifest.json').write_bytes(canonical(m))
(record/'refinement.json').write_bytes(canonical({'scope':'Unpublished candidate refinement only; all published sources and old receipts remain eligible and immutable','priorTarget':old,'target':target,'addedNativeRoutine':signature,'reason':'Person receipt visibility must classify no membership independently from an actually damaged original EXECUTE grant','bothInitializersAndLogicalRestore':True}));print(target,hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest())
