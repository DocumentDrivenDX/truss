/** Host-only PostgreSQL driver. Portable Truss package imports no pg dependency. */
export {inspectOriginalQueryFile,type OriginalQueryInspection,createFileQueryJournal,type OriginalQueryJournal,type LocalQueryCustody} from './journal';
import type {OriginalQueryJournal} from './journal';
import {originalQuery,requireOriginalCompletion} from './native-query';
import {randomUUID} from 'node:crypto';
import type {Socket} from 'node:net';
import {Pool, DatabaseError, type PoolClient, type PoolConfig} from 'pg';
import type {NativeConnectionSource,NativeConnection,StatementResult} from '@documentdrivendx/truss-postgresql';
/** Experimental read-only subject preflight. The host must qualify the exact
 * private routine and its immutable deployment; names/shape alone are not trust.
 * It returns one ordered TEXT key tuple for SESSION_USER, or no rows. */
export interface OrdinarySubjectPreflight {
  readonly schema:string; readonly routine:string; readonly keyColumns:readonly string[];
  /** Explicit native input carrier; output keys remain TEXT. Default: text. */
  readonly actorCarrier?:'text'|'name';
}
/** Experimental deployment-qualified zero-argument principal observation.
 * Caller identity remains outside the definer; names alone are not trust. */
