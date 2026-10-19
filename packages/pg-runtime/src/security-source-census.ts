// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private PostgreSQL17.9 census transport. No source/issuer or held-cut authority. */
import {createHash,randomUUID} from 'node:crypto';
import type {PoolClient} from 'pg';
import {originalQuery,requireOriginalCompletion} from './native-query';
import type {OriginalQueryJournal} from './journal';
import type {decodeResponseFrame} from './wire';
type Frame=ReturnType<typeof decodeResponseFrame>;
const MAX_BYTES=16777216,CHUNK_BYTES=32768,FETCH_ROWS=16,MAX_WIRE_BYTES=41943040;
const SOURCE_SHA256='3fc1e0e10e9acc09b8437877968de921c9a06982f8c052567766baeb261a1735';
const text=(field:Readonly<Record<string,string|null>>):string=>{
 if(typeof field.hex!=='string'||! /^(?:[0-9a-f]{2})*$/.test(field.hex))throw Error('Census text required');
 return new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(Buffer.from(field.hex,'hex'));
};
function rows(frames:readonly Frame[],status:'I'|'T',command:string,names:readonly string[]):string[][] {
 requireOriginalCompletion(frames,status,command);
 if(frames.map(f=>f.kind).join('')!=='T'+'D'.repeat(frames.length-3)+'CZ')throw Error('Census response inventory');
 const descriptors=frames[0].fields;
 if(descriptors.length!==names.length||descriptors.some((f,i)=>f.name!==names[i]||f.typeOid!=='25'||f.format!=='0'||f.typeSize!=='-1'||f.typeModifier!=='-1'))throw Error('Census text descriptor');
 return frames.slice(1,-2).map(f=>{
  if(f.fields.length!==names.length)throw Error('Census row width');
  return f.fields.map(text);
 });
}
/** Synthetic callers can supply frames: this assembler never confers original ingress custody. */
export class CensusChunkAssembly {
 #image:Buffer|undefined;#next=0;#ended=false;#failed=false;#offset=0;
 accept(frames:readonly Frame[]):void {
  try{
   if(this.#failed||this.#ended)throw Error('Census assembly ended');
   const count=frames.filter(f=>f.kind==='D').length;
   if(count>FETCH_ROWS)throw Error('Census fetch row limit');
   const batch=rows(frames,'T','FETCH '+count,['ordinal','total_bytes','chunk_hex']);
   if(!batch.length){
    if(!this.#image||this.#offset!==this.#image.length)throw Error('Census truncated');
    this.#ended=true;return;
   }
   for(const [ordinal,total,hex] of batch){
    if(! /^(0|[1-9][0-9]*)$/.test(ordinal)||ordinal!==String(this.#next)||! /^[1-9][0-9]{0,7}$/.test(total))throw Error('Census ordinal or size');
    const size=Number(total);
    if(size>MAX_BYTES)throw Error('Census image limit');
    if(!this.#image)this.#image=Buffer.alloc(size);
    if(size!==this.#image.length||this.#offset>=size||! /^(?:[0-9a-f]{2})+$/.test(hex))throw Error('Census chunk shape');
    const expected=Math.min(CHUNK_BYTES,size-this.#offset);
    if(hex.length!==expected*2)throw Error('Census chunk width');
    this.#image.set(Buffer.from(hex,'hex'),this.#offset);this.#offset+=expected;this.#next++;
   }
  }catch(error){this.#failed=true;this.#image=undefined;throw error;}
 }
 finish():string {
  if(this.#failed||!this.#ended||!this.#image)throw Error('Complete census required');
  try{return new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(this.#image);}
  catch(error){this.#failed=true;this.#image=undefined;throw error;}
 }
 get ended():boolean{return this.#ended;}
 get chunks():number{return this.#next;}
}

/** Requires host-exclusive use of one idle client for the entire call.
 * Idle status cannot establish exclusive ownership; uncoordinated client users
 * must be excluded by the host. This function does not implement a pool lease.
 * Owns its new transaction. Expected SQL is source-pinned, not authenticated.
 * Journals contain sensitive private source/configuration. Caller supplies a private journal.
 * Repeatable read stabilizes this materialized observation, not the authority execution cut.
 */
export async function captureSourceCensus(client:PoolClient,sourceSql:string,journal:OriginalQueryJournal):Promise<Readonly<{originalText:string;wireBytes:number;responses:number;chunks:number}>> {
 if(!journal||typeof journal.begin!=='function')throw Error('Private original journal required');
 if(createHash('sha256').update(sourceSql).digest('hex')!==SOURCE_SHA256)throw Error('Reviewed census source required');
 const lease=randomUUID(),cursor='truss_census_'+lease.replaceAll('-','');let ordinal=0n,wireBytes=0,begun=false;
 const query=async(sql:string)=>{
  if(ordinal>=40n)throw Error('Census response limit');
  const frames=await originalQuery(client,sql,undefined,journal,{lease,ordinal:(ordinal++).toString()});
  for(const f of frames){wireBytes+=f.originalHex.length/2;if(wireBytes>MAX_WIRE_BYTES)throw Error('Census cumulative wire limit');}
  return frames;
 };
 const control=async(sql:string,status:'I'|'T',command:string)=>{
  const frames=await query(sql);requireOriginalCompletion(frames,status,command);
  if(frames.map(f=>f.kind).join('')!=='CZ')throw Error('Census control inventory');
 };
 // Do not assume ownership or roll back a transaction supplied by the caller.
 const context=rows(await query("SELECT pg_catalog.current_setting('server_version_num')::pg_catalog.text AS version,pg_catalog.current_setting('client_encoding')::pg_catalog.text AS encoding"),'I','SELECT 1',['version','encoding']);
 if(context.length!==1||context[0][0]!=='170009'||context[0][1]!=='UTF8')throw Error('Qualified census context required');
 try{
  // Mark ownership before dispatch: an uncertain BEGIN must not release a reusable connection.
  begun=true;await control('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY','T','BEGIN');
  const sql=sourceSql.trim().replace(/;$/,'');
  const chunkSql=`WITH image AS MATERIALIZED (SELECT pg_catalog.convert_to(census,'UTF8') AS body FROM (${sql}) AS source_census)
   SELECT part::pg_catalog.text AS ordinal,pg_catalog.octet_length(body)::pg_catalog.text AS total_bytes,
    pg_catalog.encode(pg_catalog.substring(body,part*${CHUNK_BYTES}+1,${CHUNK_BYTES}),'hex') AS chunk_hex
   FROM image LEFT JOIN LATERAL pg_catalog.generate_series(0,(pg_catalog.octet_length(body)-1)/${CHUNK_BYTES}) AS part ON true ORDER BY part`;
  await control(`DECLARE ${cursor} NO SCROLL CURSOR FOR ${chunkSql}`,'T','DECLARE CURSOR');
  const assembly=new CensusChunkAssembly();
  while(!assembly.ended)assembly.accept(await query(`FETCH FORWARD ${FETCH_ROWS} FROM ${cursor}`));
  const originalText=assembly.finish();
  await control(`CLOSE ${cursor}`,'T','CLOSE CURSOR');
  await control('COMMIT','I','COMMIT');begun=false;
  return Object.freeze({originalText,wireBytes,responses:Number(ordinal),chunks:assembly.chunks});
 }catch(error){
  if(begun){try{await control('ROLLBACK','I','ROLLBACK');begun=false;}catch{(client as unknown as {connection:{stream:{destroy():void}}}).connection.stream.destroy();}}
  throw error;
 }
}
