/** Composed original field candidate; profile meaning/installed authority remain unqualified. */
import {createHash} from 'node:crypto';
import {mapAssertedOrigin} from '../../postgresql/src/asserted-origin-map';
import {requireOriginalCatalogEpochContextBasis,recheckOriginalCatalogEpochContextBasis,type collectCatalogEpochContextBasis} from './catalog-epoch-context-basis';
import type {ProfilePin,ExactArtifact} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
type Epoch=Awaited<ReturnType<typeof collectCatalogEpochContextBasis>>;
type Args=Parameters<typeof collectCatalogEpochContextBasis>;
const issued=new WeakMap<object,{connection:Args[0];prepared:Args[1];basis:Args[2];epoch:Epoch}>();
export function requireOriginalCatalogExecutionReportCandidate(value:object,connection:Args[0],prepared:Args[1],basis:Args[2]){
 const original=issued.get(value);
 if(!original||original.connection!==connection||original.prepared!==prepared||original.basis!==basis)throw Error('Original execution report candidate custody required');
 requireOriginalCatalogEpochContextBasis(original.epoch,connection,prepared,basis);
}
export async function recheckOriginalCatalogExecutionReportCandidate(value:object,connection:Args[0],prepared:Args[1],basis:Args[2]){
 requireOriginalCatalogExecutionReportCandidate(value,connection,prepared,basis);
 await recheckOriginalCatalogEpochContextBasis(issued.get(value)!.epoch,connection,prepared,basis);
}
export async function composeCatalogExecutionReportCandidate(connection:Args[0],prepared:Args[1],basis:Args[2],epoch:Epoch,
 profiles:{readonly capture:ProfilePin;readonly mapping:ProfilePin;readonly mappingArtifact:ExactArtifact}){
 requireOriginalCatalogEpochContextBasis(epoch,connection,prepared,basis);
 const capture={...profiles.capture},mapping={...profiles.mapping},artifact={...profiles.mappingArtifact};
 for(const pin of [capture,mapping])if(!pin.identity||!pin.version||!/^[0-9a-f]{64}$/.test(pin.sha256))throw Error('Original execution profile pin required');
 if(capture.sha256!==epoch.captureProfileEvidence.sha256)throw Error('Original capture bytes/profile correspondence required');
 if(!artifact.identity||artifact.bytesBase64.length>1398104||!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(artifact.bytesBase64))throw Error('Original bounded mapping artifact required');
 const bytes=Buffer.from(artifact.bytesBase64,'base64');
 if(bytes.toString('base64')!==artifact.bytesBase64||createHash('sha256').update(bytes).digest('hex')!==artifact.sha256||mapping.sha256!==artifact.sha256)throw Error('Original mapping bytes/profile correspondence required');
 await recheckOriginalCatalogEpochContextBasis(epoch,connection,prepared,basis);
 const mapped=mapAssertedOrigin(Buffer.from(epoch.assertedEvidence.bytesBase64,'base64'),epoch.origin.databaseRole);
 if(JSON.stringify(mapped.origin)!==JSON.stringify(epoch.origin)||JSON.stringify(mapped.journalOrigin)!==JSON.stringify(epoch.journalOrigin))throw Error('Original origin mapping correspondence required');
 await recheckOriginalCatalogEpochContextBasis(epoch,connection,prepared,basis);
 const result=Object.freeze({candidate:Object.freeze({installationId:epoch.installationId,sourceEpoch:epoch.sourceEpoch,origin:epoch.origin,journalOrigin:epoch.journalOrigin,
  originMappingProfile:Object.freeze(mapping),captureProfile:Object.freeze(capture),contextEvidence:epoch.contextEvidence}),
  mappingArtifact:Object.freeze(artifact),scope:'original_execution_report_candidate_only' as const});
 issued.set(result,{connection,prepared,basis,epoch});return result;
}
