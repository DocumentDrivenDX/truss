/** Original context4/native epoch and cut custody only, not complete installed admission. */
import {createHash} from 'node:crypto';
import {decodeCapturedOriginContext} from '../../postgresql/src/captured-origin-context';
import {decodeAcceptanceJson} from '../../postgresql/src/acceptance-json';
import {requireOriginalCatalogReportPreparation,type collectCatalogReportPreparation} from './catalog-report-preparation';
import {recheckCatalogReportDocumentBasis} from './catalog-report-document-basis';
import type {createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Basis=Awaited<ReturnType<typeof collectCatalogReportPreparation>>;
const issued=new WeakMap<object,{connection:CatalogStageConnection;prepared:Prepared;basis:Basis}>();
export function requireOriginalCatalogEpochContextBasis(value:object,connection:CatalogStageConnection,prepared:Prepared,basis:Basis){const original=issued.get(value);if(!original||original.connection!==connection||original.prepared!==prepared||original.basis!==basis)throw Error('Original captured origin collector custody required');requireOriginalCatalogReportPreparation(basis,prepared);}
export async function collectCatalogEpochContextBasis(connection:CatalogStageConnection,prepared:Prepared,basis:Basis,expectedCaptureProfile:Uint8Array){
 requireOriginalCatalogReportPreparation(basis,prepared);
 if(!(expectedCaptureProfile.buffer instanceof ArrayBuffer)||expectedCaptureProfile.length<1||expectedCaptureProfile.length>65536)throw Error('Original bounded capture profile bytes required');
 const profile=Buffer.from(Uint8Array.prototype.slice.call(expectedCaptureProfile) as Uint8Array),cut=basis.documentBasis.nativeObservation;
 const rows=await connection.unsafe('SELECT * FROM truss.runtime_collect_catalog_epoch_context($1,$2,$3)',[cut.writerXid,cut.operationOrdinal,cut.effectGeneration]);
 const keys=['actor_role_oid','backend_pid','context_hex','database_name','database_role','login_role','login_role_oid'];
 if(rows.length!==1||JSON.stringify(Object.keys(rows[0]).sort())!==JSON.stringify(keys)||keys.some(k=>typeof rows[0][k]!=='string')||!/^(?:[0-9a-f]{2})+$/.test(rows[0].context_hex)||rows[0].context_hex.length>2097152)throw Error('Exact original captured-context native result required');
 const row=rows[0],bytes=Buffer.from(row.context_hex,'hex'),decoded=decodeCapturedOriginContext(bytes,'0.4'),context=decodeAcceptanceJson(bytes) as Record<string,string>;
 if(context.xid!==cut.writerXid||context.ordinal!==cut.operationOrdinal||context.actingUser!==row.database_role||context.sessionUser!==row.login_role||context.database!==row.database_name||context.backendPid!==row.backend_pid||context.actorRoleOid!==row.actor_role_oid||context.sessionRoleOid!==row.login_role_oid||decoded.captureProfileHex!==profile.toString('hex'))throw Error('Original captured actor/profile correspondence required');
 await recheckCatalogReportDocumentBasis(connection,basis.documentBasis);
 const artifact=(identity:string,value:Buffer)=>Object.freeze({identity,bytesBase64:value.toString('base64'),sha256:createHash('sha256').update(value).digest('hex')});
 if(!decoded.epoch)throw Error('Original native epoch capture required');
 const result=Object.freeze({installationId:decoded.epoch.installationId,sourceEpoch:decoded.epoch.sourceEpoch,targetIncarnation:decoded.epoch.targetIncarnation,sourceEpochProfileEvidence:artifact('truss.original-epoch-profile/'+cut.writerXid+'/'+cut.operationOrdinal,Buffer.from(decoded.epoch.profileHex,'hex')),sourceEpochEvidence:artifact('truss.original-epoch-evidence/'+cut.writerXid+'/'+cut.operationOrdinal,Buffer.from(decoded.epoch.evidenceHex,'hex')),origin:decoded.origin,journalOrigin:decoded.journalOrigin,contextEvidence:artifact('truss.original-native-operation-context4/'+cut.writerXid+'/'+cut.operationOrdinal,bytes),assertedEvidence:artifact('truss.original-asserted-origin/'+cut.writerXid+'/'+cut.operationOrdinal,Buffer.from(decoded.assertedUtf8Hex,'hex')),captureProfileEvidence:artifact('truss.original-origin-capture-profile/'+cut.writerXid+'/'+cut.operationOrdinal,profile),nativeObservation:cut,scope:'original_context4_epoch_origin_basis_only' as const});
 issued.set(result,{connection,prepared,basis});return result;
}
/** Original basis is not reusable current authority; native context/cut recheck. */
export async function recheckOriginalCatalogEpochContextBasis(value:Awaited<ReturnType<typeof collectCatalogEpochContextBasis>>,connection:CatalogStageConnection,prepared:Prepared,basis:Basis){
 requireOriginalCatalogEpochContextBasis(value,connection,prepared,basis);
 const current=await collectCatalogEpochContextBasis(connection,prepared,basis,Buffer.from(value.captureProfileEvidence.bytesBase64,'base64'));
 if(JSON.stringify(current)!==JSON.stringify(value))throw Error('Original captured origin bytes/context changed');
}
