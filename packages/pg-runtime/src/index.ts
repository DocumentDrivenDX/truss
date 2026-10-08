/** Host-only PostgreSQL driver. Portable Truss package imports no pg dependency. */
export {createFileQueryJournal,type OriginalQueryJournal} from './journal';
import type {OriginalQueryJournal} from './journal';
import {originalQuery,requireOriginalCompletion} from './native-query';
import {Pool, DatabaseError, type PoolClient, type PoolConfig} from 'pg';
import type {NativeConnectionSource,NativeConnection,StatementResult} from '@documentdrivendx/truss-postgresql';
export function createPgConnectionSource(config:PoolConfig,options:{journal?:OriginalQueryJournal}={}): {
  readonly source:NativeConnectionSource;
  readonly quarantinedCount:()=>number;
  readonly close:()=>Promise<void>;
} {
  const pool=new Pool({...config,types:{getTypeParser(_oid:number,format?:string){
    if(format==='binary')throw Error('Binary native carriers unsupported');
    return (text:string)=>text;
  }}});
  const quarantine=new Set<PoolClient>();
  const source:NativeConnectionSource={async acquire(){
    const client=await pool.connect();let ended=false;let started=false;
    const alive=()=>{if(ended||quarantine.has(client))throw Error('Original native connection unavailable');};
    const onError=()=>{quarantine.add(client);};client.on('error',onError);
    const control=async(sql:string,expected?:string)=>{
      alive();const frames=await originalQuery(client,sql,undefined,options.journal);
      try{requireOriginalCompletion(frames,sql==='COMMIT'||sql==='ROLLBACK'?'I':'T',expected);}
      catch(error){quarantine.add(client);throw error;}
    };
    const connection:NativeConnection={
      async begin(options){alive();if(started)throw Error('Already begun');
        const isolation={read_committed:'READ COMMITTED',repeatable_read:'REPEATABLE READ',serializable:'SERIALIZABLE'}[options.isolation];
        const mode={read_only:'READ ONLY',read_write:'READ WRITE'}[options.accessMode];
        if(!isolation||!mode||options.cancellation)throw Error('Unsupported transaction options');
        await control('BEGIN ISOLATION LEVEL '+isolation+' '+mode,'BEGIN');started=true;
      },
      async execute(statement):Promise<StatementResult>{alive();if(!started)throw Error('Not begun');
        const frames=await originalQuery(client,statement.sql,statement.parameters.map(p=>p.carrier==='null'?null:p.text),options.journal);
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
      async control(sql){if(!/^((SAVEPOINT|RELEASE SAVEPOINT|ROLLBACK TO SAVEPOINT) truss_sp_[1-9][0-9]*)$/.test(sql))throw Error('Unregistered control SQL');await control(sql,sql.startsWith('SAVEPOINT ')?'SAVEPOINT':sql.startsWith('RELEASE ')?'RELEASE':'ROLLBACK');},
      async commit(){
        try{await control('COMMIT','COMMIT');started=false;return 'committed';}
        catch(error){
          if(!(error instanceof DatabaseError)||!error.code||! /^(23|40)[0-9A-Z]{3}$/.test(error.code))throw error;
          // Queue on this original connection and confirm rollback before classified settlement.
          await control('ROLLBACK','ROLLBACK');started=false;
          return {status:'rejected',sqlState:error.code};
        }
      },
      async rollback(){await control('ROLLBACK','ROLLBACK');started=false;return 'rolled_back';},
      async release(){alive();if(started)throw Error('Active connection cannot release');ended=true;client.off('error',onError);client.release();},
      async quarantine(){quarantine.add(client);}
    };return connection;
  }};
  return {source,quarantinedCount:()=>quarantine.size,async close(){
    if(quarantine.size)throw Error('Original quarantined custody needs explicit settlement');await pool.end();
  }};
}

export {decodeResponseFrame} from './wire';
export type {WireLimits} from './wire';
export {ResponseIngress} from './wire';
