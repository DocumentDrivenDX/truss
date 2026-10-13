from pathlib import Path
import hashlib,json,z3
root=Path(__file__).resolve().parents[5]
request=json.loads((root/'packages/python/tests/fixtures/security-mapping-request.json').read_text())
resolution=json.loads((root/'docs/helix/04-build/evidence/security-identity-requirements/resolution.json').read_text())
# Canonical JSON is only a ground fixture comparison here, not a UMF normalizer.
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'))
selected=canon(json.loads(request['modules'][0]['documentJson']))
evaluated=canon(resolution['documents'][0]['document'])
x,y=z3.Strings('selected_document evaluated_document')
same_subject=z3.Bool('same_subject_local_identity')
checks=[]
for name,constraints,expected in [
 ('current_exact_document_join',[x==selected,y==evaluated,x==y],'unsat'),
 ('current_separate_profiles_nonvacuous',[x==selected,y==evaluated],'sat'),
 ('local_subject_identity_does_not_establish_source_join',[x==selected,y==evaluated,same_subject,x!=y],'sat')]:
 s=z3.Solver();s.add(*constraints);actual=str(s.check());assert actual==expected
 checks.append({'name':name,'expected':expected,'actual':actual,'smt2':s.to_smt2(),'model':str(s.model()) if actual=='sat' else None})
result={'solver':z3.get_version_string(),'scope':'Ground current fixture canonical-document comparison under explicit exact-document-join requirement; not original UMF semantic equivalence, cryptographic proof, Python/SQL source refinement or native authority theorem','checks':checks,'selectedCanonicalSha256':hashlib.sha256(selected.encode()).hexdigest(),'evaluatedCanonicalSha256':hashlib.sha256(evaluated.encode()).hexdigest()}
(root/'docs/helix/04-build/evidence/live-subject-source-correspondence-20261013/proof.json').write_text(json.dumps(result,indent=2)+'\n')
print('1 UNSAT; 2 SAT; fixture comparison only')
