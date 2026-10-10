/** Draft wire-shape probes only; no complete catalog or native qualification. */
import {readFileSync} from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass an installed Ajv Draft 2020-12 module path');
const {default: Ajv} = await import(modulePath);
const schema = JSON.parse(readFileSync(new URL('../../../02-design/contracts/catalog-view-v0.1.schema.json', import.meta.url), 'utf8'));
const validate = new Ajv({strict:true}).compile(schema);
const hash = 'a'.repeat(64);
const pin = {identity:'fixture',version:'0.1.0',sha256:hash};
const common = {definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'},authoredIdentity:'element'};
const key = {...common,kind:'key',typeId:'2',keyNumber:'1'};
const entry = {reference:key,lifecycle:'active',resolution:'defined',definition:{identity:'definition',bytesBase64:'e30=',sha256:hash},dependencies:[],provenance:{kind:'accepted_document',acceptedCatalogRevision:"1",documentOrdinal:"0",documentRevision:"fixture",acceptedDocumentSha256:hash,authoredPointer:"/types/0/keys/0",extractionProfile:pin}};
const {kind:ignoredKind,...recordProvenance}=entry.provenance;
const bindingProvenance={kind:'accepted_binding',acceptedCatalogRevision:'1',acceptedBindingSha256:hash,bindingVocabulary:pin,authoredPointer:'/storageKeys/0',extractionProfile:pin,owningRecordDefinitionPin:'record',owningRecordProvenance:{...recordProvenance,authoredPointer:'/types/0'}};
const base = {interfaceVersion:'truss-catalog-view/0.1.0',catalogRevision:'1',layoutProfile:pin,viewProfile:pin,consistencyEvidenceSha256:hash,scope:{kind:'complete'},definitions:[entry],inventorySha256:hash};
const cases: readonly [string,unknown,boolean][] = [
 ['accepted binding provenance',{...base,definitions:[{...entry,provenance:bindingProvenance}]},true],
 ['binding missing owning Record source',{...base,definitions:[{...entry,provenance:{...bindingProvenance,owningRecordProvenance:undefined}}]},false],
 ['binding missing vocabulary',{...base,definitions:[{...entry,provenance:{...bindingProvenance,bindingVocabulary:undefined}}]},false],
 ['binding not in acceptance inventory needs semantic refusal',{...base,definitions:[{...entry,provenance:{...bindingProvenance,acceptedBindingSha256:'b'.repeat(64)}}]},true],
 ['missing archive provenance',{...base,definitions:[{reference:key,lifecycle:'active',resolution:'defined',definition:entry.definition,dependencies:[]}]},false],
 ['wrong accepted document digest requires semantic rejection',{...base,definitions:[{...entry,provenance:{...entry.provenance,acceptedDocumentSha256:'b'.repeat(64)}}]},true],
 ['complete candidate',base,true],
 ['closed authorized projection',{...base,scope:{kind:'authorized_projection',authorizedScopeIdentity:'scope',closure:'complete_within_projection'}},true],
 ['projection missing closure',{...base,scope:{kind:'authorized_projection',authorizedScopeIdentity:'scope'}},false],
 ['fabricated global key ID',{...base,definitions:[{...entry,reference:{...key,storageId:'1'}}]},false],
 ['key missing owning type',{...base,definitions:[{...entry,reference:{...common,kind:'key',keyNumber:'1'}}]},false],
 ['host numeric key',{...base,definitions:[{...entry,reference:{...key,keyNumber:1}}]},false],
 ['noncanonical numeric alias',{...base,catalogRevision:'01'},false],
 ['unknown root field',{...base,ready:true},false],
 ['duplicate inventory needs semantic rejection',{...base,definitions:[entry,entry]},true],
 ['false archive digest needs semantic rejection',base,true],
 ['unproved empty complete inventory',{...base,definitions:[]},true],
 ['same local key number on distinct types',{...base,definitions:[entry,{...entry,reference:{...key,typeId:'10',authoredIdentity:'other'}}]},true],
];
const outcomes=cases.map(([name,input,expected])=>{const actual=Boolean(validate(input));if(actual!==expected)throw Error(name+': wrong shape verdict');return {name,expected,actual};});
console.log(JSON.stringify({scope:'Catalog-view shape only; no digest, owner, closure, inventory or native qualification',cases:outcomes.length,outcomes},null,2));
