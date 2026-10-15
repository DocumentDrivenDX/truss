import {openBrowserStore,type StoreOpen} from './store';
declare const self:DedicatedWorkerGlobalScope;
let current:StoreOpen|undefined;
let pending=Promise.resolve();
self.onmessage=event=>{
  pending=pending.then(async()=>{
    try{
      if(event.data.command==='open'){
        current=await openBrowserStore({name:event.data.name,layoutSql:await(await fetch('/layout.sql')).text()});
        self.postMessage(current.outcome==='available'?{outcome:'available',info:current.store.info(current.owner)}:current);
      }else if(event.data.command==='forged'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        try{current.store.info({} as any);throw Error('Forged owner admitted');}
        catch(error){if(String(error).includes('Forged owner admitted'))throw error;}
        self.postMessage({outcome:'refused'});
      }else if(event.data.command==='close'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        await current.store.close(current.owner);self.postMessage({outcome:'closed'});
      }else throw Error('Unknown test command');
    }catch(error){self.postMessage({outcome:'error',message:String(error)});}
  });
};
