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
        if(current?.outcome!=='available')throw Error('Available test store required');
        const info=current.store.info(current.owner),name=event.data.name;
        await current.store.close(current.owner);
        // Test-only administrative fixture setup; this is not a provider mutation API.
        await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          try{await db.transaction(async tx=>{
            const type=(await tx.query<{type_id:number}>('SELECT type_id FROM truss.type_def')).rows[0]!.type_id;
            const props=(await tx.query<{prop_id:number;name:string}>('SELECT prop_id,name FROM truss.prop_def ORDER BY prop_id')).rows;
            for(const [id,name] of [['bar','Sample'],['baz','Sample'],['qux','Sample'],['spare','Untouched']]){
              const values=Object.fromEntries(props.map(p=>[p.prop_id,{kind:'string',text:p.name==='id'?id:name}]));
              await tx.query('INSERT INTO truss.object(type_id,props,rev) VALUES($1,$2::jsonb,1)',[type,JSON.stringify(values)]);
            }
          });await db.syncToFs();}finally{await db.close();}
        });
        current=await openBrowserStore({name,layoutSql:await(await fetch(new URL('layout.sql',import.meta.url))).text()});
        self.postMessage({outcome:'test_fixture_seeded'});
      }else if(event.data.command==='materialize'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        materialized=await current.store.materialize(current.owner,registeredAction,readGrant,{sql:"UPDATE products SET name='Bulk' WHERE name='Sample'",parameters:{},batchSize:2,maxItems:10});
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
      }else if(event.data.command==='catalog'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        self.postMessage({outcome:'catalog',catalog:await current.store.catalog(current.owner)});
      }else throw Error('Unknown test command');
    }catch(error){self.postMessage({outcome:'error',message:String(error)});}
  });
};
