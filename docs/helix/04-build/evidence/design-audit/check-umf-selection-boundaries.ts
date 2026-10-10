/** Dependency consistency/preservation evidence, not Truss admission qualification. */
import {selectCoreElements} from '/Users/erik/Projects/umf/src/model/selection';
import {verifyCoreElementSelection} from '/Users/erik/Projects/umf/src/model/selection-verification';
import type {Document} from '/Users/erik/Projects/umf/src/model/types';
const paths=['src/model/selection.ts','src/model/selection-verification.ts','src/model/json.ts'];
const hash=(value:string)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
const pins=async()=>await Promise.all(paths.map(async path=>({path,sha256:hash(await Bun.file('/Users/erik/Projects/umf/'+path).text())})));
const before=await pins();
const source:Document={umf:'0.1.0',id:'truss-independent-selector-fixture',vocabularies:{'future.meaning':{version:'1.0.0'}},extensions:{'future.meaning':{nativeLink:{module:'m',element:'opaque'}}},modules:[{id:'m',namespace:'m',elements:[
{id:'root',name:'Root',scalarType:'string',extensions:{},references:[{module:'m',element:'leaf',role:'child',future:'preserve annotation'},{module:'m',element:'leaf',role:'child'}]},
{id:'leaf',name:'Leaf',scalarType:'string',extensions:{},references:[{module:'m',element:'root',role:'parent'}]},
{id:'opaque',name:'Opaque',scalarType:'future-scalar',extensions:{'future.meaning':{content:'retain'}}}
]}]};
const original=JSON.stringify(source),cases:string[]=[];
function require(value:boolean,id:string){if(!value)throw Error(id);cases.push(id);}
const query={references:'transitive' as const,identities:[{module:'m',element:'root'}]};
const selected=selectCoreElements(source,query);
require(selected.sourceValidation.valid&&selected.sourceValidation.complete===false,'valid_incomplete_preserved');
require(JSON.stringify(selected.selection.map(e=>e.element.id))==='["root","leaf"]','core_cycle_closes_without_native_link');
require(JSON.stringify(selected.source)===original,'full_original_source_retained');
verifyCoreElementSelection(selected);cases.push('original_receipt_consistency_verified');
const boundary=selectCoreElements(source,{...query,references:'none'});
require(boundary.boundaryReferences.length===2&&boundary.boundaryReferences[0].reference.future==='preserve annotation','repeated_boundary_annotations_retained');
const replacement=structuredClone(source);replacement.id='different-original-artifact';
const replaced=selectCoreElements(replacement,query);verifyCoreElementSelection(replaced);
require(JSON.stringify(replaced.source)!==original,'consistent_replacement_is_not_original_source');
const tampered=structuredClone(selected);tampered.selection[0].element.name='Substituted';
let tamperCode='';try{verifyCoreElementSelection(tampered);}catch(e){tamperCode=(e as {code:string}).code;}
require(tamperCode==='CORE_SELECTION_REPORT','result_only_tamper_refused');
require(JSON.stringify(source)===original,'input_not_mutated');
if(JSON.stringify(await pins())!==JSON.stringify(before))throw Error('dependency source changed');
await Bun.write('docs/helix/04-build/evidence/design-audit/umf-selection-boundaries.json',JSON.stringify({scope:'Locally executed selected UMF consistency/source-preservation behavior only; original-artifact comparison is fixture expectation, not production Truss admission or native support',bunVersion:Bun.version,sourcePins:before,fixtureSha256:hash(original),cases,trussExecutionQualified:false,nativeExecution:false},null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,trussExecutionQualified:false}));
