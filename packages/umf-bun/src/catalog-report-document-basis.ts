/** Actual archive/input bijection and original producer observations; no accepted report. */
import {createHash} from 'node:crypto';
import type {createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export async function collectCatalogReportDocumentBasis(connection:CatalogStageConnection,prepared:Prepared,revision:string){
 if(!/^[1-9][0-9]{0,9}$/.test(revision)||BigInt(revision)>2147483647n)throw Error('Original positive native revision required');
 const rows=await connection.unsafe('SELECT * FROM truss.runtime_collect_report_documents($1::int)',[revision]);
 if(rows.length!==prepared.original.input.documents.length)throw Error('Complete original report document bijection required');
 const documents=rows.map((row,index)=>{
  const declaration=prepared.original.input.documents[index];const original=prepared.original.documents[index];
  if(row.ord!==String(index)||row.doc_id!==declaration.documentId||row.doc_revision!==declaration.documentRevision||row.content_sha256!==declaration.artifact.sha256||row.content_sha256!==original.sha256)throw Error('Original report document identity/order/digest correspondence');
  return Object.freeze({doc_id:row.doc_id,doc_revision:row.doc_revision,content_sha256:row.content_sha256,ord:row.ord});
 });
 const observations=prepared.documents.map((document,index)=>{
  const bytes=Buffer.from(JSON.stringify({producer:prepared.umfProfile,observation:document.interpretation}),'utf8');
  return Object.freeze({documentId:document.documentId,contentSha256:documents[index].content_sha256,interpretationProfile:prepared.umfProfile,
   evidence:Object.freeze({identity:'truss.original-umf-observation/'+document.documentId,bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')})});
 });
 return Object.freeze({provisionalRevision:revision,documents:Object.freeze(documents),observations:Object.freeze(observations),scope:'original_report_document_basis_only' as const});
}
