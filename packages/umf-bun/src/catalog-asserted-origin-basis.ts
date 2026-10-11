/** Original native actor plus separately captured asserted bytes; not full context. */
import {copyOriginalByteCustody} from '../../postgresql/src/original-byte-custody';
import {createHash} from 'node:crypto';
import {mapAssertedOrigin} from '../../postgresql/src/asserted-origin-map';
import {recheckOriginalCatalogNativeContext,type collectCatalogOriginalExecutionBasis} from './catalog-original-execution-basis';
type Actor=Awaited<ReturnType<typeof collectCatalogOriginalExecutionBasis>>;
type Connection=Parameters<typeof collectCatalogOriginalExecutionBasis>[0];
type Prepared=Parameters<typeof collectCatalogOriginalExecutionBasis>[1];
type Basis=Parameters<typeof collectCatalogOriginalExecutionBasis>[2];
export async function collectCatalogAssertedOriginBasis(connection:Connection,prepared:Prepared,basis:Basis,actor:Actor,originalAsserted:Uint8Array){
 let owned:Uint8Array;try{owned=copyOriginalByteCustody(originalAsserted,true)}catch{throw Error('Original bounded asserted origin bytes required')}
 await recheckOriginalCatalogNativeContext(actor,connection,prepared,basis);
 const mapped=mapAssertedOrigin(owned,actor.databaseRole);
 await recheckOriginalCatalogNativeContext(actor,connection,prepared,basis);
 const bytes=Buffer.from(owned),cut=actor.nativeObservation;
 return Object.freeze({origin:mapped.origin,journalOrigin:mapped.journalOrigin,
  assertedEvidence:Object.freeze({identity:'truss.asserted-origin-candidate/'+cut.writerXid+'/'+cut.operationOrdinal,bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')}),
  nativeActorEvidence:actor.contextEvidence,
  scope:'native_actor_and_separately_captured_asserted_origin_basis_only' as const});
}
