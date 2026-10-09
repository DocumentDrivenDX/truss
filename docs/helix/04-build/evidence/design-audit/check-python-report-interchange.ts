/** Shared wire decision check only; not native or accepted-state interchange. */
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createProposedComposedAcceptanceReportHandoff} from '../../../../../packages/umf-bun/src/canonical-report-handoff';
const cases=JSON.parse(await readFile(process.argv[2],'utf8'));
const codec=await createProposedComposedAcceptanceReportHandoff(process.argv[3]);
const results=[];
for(const candidate of cases){
 const source=Buffer.from(candidate.bytesBase64,'base64');
 try{
  const prepared=codec.prepare(source),retained=Buffer.from(prepared.originalUtf8Hex,'hex');
  results.push({name:candidate.name,accepted:true,retainedMatches:retained.equals(source),sha256:createHash('sha256').update(retained).digest('hex')});
 }catch{results.push({name:candidate.name,accepted:false});}
}
console.log(JSON.stringify({schemaPins:codec.schemaPins,results}));
