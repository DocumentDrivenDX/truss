/** Per-document declared subset correspondence only; no support interpretation authority. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import type {ExactArtifact,ProfilePin} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export type CatalogUmfSubsetSelection=Readonly<{documentId:string;contentSha256:string;sourceVersion:string;interpretationProfile:ProfilePin;supportedSubset:ExactArtifact;transitionSha256:string|null}>;
const originals=new WeakMap<object,Prepared>();
const digest=(bytes:Uint8Array)=>createHash('sha256').update(bytes).digest('hex');
function data(value:unknown,keys:readonly string[]):Record<string,unknown>{
 if(value===null||typeof value!=='object'||Array.isArray(value))throw Error('Exact original subset selection data required');
 const descriptors=Object.getOwnPropertyDescriptors(value),names=Reflect.ownKeys(value);
 if(names.length!==keys.length||keys.some(key=>!descriptors[key]||!('value' in descriptors[key]))||names.some(key=>typeof key!=='string'||!keys.includes(key)))throw Error('Exact original subset selection data required');
 return Object.fromEntries(keys.map(key=>[key,descriptors[key].value]));
}
function profile(value:unknown):ProfilePin{
 const row=data(value,['identity','version','sha256']);
 if(typeof row.identity!=='string'||!row.identity||typeof row.version!=='string'||!row.version||typeof row.sha256!=='string'||!/^[0-9a-f]{64}$/.test(row.sha256))throw Error('Exact original interpretation profile required');
 return Object.freeze(row) as unknown as ProfilePin;
}
function artifact(value:unknown):ExactArtifact{
 const row=data(value,['identity','bytesBase64','sha256']);
 if(typeof row.identity!=='string'||!row.identity||typeof row.bytesBase64!=='string'||row.bytesBase64.length>1398104||typeof row.sha256!=='string'||!/^[0-9a-f]{64}$/.test(row.sha256)||!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(row.bytesBase64))throw Error('Exact bounded original subset artifact required');
 const bytes=Buffer.from(row.bytesBase64,'base64');
 if(bytes.length>1048576||bytes.toString('base64')!==row.bytesBase64||digest(bytes)!==row.sha256)throw Error('Original subset artifact byte correspondence required');
 return Object.freeze(row) as unknown as ExactArtifact;
}
/** Order is first original document occurrence; grouping compares the entire triple, not version alone. */
export function composeCatalogUmfMembershipCandidate(prepared:Prepared,selections:readonly CatalogUmfSubsetSelection[]){
 requireOriginalCatalogPreparation(prepared);
 if(!Array.isArray(selections)||selections.length!==prepared.documents.length||selections.length>4096)throw Error('Complete original document subset membership required');
 const descriptors=Object.getOwnPropertyDescriptors(selections);
 if(Reflect.ownKeys(selections).length!==selections.length+1)throw Error('Dense original subset selection array required');
 const entries:{version:string;interpretationProfile:ProfilePin;supportedSubset:ExactArtifact}[]=[],membership:{documentId:string;contentSha256:string;entryIndex:number;transitionSha256:string|null}[]=[];
 const groups=new Map<string,number>();let retainedBytes=0;
 for(let i=0;i<prepared.documents.length;i++){
  if(!descriptors[String(i)]||!('value' in descriptors[String(i)]))throw Error('Dense original subset selection array required');
  const row=data(descriptors[String(i)].value,['documentId','contentSha256','sourceVersion','interpretationProfile','supportedSubset','transitionSha256']);
  const document=prepared.documents[i],original=prepared.original.input.documents[i],pin=profile(row.interpretationProfile),subset=artifact(row.supportedSubset);
  const transitionSha256=document.interpretation.transition===null?null:digest(Buffer.from(JSON.stringify(document.interpretation.transition)));
  if(row.documentId!==document.documentId||row.contentSha256!==original.artifact.sha256||row.sourceVersion!==document.umfVersion||JSON.stringify(pin)!==JSON.stringify(prepared.umfProfile)||row.transitionSha256!==transitionSha256)throw Error('Original document interpretation/subset membership correspondence required');
  retainedBytes+=Buffer.from(subset.bytesBase64,'base64').length;if(retainedBytes>4194304)throw Error('Original subset membership artifact capacity exceeded');
  const entry=Object.freeze({version:document.umfVersion,interpretationProfile:pin,supportedSubset:subset}),key=JSON.stringify(entry);
  let entryIndex=groups.get(key);if(entryIndex===undefined){entryIndex=entries.length;groups.set(key,entryIndex);entries.push(entry);}
  membership.push(Object.freeze({documentId:document.documentId,contentSha256:original.artifact.sha256,entryIndex,transitionSha256}));
 }
 const result=Object.freeze({umf:Object.freeze(entries),membership:Object.freeze(membership),supportSemanticsQualified:false as const,scope:'original_document_declared_subset_correspondence_only' as const});
 originals.set(result,prepared);return result;
}
export function requireOriginalCatalogUmfMembershipCandidate(value:object,prepared:Prepared):void{
 requireOriginalCatalogPreparation(prepared);
 if(originals.get(value)!==prepared)throw Error('Original document subset membership candidate custody required');
}
