"""Cross-receipt artifact integrity only; no native query/definition qualification."""
import hashlib,json
from pathlib import Path
base=Path('docs/helix/04-build/evidence/design-audit')
expected={'bootstrap-collector-source':7,'bootstrap-routine-source':1,'bootstrap-type-source':3,'bootstrap-guard-source':4,'bootstrap-external-source':2,'bootstrap-routine-ancillary-source':2,'bootstrap-hierarchy-source':2,'bootstrap-metadata-source':3,'bootstrap-shared-source':2,'bootstrap-routine-acl-source':1,'bootstrap-namespace-source':1,'bootstrap-namespace-acl-source':1,'bootstrap-namespace-rights-source':1,'bootstrap-relation-grants-source':2,'bootstrap-role-path-source':1,'bootstrap-callable-sequence-rights-source':2,'bootstrap-table-rights-source':2,'bootstrap-operator-source':4,'bootstrap-opfamily-members-source':2,'bootstrap-cast-source':1,'bootstrap-external-type-adjunct-source':3,'bootstrap-external-relation-source':4,'bootstrap-external-relation-guards-source':3,'bootstrap-external-constraint-hierarchy-source':3,'bootstrap-type-language-acl-source':2,'bootstrap-type-language-rights-source':2,'bootstrap-target-context-source':2,'bootstrap-enum-child-source':1,'bootstrap-opfamily-child-source':2,'bootstrap-transform-source':2,'bootstrap-default-source':1,'bootstrap-guard-child-source':3,'bootstrap-tablespace-source':1}
seen=set();checked=[];failures=[]
for name,count in expected.items():
 path=base/(name+'.json');raw=path.read_bytes();receipt=json.loads(raw)
 if len(receipt['observations'])!=count:failures.append(name+': query count changed')
 if receipt['ownerSource']['commit']!='16c35e8d943769ccfa7bb57d16785aa7159abe65':failures.append(name+': owner source changed')
 for item in receipt['observations']:
  if item['path'] in seen:failures.append(item['path']+': duplicate original source')
  seen.add(item['path'])
  for key,digest in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
   actual=hashlib.sha256(Path(item[key]).read_bytes()).hexdigest()
   if actual!=item[digest]:failures.append(item[key]+': stale artifact')
  if item['complete'] is not False:failures.append(item['path']+': unexpected completeness claim')
 checked.append({'receiptPath':str(path),'receiptSha256':hashlib.sha256(raw).hexdigest(),'queryCount':len(receipt['observations'])})
output={'scope':'Thirty-three source receipts/current SQL/model/export artifact digests only; no parser execution, native scope, definition resolution or installed parity','queries':len(seen),'checked':checked,'failures':failures}
(base/'bootstrap-source-inventory.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'receipts':len(checked),'queries':len(seen),'failures':failures}))
if failures:raise SystemExit(1)
