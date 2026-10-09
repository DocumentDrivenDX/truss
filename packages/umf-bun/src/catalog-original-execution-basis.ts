/** Original native actor facts only, not a complete originalExecution report. */
import {createHash} from 'node:crypto';
import {decodeAcceptanceJson} from '../../postgresql/src/acceptance-json';
import {requireOriginalCatalogReportPreparation,type collectCatalogReportPreparation} from './catalog-report-preparation';
import {recheckCatalogReportDocumentBasis} from './catalog-report-document-basis';
import type {createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Basis=Awaited<ReturnType<typeof collectCatalogReportPreparation>>;
export async function collectCatalogOriginalExecutionBasis(connection:CatalogStageConnection,prepared:Prepared,basis:Basis){
 requireOriginalCatalogReportPreparation(basis,prepared);const cut=basis.documentBasis.nativeObservation;
 const rows=await connection.unsafe('SELECT * FROM truss.runtime_collect_catalog_original_context($1::text,$2::text,$3::text)',[cut.writerXid,cut.operationOrdinal,cut.effectGeneration]);
 const columns=['actor_role_oid','backend_pid','context_hex','database_name','database_role','login_role','login_role_oid'];
 if(rows.length!==1||JSON.stringify(Object.keys(rows[0]).sort())!==JSON.stringify(columns))throw Error('Exact original native context result required');
 const row=rows[0];
 if(columns.some(key=>typeof row[key]!=='string')||!/^([0-9a-f]{2})+$/.test(row.context_hex)||row.context_hex.length>2097152)throw Error('Original bounded context bytes required');
 const bytes=Buffer.from(row.context_hex,'hex'),decoded=decodeAcceptanceJson(bytes);
 if(decoded===null||Array.isArray(decoded)||typeof decoded!=='object')throw Error('Original native context object required');
 const expected={interfaceVersion:'truss-native-operation-context/0.2',xid:cut.writerXid,ordinal:cut.operationOrdinal,
  actingUser:row.database_role,sessionUser:row.login_role,database:row.database_name,backendPid:row.backend_pid,actorRoleOid:row.actor_role_oid,sessionRoleOid:row.login_role_oid};
 if(JSON.stringify(Object.keys(decoded).sort())!==JSON.stringify(Object.keys(expected).sort())||Object.entries(expected).some(([key,value])=>decoded[key]!==value))throw Error('Original native context field correspondence required');
 if(!row.database_role||!row.login_role||!row.database_name||!/^[1-9][0-9]*$/.test(row.backend_pid))throw Error('Original native actor facts required');
 if([row.actor_role_oid,row.login_role_oid].some(value=>!/^[1-9][0-9]{0,9}$/.test(value)||BigInt(value)>4294967295n))throw Error('Original native role identities required');
 await recheckCatalogReportDocumentBasis(connection,basis.documentBasis);
 return Object.freeze({databaseRole:row.database_role,loginRole:row.login_role,actorRoleOid:row.actor_role_oid,loginRoleOid:row.login_role_oid,databaseName:row.database_name,backendPid:row.backend_pid,nativeObservation:cut,
  contextEvidence:Object.freeze({identity:'truss.original-native-operation-context/'+cut.writerXid+'/'+cut.operationOrdinal,bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')}),
  scope:'original_native_actor_context_basis_only' as const});
}
