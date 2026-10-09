/** Actual archive/input bijection and original producer observations; no accepted report. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export async function collectCatalogReportDocumentBasis(connection:CatalogStageConnection,prepared:Prepared,revision:string){
 requireOriginalCatalogPreparation(prepared);
 if(!/^[1-9][0-9]{0,9}$/.test(revision)||BigInt(revision)>2147483647n)throw Error('Original positive native revision required');
 const rows=await connection.unsafe("SELECT d.*,o.original_writer_xid::text AS writer_xid,o.operation_ordinal::text AS operation_ordinal,o.effect_generation::text AS effect_generation FROM truss.runtime_collect_report_documents($1::int) d CROSS JOIN truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase='admitted'",[revision]);
 if(rows.length!==prepared.original.input.documents.length)throw Error('Complete original report document bijection required');
 const first=rows[0];
 if(!first||!(/^[1-9][0-9]{0,19}$/).test(first.writer_xid)||BigInt(first.writer_xid)>18446744073709551615n
  ||![first.operation_ordinal,first.effect_generation].every(value=>typeof value==='string'&&/^(0|[1-9][0-9]{0,18})$/.test(value)&&BigInt(value)<=9223372036854775807n))throw Error('Original native report observation tuple required');
 const nativeObservation=Object.freeze({writerXid:first.writer_xid,operationOrdinal:first.operation_ordinal,effectGeneration:first.effect_generation});
 const documents=rows.map((row,index)=>{
  if(row.writer_xid!==first.writer_xid||row.operation_ordinal!==first.operation_ordinal||row.effect_generation!==first.effect_generation)throw Error('Mixed native report observation tuple');
  const declaration=prepared.original.input.documents[index];const original=prepared.original.documents[index];
  if(row.ord!==String(index)||row.doc_id!==declaration.documentId||row.doc_revision!==declaration.documentRevision||row.content_sha256!==declaration.artifact.sha256||row.content_sha256!==original.sha256)throw Error('Original report document identity/order/digest correspondence');
  return Object.freeze({doc_id:row.doc_id,doc_revision:row.doc_revision,content_sha256:row.content_sha256,ord:row.ord});
 });
 const observations=prepared.documents.map((document,index)=>{
  const bytes=Buffer.from(JSON.stringify({producer:prepared.umfProfile,observation:document.interpretation}),'utf8');
  return Object.freeze({documentId:document.documentId,contentSha256:documents[index].content_sha256,interpretationProfile:prepared.umfProfile,
   evidence:Object.freeze({identity:'truss.original-umf-observation/'+document.documentId,bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')})});
 });
 return Object.freeze({provisionalRevision:revision,nativeObservation,documents:Object.freeze(documents),observations:Object.freeze(observations),scope:'original_report_document_basis_only' as const});
}

/** Recheck the original cut before using its document evidence in report assembly. */
export async function recheckCatalogReportDocumentBasis(connection:CatalogStageConnection,basis:Awaited<ReturnType<typeof collectCatalogReportDocumentBasis>>){
 const original=basis.nativeObservation;
 await connection.unsafe('SELECT truss.runtime_require_catalog_observation($1::text,$2::text,$3::text)',[original.writerXid,original.operationOrdinal,original.effectGeneration]);
}
