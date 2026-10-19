// SPDX-License-Identifier: MIT OR Apache-2.0
import type {PGlite} from '@electric-sql/pglite';
// Original pinned browser-compatible owner bundle; it publishes JavaScript only.
// @ts-expect-error Original UMF JavaScript bundle has no declaration file.
import * as owner from '../python/src/truss/_umf_core08/producer.js';
import lineageSql from '../python/src/truss/_catalog_runtime/lineage.sql' with {type:'text'};
import containersSql from '../python/src/truss/_catalog_runtime/containers.sql' with {type:'text'};
import planSql from '../python/src/truss/_catalog_runtime/plan.sql' with {type:'text'};
import {preflightSourceJson} from '../postgresql/src/acceptance-json';
import {collectCatalogDeclarations} from '../umf-bun/src/catalog-declarations';

export const CATALOG_PROFILE='truss-browser-catalog/0.1';
export interface DocumentInput {documentId:string;documentRevision:string;sourceUtf8:string}
export interface CatalogSnapshot {profile:typeof CATALOG_PROFILE;catalogRevision:string;document:Record<string,unknown>;types:unknown[];properties:unknown[];keys:unknown[];changes:unknown[]}
export type Registration={outcome:'registered'|'unchanged';catalog:CatalogSnapshot}|{outcome:'refused';reason:'catalog_already_registered'};
const tables=['schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint','schema_change'] as const;
const encode=(value:unknown)=>new TextEncoder().encode(JSON.stringify(value));
export function captureDocument(input:DocumentInput):Readonly<DocumentInput>{
  if(!input||Object.keys(input).sort().join(',')!=='documentId,documentRevision,sourceUtf8')throw Error('Closed original document input required');
  const {documentId,documentRevision,sourceUtf8}=input;
  if([documentId,documentRevision].some(x=>typeof x!=='string'||!x||x.includes('\0')||new TextEncoder().encode(x).length>4096
    ||new TextDecoder('utf-8',{fatal:true}).decode(new TextEncoder().encode(x))!==x)
    ||typeof sourceUtf8!=='string'||new TextEncoder().encode(sourceUtf8).length>65536)
    throw Error('Bounded original document required');
  return Object.freeze({documentId,documentRevision,sourceUtf8});
}
function closed(value:any,names:string[]){
  if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!names.includes(k)))throw Error('Unsupported browser catalog declaration');
}
export async function prepareDocument(input:Readonly<DocumentInput>){
  const bytes=new TextEncoder().encode(input.sourceUtf8);
  if(new TextDecoder('utf-8',{fatal:true}).decode(bytes)!==input.sourceUtf8)throw Error('Lossless UTF8 source required');
  preflightSourceJson(bytes);
  const source=owner.readDocument(input.sourceUtf8,'json'),validation=owner.validateDocument(source);
  if(source.umf!=='0.8.0'||source.id!==input.documentId||!validation.valid||!Array.isArray(validation.diagnostics)
    ||validation.diagnostics.some((d:any)=>d.code!=='UNKNOWN_EXTENSION'||d.path!=='/vocabularies/umf.actions'||d.severity!=='warning')
    ||!validation.complete&&!validation.diagnostics.length)throw Error('Original supported UMF core required');
  closed(source,['umf','id','vocabularies','modules']);
  if(source.vocabularies){closed(source.vocabularies,['umf.actions']);if(source.vocabularies['umf.actions']){
    closed(source.vocabularies['umf.actions'],['version']);if(source.vocabularies['umf.actions'].version!=='0.1.0')throw Error('Unsupported opaque actions version');}}
  if(!Array.isArray(source.modules)||source.modules.length<1||source.modules.length>16)throw Error('Bounded modules required');
  const elements=source.modules.flatMap((m:any)=>m.elements??[]);
  if(elements.length<1||elements.length>65||bytes.length*(elements.length*7+16)>8388608)throw Error('Bounded complete declarations required');
  const observations:any[]=[];
  const inspect=(operation:string,identity:any)=>{const result=owner[operation](source,identity);observations.push({operation,identity,result});return result.meaning;};
  const records:any[]=[],fields:any[]=[];
  for(const module of source.modules){
    closed(module,['id','namespace','elements','extensions']);
    if(module.relationships!==undefined)throw Error('Relationships outside browser catalog profile');
    if(module.extensions)closed(module.extensions,['umf.actions']);
    if(!Array.isArray(module.elements))throw Error('Explicit module elements required');
    for(const element of module.elements){
      const identity={module:module.id,element:element.id};
      if(inspect('inspectCoreElementKind',identity).kind!==element.kind)throw Error('Original element kind required');
      if(inspect('inspectCoreReferenceLinks',identity).state!=='missing')throw Error('Unsupported reference links');
      if(element.extensions)closed(element.extensions,[]);
      if(element.kind==='record'){
        closed(element,['id','name','kind','members','keys','extensions']);
        const members=inspect('inspectCoreRecordMembers',identity),keys=inspect('inspectCoreKeys',identity);
        if(members.state!=='known'||members.uninterpretedPaths.length||keys.state!=='known'||keys.uninterpretedPaths.length
          ||keys.keys.length!==1||keys.keys[0].primary!==true||keys.keys[0].fields.length!==1)throw Error('Explicit single primary key required');
        records.push({identity,members:members.members});
      }else if(element.kind==='field'){
        closed(element,['id','name','kind','scalarType','nullability','cardinality','extensions']);
        if(typeof element.name!=='string'||!element.name||element.name.includes('\0')
          ||inspect('inspectCoreScalarType',identity).scalarType!=='string'
          ||inspect('inspectCoreNullability',identity).nullability!=='required'
          ||inspect('inspectCoreCardinality',identity).cardinality!=='one'
          ||inspect('inspectCoreFacets',identity).state!=='missing')throw Error('Required singular String subset required');
        fields.push(identity);
      }else throw Error('Unsupported element kind');
    }
  }
  if(records.length!==1||!fields.length||records[0].members.length!==fields.length
    ||fields.some(f=>!records[0].members.some((m:any)=>m.module===f.module&&m.element===f.element)))throw Error('Complete single Record membership required');
  const sourceSha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(n=>n.toString(16).padStart(2,'0')).join('');
  const evidence={sourceValidation:validation,observations,producerRevision:'7c0f0c98beee2cc1a5a407992b5c53cc2616da8e',producerSha256:'88899e3c1221ca3998e80a878d37d5344d68062afa82eb15d6cffc49dd3752f3',scope:'core_catalog_only_actions_opaque'};
  if(encode(evidence).length>8388608)throw Error('Catalog evidence limit');
  return {input,sourceSha256,declarations:[collectCatalogDeclarations(input.documentId,source)],documents:[{documentId:input.documentId,revision:input.documentRevision,umfVersion:'0.8.0',originalText:input.sourceUtf8,validation:evidence}]};
}

