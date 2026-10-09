/** Exact current configuration under original operation custody, not complete admission. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogEpochContextBasis,recheckOriginalCatalogEpochContextBasis,type collectCatalogEpochContextBasis} from './catalog-epoch-context-basis';
import {recheckCatalogReportDocumentBasis} from './catalog-report-document-basis';
import type {collectCatalogReportPreparation} from './catalog-report-preparation';
import type {createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Report=Awaited<ReturnType<typeof collectCatalogReportPreparation>>;
type Epoch=Awaited<ReturnType<typeof collectCatalogEpochContextBasis>>;
const issued=new WeakMap<object,{connection:CatalogStageConnection;prepared:Prepared;report:Report;epoch:Epoch}>();
export function requireOriginalCatalogConfigurationBasis(value:object,connection:CatalogStageConnection,prepared:Prepared,report:Report,epoch:Epoch){
 const original=issued.get(value);if(!original||original.connection!==connection||original.prepared!==prepared||original.report!==report||original.epoch!==epoch)throw Error('Original configuration collector custody required');
 requireOriginalCatalogEpochContextBasis(epoch,connection,prepared,report);
}
export async function collectCatalogConfigurationBasis(connection:CatalogStageConnection,prepared:Prepared,report:Report,epoch:Epoch){
 requireOriginalCatalogEpochContextBasis(epoch,connection,prepared,report);
 await recheckCatalogReportDocumentBasis(connection,report.documentBasis);
 const cut=epoch.nativeObservation;
 const rows=await connection.unsafe('SELECT * FROM truss.runtime_collect_catalog_original_configuration($1,$2,$3)',[cut.writerXid,cut.operationOrdinal,cut.effectGeneration]);
 const keys=['configuration_generation','configuration_hex','configuration_sha256','context_hex','installed_inventory_hex','installed_inventory_sha256','journal_mode','key_reuse','selected_binding_hex','selected_binding_sha256'];
 if(rows.length!==1||JSON.stringify(Object.keys(rows[0]).sort())!==JSON.stringify(keys)||keys.some(k=>typeof rows[0][k]!=='string'))throw Error('Exact original configuration result required');
 const row=rows[0];
 if(row.context_hex!==Buffer.from(epoch.contextEvidence.bytesBase64,'base64').toString('hex')||!/^(?:0|[1-9][0-9]{0,18})$/.test(row.configuration_generation)||BigInt(row.configuration_generation)>9223372036854775807n||!['forbid','allow'].includes(row.key_reuse)||!['engine','trigger'].includes(row.journal_mode))throw Error('Original configuration context/scalar correspondence required');
 let bytes=0;
 const artifact=(kind:string,hex:string,digest:string)=>{
  if(!/^(?:[a-f0-9]{2})+$/.test(hex)||hex.length>33554432||(bytes+=hex.length/2)>16777216||!/^[a-f0-9]{64}$/.test(digest))throw Error('Bounded original configuration artifact required');
  const original=Buffer.from(hex,'hex');if(createHash('sha256').update(original).digest('hex')!==digest)throw Error('Original configuration artifact digest mismatch');
  return Object.freeze({identity:'truss.original-'+kind+'/'+cut.writerXid+'/'+cut.operationOrdinal+'/'+row.configuration_generation,bytesBase64:original.toString('base64'),sha256:digest});
 };
 const configuration=artifact('configuration',row.configuration_hex,row.configuration_sha256),selectedBinding=artifact('selected-binding',row.selected_binding_hex,row.selected_binding_sha256),installedInventory=artifact('installed-inventory',row.installed_inventory_hex,row.installed_inventory_sha256);
 await recheckOriginalCatalogEpochContextBasis(epoch,connection,prepared,report);
 const result=Object.freeze({configurationGeneration:row.configuration_generation,keyReuse:row.key_reuse as 'forbid'|'allow',journalMode:row.journal_mode as 'engine'|'trigger',configuration,selectedBinding,installedInventory,nativeObservation:cut,scope:'original_configuration_byte_basis_only' as const});
 issued.set(result,{connection,prepared,report,epoch});return result;
}
export async function recheckOriginalCatalogConfigurationBasis(value:Awaited<ReturnType<typeof collectCatalogConfigurationBasis>>,connection:CatalogStageConnection,prepared:Prepared,report:Report,epoch:Epoch){
 requireOriginalCatalogConfigurationBasis(value,connection,prepared,report,epoch);
 const current=await collectCatalogConfigurationBasis(connection,prepared,report,epoch);
 if(JSON.stringify(current)!==JSON.stringify(value))throw Error('Original configuration bytes/generation changed');
}
