from pathlib import Path
import subprocess,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
source=ROOT/'scripts/prove-graph-semantic-membership.py';original=ROOT/'docs/helix/04-build/evidence/graph-policy-read-20261013/formal'
receipt=json.loads((original/'receipt.json').read_bytes());replica=OUT/'proof-replay'
for rel in receipt['sources']:
 dest=replica/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/rel).read_bytes())
r=subprocess.run(['/private/tmp/umf-write-comparison-proof-env-20261013/bin/python',str(replica/'scripts/prove-graph-semantic-membership.py')],text=True,capture_output=True,timeout=40);assert r.returncode==0,r.stderr
output=replica/'docs/helix/04-build/evidence/graph-policy-read-20261013/formal'
files={p.name:p.read_bytes() for p in output.iterdir()}
for name,raw in files.items():assert raw==(original/name).read_bytes(),name
record={'status':'passed','queries':3,'unsat':1,'sat':2,'solver':'4.15.4','exactCompleteOutputMatch':True,'scriptSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Exact copied script/source replay. Propositional compared-pair injectivity assumptions over unbounded symbolic IDs/strings; not global quantified injectivity, native/codec/evaluator refinement or policy authority.'}
(OUT/'proof-replay.json').write_text(json.dumps(record,indent=2)+'\n');print(r.stdout.strip())
