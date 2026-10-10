/** Closed wire shape only; no UMF/native key semantic qualification. */
import {readFileSync} from 'node:fs';
const path=process.argv[2];if(!path)throw Error('Pass installed Ajv Draft 2020-12 path');
const {default:Ajv}=await import(path);
const schema=JSON.parse(readFileSync(new URL('../../../02-design/contracts/key-bindings-v0.1.schema.json',import.meta.url),'utf8'));
const validate=new Ajv({strict:true}).compile(schema);
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const record={documentId:'d',moduleId:'m',recordId:'r',definitionPin:'record'};
const property={authoredPropertyId:'p',definitionPin:'property'};
const portable={bindingId:'key',record,kind:'portable_identity',authoredKeyId:'source-key',tupleProfile:pin,transportProfile:pin,components:[property]};
const storage={bindingId:'storage-key',record,kind:'storage_uniqueness',missingComponent:'omit_and_report',encodingProfile:pin,components:[{property,equalityProfile:pin,nullPolicy:'reject'}]};
const base={interfaceVersion:'truss-key-bindings/0.1.0',vocabularyProfile:pin,bindings:[portable]};
const cases:readonly [string,unknown,boolean][]=[
 ['portable binding',base,true],
 ['sparse storage binding',{...base,bindings:[storage]},true],
 ['participating null explicit',{...base,bindings:[{...storage,components:[{...storage.components[0],nullPolicy:'participating_null'}]}]},true],
 ['nonparticipating null explicit',{...base,bindings:[{...storage,components:[{...storage.components[0],nullPolicy:'nonparticipating'}]}]},true],
 ['portable cannot override null policy',{...base,bindings:[{...portable,nullPolicy:'participating_null'}]},false],
 ['missing component policy',{...base,bindings:[{...storage,missingComponent:undefined}]},false],
 ['empty components',{...base,bindings:[{...portable,components:[]}]},false],
 ['numeric authored key ID',{...base,bindings:[{...portable,authoredKeyId:1}]},false],
 ['artifact executable field',{...base,bindings:[{...storage,execute:'code'}]},false],
 ['duplicate binding IDs need semantic refusal',{...base,bindings:[portable,portable]},true],
 ['duplicate components need semantic refusal',{...base,bindings:[{...portable,components:[property,property]}]},true],
 ['foreign source owner needs semantic refusal',{...base,bindings:[{...portable,record:{...record,recordId:'other'}}]},true],
 ['unavailable profile needs semantic refusal',{...base,bindings:[{...portable,tupleProfile:{...pin,identity:'unavailable'}}]},true]
];
const outcomes=cases.map(([name,input,expected])=>{const actual=Boolean(validate(input));if(actual!==expected)throw Error(name);return {name,expected,actual}});
console.log(JSON.stringify({scope:'Key binding shape only; no ownership, profile/source semantics, identity continuity, native enforcement or resource qualification',cases:outcomes.length,outcomes},null,2));