export interface OrdinaryPrincipalObserver { readonly schema:string; readonly routine:string }
export function createPgConnectionSource(config:PoolConfig,options:{journal?:OriginalQueryJournal;ordinaryPrincipal?:string;ordinarySubject?:OrdinarySubjectPreflight;ordinaryPrincipalObserver?:OrdinaryPrincipalObserver;originalResponseTimeoutMs?:number}={}): {
  readonly source:NativeConnectionSource;
  readonly quarantinedCount:()=>number;
  readonly close:()=>Promise<void>;
  /** Explicit transport shutdown only; uncertain native outcomes remain unresolved. */
  readonly shutdownQuarantinedTransports:()=>Promise<void>;
} {
  const responseTimeout=options.originalResponseTimeoutMs===undefined?5000:options.originalResponseTimeoutMs;
  if(typeof responseTimeout!=='number'||!Number.isInteger(responseTimeout)||responseTimeout<1||responseTimeout>60000)throw Error('Unsupported original response deadline');
  const principal=options.ordinaryPrincipal;
  if(principal!==undefined&&(typeof principal!=='string'||!principal.length||principal.length>1024||principal.includes('\0')))throw Error('Invalid pinned ordinary principal');
  const nativeIdentifier=(value:string)=>{
    if(typeof value!=='string'||!value.length||value.includes('\0')||[...value].some(c=>c.charCodeAt(0)>=0xd800&&c.charCodeAt(0)<=0xdfff)||new TextEncoder().encode(value).length>63)throw Error('Invalid subject preflight identity');
    return '"'+value.replaceAll('"','""')+'"';
  };
  // Copy the selection before any asynchronous acquisition; caller mutation
  // cannot change an already constructed host's routine or key ordering.
  const subject=options.ordinarySubject===undefined?undefined:Object.freeze({
    schema:nativeIdentifier(options.ordinarySubject.schema),routine:nativeIdentifier(options.ordinarySubject.routine),
    actorCarrier:options.ordinarySubject.actorCarrier===undefined?'text':options.ordinarySubject.actorCarrier,
    keyColumns:Object.freeze([...options.ordinarySubject.keyColumns].map(name=>{nativeIdentifier(name);return name;}))
  });
  if(subject&&((subject.actorCarrier!=='text'&&subject.actorCarrier!=='name')||principal===undefined||!subject.keyColumns.length||subject.keyColumns.length>32||new Set(subject.keyColumns).size!==subject.keyColumns.length))throw Error('Subject preflight requires pinned principal and ordered key');
  const observer=options.ordinaryPrincipalObserver===undefined?undefined:Object.freeze({
    schema:nativeIdentifier(options.ordinaryPrincipalObserver.schema),routine:nativeIdentifier(options.ordinaryPrincipalObserver.routine)
  });
  if(observer&&principal===undefined)throw Error('Principal observer requires pinned principal');
  const pool=new Pool({...config,types:{getTypeParser(_oid:number,format?:string){
    if(format==='binary')throw Error('Binary native carriers unsupported');
    return (text:string)=>text;
  }}});
  const quarantine=new Set<PoolClient>();const active=new Set<PoolClient>();let admissionClosed=false;let poolEnded=false;
  const source:NativeConnectionSource={async acquire(){
    if(admissionClosed)throw Error('Host admission closed');
    const client=await pool.connect();
    if(admissionClosed){client.release();throw Error('Host admission closed');}
    active.add(client);let ended=false;let started=false;let subjectPending=false;
    const lease=randomUUID();let ordinal=0n;
    const query=(sql:string,values?:readonly (string|null)[])=>originalQuery(client,sql,values,options.journal,{lease,ordinal:(ordinal++).toString()},responseTimeout);
    const alive=()=>{if(ended||quarantine.has(client))throw Error('Original native connection unavailable');};
    const ready=()=>{alive();if(subjectPending)throw Error('Subject preflight still pending');};
    const onError=()=>{quarantine.add(client);};client.on('error',onError);
    const control=async(sql:string,expected?:string)=>{
      alive();const frames=await query(sql);
      try{requireOriginalCompletion(frames,sql==='COMMIT'||sql==='ROLLBACK'?'I':'T',expected);}
      catch(error){quarantine.add(client);throw error;}
    };
    // A configured ordinary-principal source observes the actual
    // native session identity. This pin selects context, never a caller credential/policy.
    const verifyPrincipal=async(requireCurrent:boolean,status:'I'|'T'='I')=>{
      const frames=await query(observer
        ? 'SELECT SESSION_USER AS original_actor,CURRENT_USER AS effective_actor,p.native_superuser,p.native_bypass,p.native_encoding FROM '+observer.schema+'.'+observer.routine+'() p'
        : "SELECT session_user::pg_catalog.text AS original_actor,current_user::pg_catalog.text AS effective_actor,(SELECT rolsuper::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) session_user) AS native_superuser,(SELECT rolbypassrls::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) session_user) AS native_bypass,pg_catalog.current_setting('client_encoding')::pg_catalog.text AS native_encoding");
      requireOriginalCompletion(frames,status);
      const descriptions=frames.filter(frame=>frame.kind==='T'),rows=frames.filter(frame=>frame.kind==='D');
      if(descriptions.length!==1||JSON.stringify(descriptions[0].fields.map(field=>field.name))!==JSON.stringify(['original_actor','effective_actor','native_superuser','native_bypass','native_encoding'])||descriptions[0].fields.some((field,i)=>field.typeOid!==(observer&&i<2?'19':'25')||field.format!=='0')||rows.length!==1||rows[0].fields.length!==5||rows[0].fields.some(field=>typeof field.hex!=='string'))throw Error('Original principal response unavailable');
      const values=rows[0].fields.map(field=>new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(Buffer.from(field.hex!,'hex')));
      if(values[0]!==principal||requireCurrent&&values[1]!==principal||values[2]!=='false'||values[3]!=='false'||values[4]!=='UTF8')throw Error('Pinned ordinary principal unavailable');
    };
    const verifySubject=async()=>{
      if(!subject)return;
      const frames=await query('SELECT * FROM '+subject.schema+'.'+subject.routine+(subject.actorCarrier==='name'?'(SESSION_USER)':'(SESSION_USER::pg_catalog.text)'));
      requireOriginalCompletion(frames,'T');
      const descriptions=frames.filter(frame=>frame.kind==='T'),rows=frames.filter(frame=>frame.kind==='D');
      if(descriptions.length!==1||JSON.stringify(descriptions[0].fields.map(field=>field.name))!==JSON.stringify(subject.keyColumns)||descriptions[0].fields.some(field=>field.typeOid!=='25'||field.format!=='0')||rows.length!==1||rows[0].fields.length!==subject.keyColumns.length||rows[0].fields.some(field=>typeof field.hex!=='string'||field.hex.length>131072))throw Error('Original subject binding unavailable');
      // Validate native UTF-8 without converting identities through JS numbers.
      rows[0].fields.forEach(field=>new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(Buffer.from(field.hex!,'hex')));
    };
    const resetPrincipal=async()=>{
      try{
        alive();await verifyPrincipal(false);
        for(const statement of ['RESET ROLE','RESET SESSION AUTHORIZATION','RESET ALL']){
          requireOriginalCompletion(await query(statement),'I','RESET');
        }
        await verifyPrincipal(true);
      }catch(error){
        quarantine.add(client);admissionClosed=true;
        // Preserve original checkout/custody on reset or identity uncertainty.
        // It cannot return to the pool; explicit transport shutdown remains available.
        throw error;
      }
    };
    if(principal!==undefined)await resetPrincipal();
    // Another pending reset can close admission while this checkout awaits its
    // original response. Never publish a lease after that closure; retain its
    // checkout for explicit quarantine shutdown alongside the failing one.
    if(admissionClosed){quarantine.add(client);throw Error('Host admission closed');}
    const connection:NativeConnection={
      async begin(options){ready();if(started)throw Error('Already begun');
        const isolation={read_committed:'READ COMMITTED',repeatable_read:'REPEATABLE READ',serializable:'SERIALIZABLE'}[options.isolation];
        const mode={read_only:'READ ONLY',read_write:'READ WRITE'}[options.accessMode];
        if(!isolation||!mode||options.cancellation)throw Error('Unsupported transaction options');
        if(subject&&(options.isolation==='read_committed'||options.accessMode!=='read_only'))throw Error('Subject preflight requires stable read-only transaction');
        subjectPending=subject!==undefined;
        try{
          await control('BEGIN ISOLATION LEVEL '+isolation+' '+mode,'BEGIN');started=true;
          if(principal!==undefined)try{await verifyPrincipal(true,'T');await verifySubject();}catch(error){quarantine.add(client);admissionClosed=true;throw error;}
        }finally{subjectPending=false;}
      },
      async execute(statement):Promise<StatementResult>{ready();if(!started)throw Error('Not begun');
        const frames=await query(statement.sql,statement.parameters.map(p=>p.carrier==='null'?null:p.text));
        try{requireOriginalCompletion(frames,'T');}catch(error){quarantine.add(client);throw error;}
        const descriptions=frames.filter(frame=>frame.kind==='T'),commands=frames.filter(frame=>frame.kind==='C');
        if(descriptions.length>1||commands.length!==1)throw Error('Unsupported original response inventory');
        const original=commands[0].fields[0];const command=original.command!.split(' ')[0];
        const noCount=original.affectedRows===null&&['CREATE','DROP','ALTER','SET','GRANT','REVOKE','COMMENT'].includes(command);
        if(original.affectedRows===null&&!noCount)throw Error('Unknown original command count');
        const rows=frames.filter(frame=>frame.kind==='D').map(frame=>frame.fields.map(field=>{
          if(field.hex===null)return {state:'null' as const};
          return {state:'text' as const,text:new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(Buffer.from(field.hex!,'hex'))};
        }));
        return {columns:descriptions[0]?.fields.map(field=>field.name!)??[],rows,affectedRows:noCount?'0':original.affectedRows!,command};
      },
      async control(sql){ready();if(!/^((SAVEPOINT|RELEASE SAVEPOINT|ROLLBACK TO SAVEPOINT) truss_sp_[1-9][0-9]*)$/.test(sql))throw Error('Unregistered control SQL');await control(sql,sql.startsWith('SAVEPOINT ')?'SAVEPOINT':sql.startsWith('RELEASE ')?'RELEASE':'ROLLBACK');},
      async commit(){
        ready();try{await control('COMMIT','COMMIT');started=false;return 'committed';}
        catch(error){
          if(!(error instanceof DatabaseError)||!error.code||! /^(23|40)[0-9A-Z]{3}$/.test(error.code))throw error;
          // Queue on this original connection and confirm rollback before classified settlement.
          await control('ROLLBACK','ROLLBACK');started=false;
          return {status:'rejected',sqlState:error.code};
        }
      },
      async rollback(){ready();await control('ROLLBACK','ROLLBACK');started=false;return 'rolled_back';},
      async release(){ready();if(started)throw Error('Active connection cannot release');if(principal!==undefined)await resetPrincipal();ended=true;client.off('error',onError);client.release();active.delete(client);},
      async quarantine(){quarantine.add(client);}
    };
    // Each original socket parser/journal belongs to one operation until all
    // original frames settle. Refuse overlap locally; do not queue native work.
    let busy=false;
    const exclusive=<A extends unknown[],R>(operation:(...args:A)=>Promise<R>)=>async(...args:A):Promise<R>=>{
      ready();if(busy)throw Error('Original native operation still pending');
      busy=true;try{return await operation(...args);}finally{busy=false;}
    };
    connection.begin=exclusive(connection.begin);
    connection.execute=exclusive(connection.execute);
    connection.control=exclusive(connection.control);
    connection.commit=exclusive(connection.commit);
    connection.rollback=exclusive(connection.rollback);
    connection.release=exclusive(connection.release);
    return connection;
  }};
  return {source,quarantinedCount:()=>quarantine.size,async close(){
    if(quarantine.size)throw Error('Original quarantined custody needs explicit settlement');
    if(active.size)throw Error('Original active checkout still held');admissionClosed=true;if(!poolEnded){await pool.end();poolEnded=true;}
  },async shutdownQuarantinedTransports(){
    if(poolEnded)return;
    if([...active].some(client=>!quarantine.has(client)))throw Error('Healthy active checkout cannot be shut down through quarantine');
    admissionClosed=true;
    for(const client of quarantine){
      if(!active.has(client))continue;
      const stream=(client as unknown as {connection:{stream:Socket}}).connection?.stream;
      if(!stream)throw Error('Original transport unavailable for shutdown');
      if(!stream.closed)await new Promise<void>((resolve,reject)=>{
        const timeout=setTimeout(()=>{stream.off('close',closed);reject(Error('Original transport shutdown unresolved'));},5000);
        const closed=()=>{clearTimeout(timeout);resolve();};stream.once('close',closed);stream.destroy();
      });
      // Actual local close only: retain the original quarantine object and its
      // unresolved native outcome, while removing its dead pool checkout.
      client.release(true);active.delete(client);
    }
    await pool.end();poolEnded=true;
  }};
}

export {decodeResponseFrame} from './wire';
export type {WireLimits} from './wire';
export {ResponseIngress} from './wire';
