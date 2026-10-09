/** Governing wire correspondence only, not native actor/capture authority. */
import {createRequire} from 'node:module';
import {mapAssertedOrigin} from '../packages/postgresql/src/asserted-origin-map';
const Ajv=createRequire('/Users/erik/Projects/umf/package.json')('ajv/dist/2020').default;
const ajv=new Ajv({strict:true});
const paths=['acceptance-input-v0.1.schema.json','exact-value-v0.1.schema.json'];
const pins:Record<string,string>={};const hash=(bytes:Uint8Array)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
for(const name of paths){const path='docs/helix/02-design/contracts/'+name;const bytes=new Uint8Array(await Bun.file(path).arrayBuffer());pins[path]=hash(bytes);ajv.addSchema(JSON.parse(new TextDecoder().decode(bytes)));}
const reportPath='docs/helix/02-design/contracts/acceptance-report-v0.1.schema.json';
const historyPath='docs/helix/02-design/contracts/history-event-v0.1.schema.json';
for(const path of [reportPath,historyPath])pins[path]=hash(new Uint8Array(await Bun.file(path).arrayBuffer()));
const report=await Bun.file(reportPath).json(),history=await Bun.file(historyPath).json();
const validateReportOrigin=ajv.compile(report.properties.originalExecution.properties.origin);
const validateJournalOrigin=ajv.compile(history.oneOf[0].properties.origin);
for(const variant of history.oneOf)if(JSON.stringify(variant.properties.origin)!==JSON.stringify(history.oneOf[0].properties.origin))throw Error('History origin variant mismatch');
const cases=['null','false','"9007199254740993.000"','[null,true,"\\u0000",{}]','{"kind":"integer","text":"123","databaseRole":"claimed","__proto__":"retained","😀":"unicode"}'];
for(const source of cases){const result=mapAssertedOrigin(new TextEncoder().encode(source),'native role supplied separately');if(!validateReportOrigin(result.origin)||!validateJournalOrigin(result.journalOrigin))throw Error('Governing origin shape mismatch');}
for(const changed of [{asserted:{kind:'null'}},{asserted:{kind:'null'},databaseRole:'role',extra:true}])if(validateJournalOrigin(changed))throw Error('Closed origin accepted missing/extra field');
const producer='packages/postgresql/src/asserted-origin-map.ts';pins[producer]=hash(new Uint8Array(await Bun.file(producer).arrayBuffer()));
const profile={identity:'truss.asserted-origin-map',version:'0.1.0-candidate',scope:'Pure numeric-free asserted tree to exact tagged journal value; supplied role is not observed native authority',sources:pins,mapping:{null:'null',boolean:'boolean',string:'string without interpretation',array:'ordered sequence',object:'map ordered by unsigned UTF8 original keys'},preservation:['Complete original asserted tree','Exact original UTF8 bytes','User labels and kind-like fields remain asserted','No overwrite from separately supplied databaseRole'],limits:{sourceBytes:'1048576',mappedNodes:'32768',encodedOutputBytes:'4194304'},adoption:'Requires original actor and asserted-origin capture custody, immutable registration, shared resource/native parity qualification and complete originalExecution composition'};
const path='docs/helix/02-design/contracts/asserted-origin-map-v0.1.proposal.json';await Bun.write(path,JSON.stringify(profile,null,2)+'\n');
await Bun.write('docs/helix/04-build/evidence/design-audit/asserted-origin-map.json',JSON.stringify({profilePath:path,profileSha256:hash(new Uint8Array(await Bun.file(path).arrayBuffer())),vectors:cases.length,allHistoryOriginShapesIdentical:true,closedShapeRefusals:2,scope:'Actual candidate mapping output against governing report origin and every current history origin shape only; no installed mapping/actor authority or resource adoption'},null,2)+'\n');
console.log('Five mapping vectors match report/history origin schemas; two closed-shape refusals pass.');
