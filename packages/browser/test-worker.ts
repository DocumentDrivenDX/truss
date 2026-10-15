import {openBrowserStore,type StoreOpen} from './store';
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
      }else if(event.data.command==='catalog'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        self.postMessage({outcome:'catalog',catalog:await current.store.catalog(current.owner)});
      }else throw Error('Unknown test command');
    }catch(error){self.postMessage({outcome:'error',message:String(error)});}
  });
};
