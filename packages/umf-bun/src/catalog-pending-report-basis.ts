/** Exact private pending source/value basis; no accepted report or readiness authority. */
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import type {CatalogStageConnection} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Basis=Readonly<{provisionalRevision:string;originalBasisHex:string;scope:'original_pending_association_report_basis_only'}>;
const originals=new WeakMap<object,{connection:CatalogStageConnection;prepared:Prepared;revision:string;hex:string}>();
export async function collectPendingCatalogReportBasis(connection:CatalogStageConnection,prepared:Prepared,revision:string):Promise<Basis>{
 requireOriginalCatalogPreparation(prepared);
 if(typeof revision!=='string'||!/^[1-9][0-9]{0,9}$/.test(revision)||BigInt(revision)>2147483647n)throw Error('Original positive native revision required');
 await connection.unsafe("SELECT truss.runtime_require_catalog_input(decode($1::text,'hex'))",[prepared.original.originalUtf8Hex]);
 const rows=await connection.unsafe("SELECT encode(truss.runtime_collect_pending_association_report_basis_candidate($1::int),'hex') AS original_basis_hex",[revision]);
 if(rows.length!==1||rows[0]===null||typeof rows[0]!=='object'||Array.isArray(rows[0])
  ||Object.keys(rows[0]).length!==1||typeof rows[0].original_basis_hex!=='string'
  ||rows[0].original_basis_hex.length>16777216||rows[0].original_basis_hex.length%2!==0||!(/^[0-9a-f]+$/).test(rows[0].original_basis_hex))throw Error('Exact bounded original native report basis bytes required');
 const hex=rows[0].original_basis_hex;
 const result=Object.freeze({provisionalRevision:revision,originalBasisHex:hex,scope:'original_pending_association_report_basis_only' as const});
 originals.set(result,{connection,prepared,revision,hex});
 await recheckPendingCatalogReportBasis(connection,prepared,result);
 return result;
}
export async function recheckPendingCatalogReportBasis(connection:CatalogStageConnection,prepared:Prepared,basis:Basis):Promise<void>{
 requireOriginalCatalogPreparation(prepared);
 const original=originals.get(basis);
 if(!original||original.connection!==connection||original.prepared!==prepared||basis.provisionalRevision!==original.revision
  ||basis.originalBasisHex!==original.hex||basis.scope!=='original_pending_association_report_basis_only')throw Error('Original bound pending report basis required');
 await connection.unsafe("SELECT truss.runtime_require_catalog_input(decode($1::text,'hex'))",[prepared.original.originalUtf8Hex]);
 await connection.unsafe("SELECT truss.runtime_require_pending_association_report_basis_candidate($1::int,decode($2::text,'hex'))",[original.revision,original.hex]);
}
