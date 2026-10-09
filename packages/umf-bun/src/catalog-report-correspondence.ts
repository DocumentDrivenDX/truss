/** Existing producer fields only; never full report/effect admission. */
import {createCanonicalAcceptanceReportHandoff} from './canonical-report-handoff';
import {decodeAcceptanceJson} from '../../postgresql/src/acceptance-json';
import {requireOriginalCatalogReportPreparation,type collectCatalogReportPreparation} from './catalog-report-preparation';
import {recheckCatalogReportDocumentBasis} from './catalog-report-document-basis';
import type {createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Basis=Awaited<ReturnType<typeof collectCatalogReportPreparation>>;
// Object order is irrelevant; array order, exact strings and complete key sets matter.
function same(a:unknown,b:unknown):boolean{
 if(a===b)return true;
 if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return false;
 if(Array.isArray(a)||Array.isArray(b))return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>same(v,b[i]));
 const left=a as Record<string,unknown>,right=b as Record<string,unknown>,keys=Object.keys(left).sort(),other=Object.keys(right).sort();
 return keys.length===other.length&&keys.every((k,i)=>k===other[i]&&same(left[k],right[k]));
}
export async function createCatalogReportCorrespondence(dependenciesPackage:string){
 const codec=await createCanonicalAcceptanceReportHandoff(dependenciesPackage);
 return Object.freeze({async verify(connection:CatalogStageConnection,prepared:Prepared,basis:Basis,wire:Uint8Array){
  requireOriginalCatalogReportPreparation(basis,prepared);
  const encoded=codec.prepare(wire),report=decodeAcceptanceJson(Buffer.from(encoded.originalUtf8Hex,'hex')) as Record<string,unknown>;
  const expected={rev:basis.provisionalRevision,acceptedInput:prepared.original.input,documents:basis.documentBasis.documents,counts:basis.counts,
   provisional:basis.provisional,diagnostics:basis.validationEvidence.diagnostics,documentInterpretations:basis.validationEvidence.documentInterpretations,
   losses:basis.ingressBasis.losses,transformRegistrations:basis.ingressBasis.transformRegistrations};
  for(const [field,value] of Object.entries(expected))if(!same(report[field],value))throw Error('Original report producer correspondence required: '+field);
  await recheckCatalogReportDocumentBasis(connection,basis.documentBasis);
  return Object.freeze({...encoded,verifiedFields:Object.freeze(Object.keys(expected)),nativeObservation:basis.documentBasis.nativeObservation,
   scope:'nine_original_report_producer_fields_only' as const});
 }});
}
