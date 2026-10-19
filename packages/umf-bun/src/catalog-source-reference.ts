// SPDX-License-Identifier: MIT OR Apache-2.0
/** Versioned Truss wrapper references; original UMF producer results remain upstream. */
import type {createCatalogInputPreparation} from './catalog-input';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export const SOURCE_REFERENCE_FORMAT='truss-catalog-source-reference/0.1';
const SUPPORT={identity:'truss-fresh-catalog-support',version:'0.20.0',sha256:'364335de9a0e6968106af189dcb11d5b4c86b2114361fcffd722c4154bf809cb'};
export function compactCatalogSources(prepared:Prepared):boolean{
 const pin=prepared.original.input.supportProfile;
 return pin.identity===SUPPORT.identity&&pin.version===SUPPORT.version&&pin.sha256===SUPPORT.sha256;
}
export function catalogSourceReference(prepared:Prepared,index:number,basis:'original'|'reversible_target'){
 const document=prepared.documents[index];if(!document)throw Error('Same-request source document required');
 return Object.freeze({interfaceVersion:SOURCE_REFERENCE_FORMAT,documentId:document.documentId,contentSha256:prepared.original.documents[index]!.sha256,documentRevision:prepared.original.input.documents[index]!.documentRevision,basis});
}
export function compactCatalogObservation(prepared:Prepared,index:number,basis:'original'|'reversible_target',observation:any):any{
 if(!compactCatalogSources(prepared))return observation;
 const document=prepared.documents[index]!;
 const expected=basis==='original'?document.interpretation.source:document.interpretation.target;
 if(!observation||JSON.stringify(observation.source)!==JSON.stringify(expected))throw Error('Captured original owner source correspondence required');
 // Only the documented observation.source position is interpreted as a reference.
 return {...observation,source:catalogSourceReference(prepared,index,basis)};
}
export function resolveCatalogObservation(prepared:Prepared,observed:{documentId:string;basis:'original'|'reversible_target';result:unknown}):any{
 const result=observed.result as any;
 if(!compactCatalogSources(prepared)||result.state!=='observed')return result.observation;
 const index=prepared.documents.findIndex(d=>d.documentId===observed.documentId);
 const reference=catalogSourceReference(prepared,index,observed.basis);
 if(JSON.stringify(result.observation.source)!==JSON.stringify(reference))throw Error('Exact same-request source reference required');
 const document=prepared.documents[index]!;
 return {...result.observation,source:observed.basis==='original'?document.interpretation.source:document.interpretation.target};
}
export function catalogSourceArtifact(prepared:Prepared,index:number){
 const artifact=prepared.original.input.documents[index]!.artifact;
 return compactCatalogSources(prepared)?Object.freeze({identity:artifact.identity,sha256:artifact.sha256,reference:catalogSourceReference(prepared,index,'original')}):artifact;
}

export function catalogObservationIdentity(prepared:Prepared,index:number,ordinal:number):string{
 return (compactCatalogSources(prepared)?'truss.owner-declaration-observation-references/0.1/':'truss.owner-declaration-observation/')+index+'/'+ordinal;
}
