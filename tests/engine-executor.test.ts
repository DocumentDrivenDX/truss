import {test,expect} from 'bun:test';
import {createEngineExecutor,type NativeConnection,type TransactionHandle} from '../packages/postgresql/src/index';
function fixture(commitFails=false){
  const calls:string[]=[];
  const connection:NativeConnection={async begin(){calls.push('begin');},async execute(){calls.push('execute');return {columns:['id'],rows:[[{state:'text',text:'9007199254740993123'}]],affectedRows:'1',command:'SELECT'};},
    async control(sql){calls.push(sql);},async commit(){calls.push('commit');if(commitFails)throw Error('lost response');return 'committed';},async rollback(){calls.push('rollback');return 'rolled_back';},async release(){calls.push('release');},async quarantine(reason){calls.push('quarantine:'+reason);}};
  return {calls,connection,executor:createEngineExecutor({async acquire(){return connection;}})};
}
const options={isolation:'serializable' as const,accessMode:'read_write' as const};
test('engine commit, exact cells and ended handle refusal',async()=>{
  const f=fixture();let retained:TransactionHandle|undefined;
  const result=await f.executor.withTransaction(options,async handle=>{retained=handle;
    const read=await f.executor.execute(handle,{sql:'SELECT id::text',parameters:[]});expect(read.status).toBe('ok');
    const point=await f.executor.savepoint(handle);if(point.status!=='ok')throw Error();
    expect((await f.executor.rollbackToSavepoint(handle,point.value)).status).toBe('ok');
    expect((await f.executor.releaseSavepoint(handle,point.value)).status).toBe('ok');return 'done';});
  expect(result).toEqual({status:'ok',value:{value:'done',durability:'committed'}});
  expect(f.calls.slice(-2)).toEqual(['commit','release']);
  expect((await f.executor.execute(retained!,{sql:'SELECT 1',parameters:[]})).status).toBe('error');
});
test('original callback exception follows confirmed rollback',async()=>{
  const f=fixture();const original=Error('callback');
  try{await f.executor.withTransaction(options,async()=>{throw original;});throw Error('unexpected');}catch(error){expect(error).toBe(original);}
  expect(f.calls).toEqual(['begin','rollback','release']);
});
test('unknown commit retains quarantined resource and never rolls back or releases',async()=>{
  const f=fixture(true);const result=await f.executor.withTransaction(options,async()=>42);
  expect(result).toMatchObject({status:'error',error:{code:'commit_unknown',retryScope:'none'}});
  expect(f.calls).toEqual(['begin','commit','quarantine:commit_unknown']);
});
test('foreign adapter handle and unsupported adoption never touch native ports',async()=>{
  const a=fixture(),b=fixture();
  await a.executor.withTransaction(options,async handle=>{expect((await b.executor.execute(handle,{sql:'SELECT 1',parameters:[]})).status).toBe('error');});
  expect(b.calls).toEqual([]);
});

test('invalid carrier domains refuse before native execution',async()=>{
  for(const parameter of [{carrier:'integer',text:'1.5'},{carrier:'decimal',text:'NaN'},{carrier:'boolean',text:'yes'},{carrier:'json',text:'{broken'}]){
    const f=fixture();
    const result=await f.executor.withTransaction(options,async handle=>f.executor.execute(handle,{sql:'SELECT $1',parameters:[{position:1,...parameter} as any]}));
    expect(result.status).toBe('error');expect(f.calls).toEqual(['begin','rollback','release']);
  }
});
