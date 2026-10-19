// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private receipt-consistent declaration duties; record-valued literal semantics are unavailable. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {collectCatalogCoreAssertionIdentities} from './catalog-core-assertion-identities';
import {requireOriginalCatalogTypeReceipts,type collectCatalogTypeReceipts} from './catalog-type-receipts';
import {requireOriginalCatalogTypeJournals,type collectCatalogTypeJournals} from './catalog-type-journals';
import {sameReceiptMeaning} from './catalog-receipt-json';
import type {collectCatalogAssertionObservations} from './catalog-assertion-observations';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Collection=ReturnType<typeof collectCatalogAssertionObservations>;
type Receipts=ReturnType<typeof collectCatalogTypeReceipts>;type Journals=ReturnType<typeof collectCatalogTypeJournals>;
const issued=new WeakMap<object,Prepared>();
export function collectCatalogRecordTypeRuleFamilies(prepared:Prepared,collection:Collection,receipts?:Receipts,journals?:Journals){
 requireOriginalCatalogPreparation(prepared);
 if(receipts!==undefined)requireOriginalCatalogTypeReceipts(prepared,receipts);
 if(journals!==undefined)requireOriginalCatalogTypeJournals(prepared,journals);
 const core=collectCatalogCoreAssertionIdentities(prepared,collection);
 const bytes=Buffer.from(JSON.stringify({interfaceVersion:'truss-record-type-rule-family-candidate/0.1.0',basis:'original 0.7 explicit receipt-consistent declaration',
  semanticOwner:{identity:'umf.core.record-type.authoring',version:'6.0.0'},family:'record_type_declaration',
  meaning:'retain the exact qualified Field to Record authored declaration occurrence and its original evidence',
  identity:'candidate profile, original document/revision/digest, qualified Field, exact source occurrence and family; receipt protocol is evidence, not a second duty',
  valueSemantics:'unavailable; record-valued literals require a separate owner contract',issuerAuthority:'unverified',enforcement:'none',scope:'partial declaration duties only; no registration or accepted authority'}));
 const manifest=Object.freeze({identity:'truss.record-type-rule-family-candidate/0.1.0',bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')});
 const profile=Object.freeze({identity:'truss-record-type-rule-family-candidate',version:'0.1.0',sha256:manifest.sha256});
 const carriers=[...(receipts?.entries??[]).map(carrier=>({protocol:'exact_current_receipt' as const,carrier,meaning:carrier.ownerMeaning as any})),
  ...(journals?.entries??[]).map(carrier=>({protocol:'transition_journal' as const,carrier,meaning:carrier.originalMeaning as any}))];
 const rules=[],occurrences=new Set<string>();
 const key=(documentId:string,pointer:string)=>JSON.stringify([documentId,pointer]);
 for(const {protocol,carrier,meaning} of carriers){
  const occurrence=Object.freeze({sourceKind:'umf_document' as const,documentId:carrier.documentId,documentRevision:carrier.documentRevision,definitionPin:carrier.source.sha256,
   owner:carrier.identity,sourcePointer:carrier.sourcePointer});
  const at=key(carrier.documentId,carrier.sourcePointer);if(occurrences.has(at))throw Error('Duplicate original record-type declaration occurrence');occurrences.add(at);
  const generic=core.referenceLinks.filter(link=>key(link.documentId,link.sourcePointer)===at);
  if((collection.referenceLinksProfile&&generic.length!==1)||generic.length>1||(generic.length===1&&!sameReceiptMeaning(generic[0]!.originalMeaning,meaning.link)))throw Error('Original generic link and verified declaration correspondence required');
  const parameters=Object.freeze({field:carrier.identity,record:meaning.link.target.identity as Readonly<{module:string;element:string}>,recordPath:meaning.recordPath as string,reference:meaning.link.reference as unknown});
  const identity=Object.freeze({profile,occurrence,family:'record_type_declaration' as const});
  rules.push(Object.freeze({identity,source:carrier.source,parameters,protocol,carrier,ownerProfile:carrier.ownerProfile,ownerEvidence:carrier.ownerEvidence,
   originalReferenceBytesBase64:carrier.originalReferenceBytesBase64,receiptConsistency:'verified' as const,issuerAuthority:'unverified' as const,enforcement:'none' as const,reason:'unqualified' as const,
   valueSemantics:'unavailable' as const,interpretationQualified:false as const}));
 }
 const linksWithoutReceipt=core.referenceLinks.filter(link=>(link.originalMeaning as any).reference.role==='record-type'&&!occurrences.has(key(link.documentId,link.sourcePointer)));
 const result=Object.freeze({profile,manifest,core,rules:Object.freeze(rules),linksWithoutReceipt:Object.freeze(linksWithoutReceipt),
  genericLinkOwnerAvailability:collection.referenceLinksProfile?'configured' as const:'unavailable' as const,
  complete:false as const,semanticFamilyCoverageComplete:false as const,interpretationQualified:false as const,
  issuerAuthority:'unverified' as const,enforcement:'none' as const,valueSemantics:'unavailable' as const,scope:'original_receipt_consistent_record_type_declaration_duties_only' as const});
 issued.set(result,prepared);return result;
}
export function requireOriginalCatalogRecordTypeRuleFamilies(prepared:Prepared,candidate:object):void{
 requireOriginalCatalogPreparation(prepared);if(issued.get(candidate)!==prepared)throw Error('Original record-type rule-family candidate custody required');
}
