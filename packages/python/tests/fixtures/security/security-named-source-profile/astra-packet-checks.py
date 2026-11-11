from pathlib import Path
import subprocess,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;MIRROR=OUT/'packet-mirror';REL=Path('docs/helix/04-build/evidence/security-named-source-profile')
paths=[Path('scripts/evaluate-security-captured-identity-fixture.ts'),Path('scripts/security-named-source-fixture.ts')]+[p.relative_to(ROOT) for p in (ROOT/REL).glob('*.json')]
for p in paths:
 q=MIRROR/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/p).read_bytes())
payload=Path('/private/tmp/resource-list-review-20261013/baseline.json').read_text();checks=[]
def run(name,ok):
 r=subprocess.run(['/opt/homebrew/bin/bun',str(MIRROR/'scripts/evaluate-security-captured-identity-fixture.ts'),'--named-source'],cwd=MIRROR,input=payload,capture_output=True,text=True,timeout=10)
 assert (r.returncode==0) if ok else (r.returncode!=0 and r.stdout==''),(name,r.stdout,r.stderr)
 checks.append({'name':name,'passed':True,'successful':ok})
run('byte-exact copied source/packets positive',True)
doc=MIRROR/REL/'document.json';original=doc.read_bytes();doc.write_bytes(original+b' ');run('document byte drift refuses no stdout',False);doc.write_bytes(original)
mapping=MIRROR/REL/'mapping-request.json';original=mapping.read_bytes()
for name,fn in [('module document',lambda p:p['modules'][0].update(documentJson=p['modules'][0]['documentJson']+' ')),('policy',lambda p:p.update(policyJson=p['policyJson']+' ')),('ontology',lambda p:p.update(ontologyJson=p['ontologyJson']+' ')),('extra module',lambda p:p['modules'].append(p['modules'][0])),('empty modules',lambda p:p.update(modules=[]))]:
 p=json.loads(original);fn(p);mapping.write_text(json.dumps(p));run(name+' drift refuses no stdout',False)
mapping.write_bytes(original);run('exact restoration positive',True)
# Revised authored fixture differs only in explicit names and revision/id pins.
legacy=json.loads((ROOT/'docs/helix/04-build/evidence/security-identity-requirements/resolution.json').read_bytes());named=json.loads((ROOT/REL/'resolution.json').read_bytes())
a=named['documents'][0]['document'];b=legacy['documents'][0]['document'];stripped=json.loads(json.dumps(a))
for m in stripped['modules']:
 for e in m['elements']:assert e.pop('name')==e['id']
assert stripped==b
checks.append({'name':'new named document preserves every legacy field/assertion plus explicit names','passed':True})
assert named['documents'][0]['revision']=='named-schema-1' and named['ontology']['revision']=='named-ontology-1'
checks.append({'name':'new authored revisions are distinct','passed':True})
def pin(p):b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
(OUT/'packet-results.json').write_text(json.dumps({'count':len(checks),'controls':checks,'sourcePins':[pin(ROOT/p) for p in paths]+[pin(Path(__file__))],'scope':'Actual unchanged fixture evaluator and named helper copied into an owned mirror; only owned packet copies mutated. No repository or native mutation.'},indent=2)+'\n')
print(json.dumps({'controls':len(checks),'pass':True}))