export async function readCatalog(db:Pick<PGlite,'query'>):Promise<CatalogSnapshot|null>{
  const result=(await db.query<{catalog:CatalogSnapshot|null}>(`SELECT CASE WHEN h.rev=0 THEN NULL ELSE jsonb_build_object(
    'profile','${CATALOG_PROFILE}','catalogRevision',h.rev::text,
    'document',(SELECT jsonb_build_object('documentId',doc_id,'documentRevision',doc_revision,'sourceSha256',content_sha256,'sourceUtf8',document,'validation',validation) FROM truss.schema_doc WHERE rev=h.rev AND ord=0),
    'types',(SELECT coalesce(jsonb_agg(jsonb_build_object('typeId',type_id::text,'documentId',document_id,'moduleId',module,'recordId',element,'lineageProfile',lineage_profile,'lineageHex',encode(lineage_bytes,'hex')) ORDER BY type_id),'[]') FROM truss.type_def),
    'properties',(SELECT coalesce(jsonb_agg(jsonb_build_object('propertyId',prop_id::text,'typeId',type_id::text,'moduleId',declaration_module,'fieldId',element,'name',name) ORDER BY prop_id),'[]') FROM truss.prop_def),
    'keys',(SELECT coalesce(jsonb_agg(jsonb_build_object('typeId',type_id::text,'keyId',key_id,'keyNumber',key_num::text,'propertyIds',(SELECT jsonb_agg(n::text ORDER BY ord) FROM unnest(prop_ids) WITH ORDINALITY p(n,ord)),'primary',is_primary) ORDER BY type_id,key_num),'[]') FROM truss.key_def),
    'changes',(SELECT coalesce(jsonb_agg(to_jsonb(c) ORDER BY seq),'[]') FROM truss.schema_change c WHERE rev=h.rev)) END AS catalog FROM truss.schema_head h WHERE id=1`)).rows;
  if(result.length!==1)throw Error('Original catalog head required');
  return result[0]!.catalog;
}

