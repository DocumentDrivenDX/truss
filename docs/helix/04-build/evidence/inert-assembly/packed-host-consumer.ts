import {createPgConnectionSource} from '@documentdrivendx/truss-pg-runtime';
import {createEngineExecutor} from '@documentdrivendx/truss-postgresql';
import type {NativeConnectionSource,TransactionHandle} from '@documentdrivendx/truss-postgresql';
const host=createPgConnectionSource({host:'127.0.0.1',port:1,user:'unused',database:'unused',max:1});
const source:NativeConnectionSource=host.source;
const executor=createEngineExecutor(source);
// Exact public handle relation compiles without a brand-repair assertion.
const typed=(handle:TransactionHandle)=>executor.execute(handle,{sql:'SELECT 1',parameters:[]});
if(typeof typed!=='function'||host.quarantinedCount()!==0)throw Error('Public construction failed');
await host.close();
console.log('Packed host construction closes without acquiring a connection.');
