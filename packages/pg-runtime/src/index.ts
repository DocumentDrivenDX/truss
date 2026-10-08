/** Host-only PostgreSQL driver. Portable Truss package imports no pg dependency. */
import {Pool, type PoolClient, type PoolConfig} from 'pg';
import type {NativeConnectionSource,NativeConnection,StatementResult} from '../../postgresql/src/index';
export function createPgConnectionSource(config:PoolConfig): {
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
      alive();const result=await client.query({text:sql,rowMode:'array'});
      if(Array.isArray(result)||expected&&result.command!==expected)throw Error('Native command correspondence');
    };
    const connection:NativeConnection={
      async begin(options){alive();if(started)throw Error('Already begun');
        const isolation={read_committed:'READ COMMITTED',repeatable_read:'REPEATABLE READ',serializable:'SERIALIZABLE'}[options.isolation];
        const mode={read_only:'READ ONLY',read_write:'READ WRITE'}[options.accessMode];
        if(!isolation||!mode||options.cancellation)throw Error('Unsupported transaction options');
        await control('BEGIN ISOLATION LEVEL '+isolation+' '+mode,'BEGIN');started=true;
      },
      async execute(statement):Promise<StatementResult>{alive();if(!started)throw Error('Not begun');
        const result=await client.query({text:statement.sql,values:statement.parameters.map(p=>p.carrier==='null'?null:p.text),rowMode:'array'});
        if(Array.isArray(result)||result.rowCount===null||!Number.isSafeInteger(result.rowCount)||result.rowCount<0)throw Error('Unsupported native count/result');
        // Command-tag count is protocol metadata, never a stored numeric cell.
        const rows=result.rows.map((row:unknown[])=>row.map(value=>{
          if(value===null)return {state:'null' as const};
          if(typeof value!=='string')throw Error('Non-text native cell');
          return {state:'text' as const,text:value};
        }));
        return {columns:result.fields.map(field=>field.name),rows,affectedRows:String(result.rowCount),command:result.command};
      },
      async control(sql){if(!/^((SAVEPOINT|RELEASE SAVEPOINT|ROLLBACK TO SAVEPOINT) truss_sp_[1-9][0-9]*)$/.test(sql))throw Error('Unregistered control SQL');await control(sql);},
      async commit(){await control('COMMIT','COMMIT');started=false;return 'committed';},
      async rollback(){await control('ROLLBACK','ROLLBACK');started=false;return 'rolled_back';},
      async release(){alive();if(started)throw Error('Active connection cannot release');ended=true;client.off('error',onError);client.release();},
      async quarantine(){quarantine.add(client);}
    };return connection;
  }};
  return {source,quarantinedCount:()=>quarantine.size,async close(){
    if(quarantine.size)throw Error('Original quarantined custody needs explicit settlement');await pool.end();
  }};
}