export async function registerCatalog(db:PGlite,prepared:Awaited<ReturnType<typeof prepareDocument>>):Promise<Registration>{
  return db.transaction<Registration>(async tx=>{
    const head=(await tx.query<{rev:number}>('SELECT rev FROM truss.schema_head WHERE id=1 FOR UPDATE')).rows[0];
    if(head?.rev!==0){
      const docs=(await tx.query<{doc_id:string;doc_revision:string;document:string}>('SELECT doc_id,doc_revision,document FROM truss.schema_doc ORDER BY rev,ord')).rows;
      if(docs.length===1&&docs[0]!.doc_id===prepared.input.documentId&&docs[0]!.doc_revision===prepared.input.documentRevision&&docs[0]!.document===prepared.input.sourceUtf8)
        return {outcome:'unchanged',catalog:await readCatalog(tx) as CatalogSnapshot};
      return {outcome:'refused',reason:'catalog_already_registered'};
    }
    for(const sql of [lineageSql,containersSql,planSql])await tx.exec(sql);
    const prior:Record<string,unknown>={schema_rev:(await tx.query<{rows:unknown}>('SELECT jsonb_agg(to_jsonb(r)) AS rows FROM truss.schema_rev r')).rows[0]!.rows};
    for(const table of tables)if(table!=='schema_rev')prior[table]=[];
    const planned=(await tx.query<{plan:Record<string,any[]>}>(`SELECT truss.catalog_revision_plan($1::jsonb,truss.catalog_expected_records($2::bytea,$3::bytea,$4::bytea,transaction_timestamp(),(SELECT accepted_at FROM truss.schema_rev WHERE rev=0),1,0,0,0)) AS plan`,[JSON.stringify(prior),encode(prepared.declarations),encode(prepared.documents),encode({})])).rows[0]!.plan;
    for(const table of tables){
      let rows=planned[table]!;if(table==='schema_rev')rows=rows.filter(r=>r.rev!==0);
      if(table==='schema_change'){await tx.query('INSERT INTO truss.schema_change SELECT * FROM truss.catalog_planned_changes($1::jsonb)',[JSON.stringify(rows)]);continue;}
      const columns=(await tx.query<{columns:string}>("SELECT string_agg(quote_ident(attname),',' ORDER BY attnum) AS columns FROM pg_attribute WHERE attrelid=to_regclass($1) AND attnum>0 AND NOT attisdropped AND attgenerated=''",['truss.'+table])).rows[0]!.columns;
      await tx.query(`INSERT INTO truss.${table}(${columns}) SELECT ${columns} FROM jsonb_populate_recordset(NULL::truss.${table},$1::jsonb)`,[JSON.stringify(rows)]);
    }
    await tx.query('UPDATE truss.schema_head SET rev=1 WHERE id=1');
    return {outcome:'registered',catalog:await readCatalog(tx) as CatalogSnapshot};
  });
}
