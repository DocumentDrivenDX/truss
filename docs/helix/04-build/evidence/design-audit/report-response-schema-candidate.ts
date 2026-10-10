/** Private full-response schema candidate; no original account or acceptance authority. */
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {decodeReportResponseJson} from './report-response-json-candidate';
const pins={
  "exact-value-v0.1.schema.json": "0c804796bfbf68339c299f0c55d24db58fcfcc929bffe2d5ffaf4a2f27e24880",
  "history-record-v0.1.schema.json": "c35c1258028cc4c8c95dcd16b561caed4f2a347c086f72ebfc7bfc4f2dfcf2fe",
  "history-event-v0.1.schema.json": "e42f9b48642528cabbb646ccb758eb12b7f030029b712cf5d6f5174cbd90bfa6",
  "acceptance-input-v0.1.schema.json": "0278cbbbde843091c005b688fd9c081a2fdff843b9adda006ba80fb87828d7cd",
  "acceptance-rejection-v0.1.schema.json": "98262b8d99fe0f87f752140a418a4e4f8751c4d28986457302586fee622258cf",
  "enforcement-report-v0.1.schema.json": "7af9c786a297583d6eb5489d85f33fb0a04b2c1d0b6551e6d107528cc15c4137",
  "direct-cursor-v0.1.schema.json": "bff79ad2e5ccc1047b43bdbe6eeb51b597f098c881313fd980de01c1685b4942",
  "acceptance-report-v0.1.schema.json": "ccdc9976de3c158fae0a14d6cc41685d5f5a289d67daeb86b5e998b4a611e902",
  "history-retain-payload-v0.1.proposal.schema.json": "fc08e07a4b09636ac234737be9bb2cf3a9a3c26120baad612176574c17659605",
  "history-event-v0.2.proposal.schema.json": "714923be0f86bd3508a097cabfee63a180e03b19651ebbfa38844bb3e637b425",
  "acceptance-report-v0.3.proposal.schema.json": "c54196f8b4324aec768a33eeeab89bc2615a954af0e45559ed2038ccad7f14bf"
} as const;
export async function createReportResponseSchemaCandidate(dependenciesPackage:string){
 const require=createRequire(dependenciesPackage),Ajv=require('ajv/dist/2020').default;
 const ajv=new Ajv({strict:true});let root:unknown;
 for(const [name,expected] of Object.entries(pins)){
  const bytes=await readFile(new URL('../../../02-design/contracts/'+name,import.meta.url));
  if(createHash('sha256').update(bytes).digest('hex')!==expected)throw Error('Original response schema pin mismatch');
  const schema=JSON.parse(bytes.toString('utf8'));
  if(name==='acceptance-report-v0.3.proposal.schema.json')root=schema;else ajv.addSchema(schema);
 }
 const validate=ajv.compile(root);
 return Object.freeze({scope:'response_schema_bytes_only_without_account_admission' as const,
  prepare(original:Uint8Array){
   if(!(original.buffer instanceof ArrayBuffer)||original.length>4194304)throw Error('Response byte custody/capacity required');
   const owned=Uint8Array.prototype.slice.call(original) as Uint8Array;
   const report=decodeReportResponseJson(owned);
   if(!validate(report))throw Error('Original composed response schema refused');
   // The returned tree and bytes are data, never prepared operation authority.
   return {originalBytes:owned,report,scope:'response_schema_bytes_only_without_account_admission' as const};
  }});
}
