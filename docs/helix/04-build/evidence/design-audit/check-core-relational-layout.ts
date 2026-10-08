/** Candidate inspection only; refusal is retained, not converted into success. */
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
const path='docs/helix/02-design/models/truss-layout-core-relational-0.1.proposal.umf.json';
const d=await Bun.file(path).json();
const result=validateDocument(d);
const errors=result.diagnostics.filter(x=>x.severity==='error');
const report={scope:'UMF core relational candidate validation only; no DDL lowering/native adoption',modelPath:path,modelSha256:new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex'),valid:result.valid,complete:result.complete,errors,diagnosticCodes:[...new Set(result.diagnostics.map(x=>x.code))]};
await Bun.write('docs/helix/04-build/evidence/design-audit/core-relational-layout-validation.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({valid:result.valid,complete:result.complete,errors:errors.length,errorCodes:[...new Set(errors.map(x=>x.code))]}));
