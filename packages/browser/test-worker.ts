import {openBrowserStore,type StoreOpen} from './store';
import {PGlite} from '@electric-sql/pglite';
let registeredAction:any,readGrant:any,previousAction:any,materialized:any;
declare const self:DedicatedWorkerGlobalScope;
let current:StoreOpen|undefined;
let pending=Promise.resolve();
self.onmessage=event=>{
  pending=pending.then(async()=>{
    try{
      if(event.data.command==='open'){
        current=await openBrowserStore({name:event.data.name,layoutSql:await(await fetch(new URL('layout.sql',import.meta.url))).text()});
        self.postMessage(current.outcome==='available'?{outcome:'available',info:current.store.info(current.owner)}:current);
      }else if(event.data.command==='forged'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        try{current.store.info({} as any);throw Error('Forged owner admitted');}
        catch(error){if(String(error).includes('Forged owner admitted'))throw error;}
        self.postMessage({outcome:'refused'});
      }else if(event.data.command==='close'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        await current.store.close(current.owner);self.postMessage({outcome:'closed'});
      }else if(event.data.command==='register'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        const sourceUtf8=await(await fetch(new URL('model.json',import.meta.url))).text();
        const result=await current.store.registerDocument(current.owner,{documentId:'product-local-action-demo',documentRevision:'b8ce3cfe76eeda7c1531b2bbf8aba121c9d9614800ff1f3301f853c048516f27',sourceUtf8});
        self.postMessage(result);
      }else if(event.data.command==='action'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        const registered=await current.store.registerAction(current.owner,{module:'sales',action:'set-name-local'});
        registeredAction=registered.action;
        const granted=await current.store.grantSelectionRead(current.owner,registeredAction);readGrant=granted.grant;
        self.postMessage({outcome:'action_registered',modelSha256:registered.model.sha256,preparationSha256:registered.preparation.sha256,declaration:granted.declaration,opaque:JSON.stringify(registered.action)==='{}'&&JSON.stringify(readGrant)==='{}'});
      }else if(event.data.command==='forgedAction'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        try{await current.store.grantSelectionRead(current.owner,{} as any);throw Error('Forged action admitted');}
        catch(error){if(String(error).includes('Forged action admitted'))throw error;}
        self.postMessage({outcome:'refused'});
      }else if(event.data.command==='reopenAction'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        previousAction=registeredAction;const name=event.data.name;
        await current.store.close(current.owner);current=await openBrowserStore({name,layoutSql:await(await fetch(new URL('layout.sql',import.meta.url))).text()});
        if(current.outcome!=='available')throw Error('Reopen required');
        try{await current.store.grantSelectionRead(current.owner,previousAction);throw Error('Previous action admitted');}
        catch(error){if(String(error).includes('Previous action admitted'))throw error;}
        self.postMessage({outcome:'previous_action_refused',info:current.store.info(current.owner)});
      }else if(event.data.command==='seedFixture'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const target={documentId:'product-local-action-demo',module:'sales',record:'products'};
        const rows=[['bar','Sample'],['baz','Sample'],['qux','Sample'],['spare','Untouched']].map(([id,name])=>({fields:[{module:'sales',field:'product-id',value:id!},{module:'sales',field:'product-name',value:name!}]}));
        const input={target,rows,request:{requestKey:'initial-products',attempt:'load-1'}};
        const loaded=await current.store.loadObjects(current.owner,input);
        if(loaded.outcome!=='loaded')throw Error(JSON.stringify(loaded));
        const replay=await current.store.loadObjects(current.owner,input);
        if(JSON.stringify(replay)!==JSON.stringify(loaded))throw Error('Load replay changed');
        const refused=await current.store.loadObjects(current.owner,{...input,rows:[{fields:[{module:'sales',field:'product-id',value:'would-be-new'},{module:'sales',field:'product-name',value:'New'}]},rows[0]!],request:{requestKey:'duplicate-load',attempt:'load-2'}});
        if(refused.outcome!=='failure'||refused.settlement!=='current_attempt_rolled_back')throw Error('Duplicate key must refuse full load');
        const read=await current.store.readObjects(current.owner,target);
        if(read.length!==4||read.some(r=>r.fields.some(f=>f.value==='would-be-new')))throw Error('Partial load leaked');
        self.postMessage({outcome:'public_objects_loaded',loaded,replayedByteEqual:true,duplicate:refused.outcome,read});
      }else if(event.data.command==='recoverLoad'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const target={documentId:'product-local-action-demo',module:'sales',record:'products'};
        const rows=[['bar','Sample'],['baz','Sample'],['qux','Sample'],['spare','Untouched']].map(([id,name])=>({fields:[{module:'sales',field:'product-id',value:id!},{module:'sales',field:'product-name',value:name!}]}));
        self.postMessage(await current.store.recoverLoad(current.owner,{target,rows,request:{requestKey:'initial-products',attempt:'load-1'}}));
      }else if(event.data.command==='inspectStorage'){
        // Read-only physical evidence after the public owner releases its lock.
        await navigator.locks.request('truss-browser:lifecycle-basic',async()=>{
          const db=new PGlite('idb://truss-browser:lifecycle-basic',{relaxedDurability:false});
          try{self.postMessage((await db.query(`SELECT (SELECT count(*)::text FROM truss.object) AS objects,(SELECT count(*)::text FROM truss.object_key_bucket) AS keys,(SELECT count(*)::text FROM truss.object_key_reservation_bucket) AS reservations,(SELECT count(*)::text FROM truss.journal) AS journal,(SELECT min(generation)::text FROM truss.key_bucket_guard) AS generation,(SELECT bool_and(new_value->>'interfaceVersion'='truss-browser-journal-exact-bytes/0.1' AND new_value->>'bytesSha256'=encode(sha256(decode(new_value->>'bytesBase64','base64')),'hex') AND origin->>'interfaceVersion'='truss-browser-journal-exact-bytes/0.1') FROM truss.journal) AS exact`)).rows[0]);}finally{await db.close();}
        });
      }else if(event.data.command==='batchFault'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const id=event.data.id;if(typeof id!=='string'||!/^[1-9][0-9]{0,18}$/.test(id))throw Error('Exact fixture identity required');
        const info=current.store.info(current.owner);await current.store.close(current.owner);
        // Test-only fault injection; all business objects still use public loading.
        await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          try{
            if(event.data.remove)await db.exec('DROP TRIGGER test_batch_fault ON truss.object; DROP FUNCTION truss.test_batch_fault()');
            else await db.exec(`CREATE FUNCTION truss.test_batch_fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF OLD.id=${id}::bigint THEN RAISE EXCEPTION 'test second-item update failure'; END IF; RETURN NEW; END $$; CREATE TRIGGER test_batch_fault BEFORE UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION truss.test_batch_fault()`);
            await db.syncToFs();
          }finally{await db.close();}
        });
        current=await openBrowserStore({name:'lifecycle-basic',layoutSql:await(await fetch(new URL('layout.sql',import.meta.url))).text()});
        self.postMessage({outcome:event.data.remove?'fault_removed':'fault_installed'});
      }else if(event.data.command==='materialize'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        materialized=await current.store.materialize(current.owner,registeredAction,readGrant,{sql:event.data.sql??"UPDATE products SET name='Bulk' WHERE name='Sample'",parameters:{},batchSize:2,maxItems:10});
        self.postMessage({outcome:'materialized',plan:materialized.plan,manifest:materialized.manifest,count:materialized.count,batches:materialized.batches});
      }else if(event.data.command==='forgedGrant'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        try{await current.store.materialize(current.owner,registeredAction,{} as any,{sql:"UPDATE products SET name='Bulk' WHERE name='Sample'",parameters:{},batchSize:2,maxItems:10});throw Error('Forged grant admitted');}
        catch(error){if(String(error).includes('Forged grant admitted'))throw error;}
        self.postMessage({outcome:'refused'});
      }else if(event.data.command==='seal'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        self.postMessage(await current.store.seal(current.owner,registeredAction,readGrant,materialized.work,event.data.request));
      }else if(event.data.command==='recoverSeal'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        self.postMessage(await current.store.recoverSeal(current.owner,registeredAction,readGrant,event.data.reference));
      }else if(event.data.command==='submit'||event.data.command==='recoverSubmit'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const method=event.data.command==='submit'?current.store.submit:current.store.recoverSubmit;
        self.postMessage(await method(current.owner,registeredAction,readGrant,event.data.input));
      }else if(event.data.command==='executeBatch'||event.data.command==='recoverBatch'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const method=event.data.command==='executeBatch'?current.store.executeBatch:current.store.recoverBatch;
        self.postMessage(await method(current.owner,registeredAction,readGrant,event.data.input));
      }else if(event.data.command==='readFeed'){
        if(current?.outcome!=='available')throw Error('Available store required');
        self.postMessage(await current.store.readFeed(current.owner,event.data.input));
      }else if(event.data.command==='readObjects'){
        if(current?.outcome!=='available')throw Error('Available store required');
        self.postMessage(await current.store.readObjects(current.owner,{documentId:'product-local-action-demo',module:'sales',record:'products'}));
      }else if(event.data.command==='cancel'||event.data.command==='recoverCancel'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const method=event.data.command==='cancel'?current.store.cancel:current.store.recoverCancel;
        self.postMessage(await method(current.owner,registeredAction,readGrant,event.data.input));
      }else if(event.data.command==='claim'||event.data.command==='recoverClaim'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const method=event.data.command==='claim'?current.store.claim:current.store.recoverClaim;
        self.postMessage(await method(current.owner,registeredAction,readGrant,event.data.input));
      }else if(event.data.command==='reviewJob'){
        if(current?.outcome!=='available')throw Error('Available store required');
        self.postMessage(await current.store.reviewJob(current.owner,registeredAction,readGrant,event.data.job));
      }else if(event.data.command==='catalog'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        self.postMessage({outcome:'catalog',catalog:await current.store.catalog(current.owner)});
      }else throw Error('Unknown test command');
    }catch(error){self.postMessage({outcome:'error',message:String(error)});}
  });
};
