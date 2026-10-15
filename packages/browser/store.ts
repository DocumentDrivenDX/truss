import {createBulk,captureSubmit,captureJob,type SubmitInput,type SubmitResult,type JobRef,type JobState,type JobReview} from './bulk';
import {createObjectAccess,captureLoad,captureTarget,journalHorizon,type LoadInput,type LoadOutcome,type RecordIdentity} from './objects';
import {PGlite} from '@electric-sql/pglite';
import {createMaterializer,createSealer,captureSeal,captureSealReference,captureMaterialize,type MaterializeInput,type Materialization,type FrozenWork,type SealRequest,type SealReference,type SealOutcome} from './materialize';
import {createActionIssuer,captureAction,type ActionIdentity,type LocalAction,type BrowserActionRegistration,type SelectionReadRegistration} from './actions';
import {captureDocument,prepareDocument,registerCatalog,readCatalog,type DocumentInput,type CatalogSnapshot,type Registration} from './catalog';

const LAYOUT='c203d09418fb4eddda829d791dda11c20341227c2d1d82e86d4c24afda5e7294';
const PROFILE='truss-browser-layout/0.1';
declare const ownerBrand:unique symbol;
export interface LocalOwner {readonly [ownerBrand]:true}
export interface StoreInfo {
  readonly profile:typeof PROFILE;readonly namespace:string;readonly origin:string;
  readonly storeId:string;readonly incarnation:string;readonly layoutSha256:string;
}
export interface BrowserStore {
  info(owner:LocalOwner):StoreInfo;
  registerDocument(owner:LocalOwner,input:DocumentInput):Promise<Registration>;
  catalog(owner:LocalOwner):Promise<CatalogSnapshot|null>;
  registerAction(owner:LocalOwner,input:ActionIdentity):Promise<BrowserActionRegistration>;
  grantSelectionRead(owner:LocalOwner,action:LocalAction):Promise<SelectionReadRegistration>;
  materialize(owner:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:MaterializeInput):Promise<Materialization>;
  seal(owner:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,work:FrozenWork,input:SealRequest):Promise<SealOutcome>;
  recoverSeal(owner:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,reference:SealReference):Promise<SealOutcome>;
  loadObjects(owner:LocalOwner,input:LoadInput):Promise<LoadOutcome>;
  recoverLoad(owner:LocalOwner,input:LoadInput):Promise<LoadOutcome>;
  readObjects(owner:LocalOwner,target:RecordIdentity):Promise<{id:string;typeId:string;version:string;fields:{module:string;field:string;value:string}[]}[]>;
  submit(owner:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:SubmitInput):Promise<SubmitResult>;
  recoverSubmit(owner:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:SubmitInput):Promise<SubmitResult>;
  reviewJob(owner:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,job:JobRef):Promise<JobReview>;
  close(owner:LocalOwner):Promise<void>;
}
export type StoreOpen={outcome:'available';store:BrowserStore;owner:LocalOwner}|{outcome:'unavailable';reason:'store_in_use'};

/** Worker-local capability. No SQL connection or action/read authority is exported. */
export async function openBrowserStore(input:{name:string;layoutSql:string}):Promise<StoreOpen>{
  const WorkerScope=(globalThis as any).WorkerGlobalScope;
  if(!WorkerScope||!(globalThis instanceof WorkerScope)||!navigator.locks||!globalThis.indexedDB)
    throw new Error('Browser worker, Web Locks and IndexedDB required');
  if(!input)throw new Error('Original store input required');
  const name=input.name,layoutSql=input.layoutSql;
  if(typeof name!=='string'||!/^[a-z0-9][a-z0-9-]{0,63}$/.test(name)
    ||typeof layoutSql!=='string'||layoutSql.length>1048576)
    throw new Error('Bounded canonical store name and original layout required');
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(layoutSql))))
    .map(x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==LAYOUT)throw new Error('Original generated Truss layout required');
  const namespace='truss-browser:'+name,origin=location.origin;
  let release!:()=>void;
  const held=new Promise<void>(resolve=>{release=resolve;});
  let ready!:(result:StoreOpen)=>void,fail!:(error:unknown)=>void;
  const opening=new Promise<StoreOpen>((resolve,reject)=>{ready=resolve;fail=reject;});
  const lockTask:Promise<void>=navigator.locks.request(namespace,{mode:'exclusive',ifAvailable:true},async lock=>{
    if(!lock){ready({outcome:'unavailable',reason:'store_in_use'});return;}
    let db:PGlite|undefined;
    try{
      db=new PGlite('idb://'+namespace,{relaxedDurability:false});
      const actual=db;
      const version=(await actual.query<{n:string;version:string}>('SELECT current_setting(\'server_version_num\') AS n,version()')).rows[0];
      if(version?.n!=='180006'||!version.version.includes('PGlite 0.5.10'))throw new Error('PGlite0.5.10/PostgreSQL18.6 required');
      const exists=(await actual.query<{present:boolean}>("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='truss') AS present")).rows[0]!.present;
      if(!exists){
        await actual.transaction(async tx=>{
          await tx.exec(layoutSql);
          const marker:StoreInfo={profile:PROFILE,namespace,origin,storeId:crypto.randomUUID(),incarnation:crypto.randomUUID(),layoutSha256:LAYOUT};
          await tx.query("INSERT INTO truss.setting(key,value) VALUES('browser_store_marker',$1::jsonb)",[JSON.stringify(marker)]);
        });
        await actual.syncToFs();
      }
      const rows=(await actual.query<{value:StoreInfo}>("SELECT value FROM truss.setting WHERE key='browser_store_marker'")).rows;
      const marker=rows[0]?.value;
      const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      if(rows.length!==1||!marker||Object.keys(marker).sort().join(',')!=='incarnation,layoutSha256,namespace,origin,profile,storeId'
        ||marker.profile!==PROFILE||marker.namespace!==namespace||marker.origin!==origin||marker.layoutSha256!==LAYOUT
        ||typeof marker.storeId!=='string'||typeof marker.incarnation!=='string'
        ||!uuid.test(marker.storeId)||!uuid.test(marker.incarnation))
        throw new Error('Original store incarnation marker required; no automatic reset');
      await journalHorizon(actual,false);
      const tables=(await actual.query<{n:string}>("SELECT count(*)::text AS n FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p') AND NOT c.relispartition")).rows[0];
      const head=(await actual.query<{rev:number}>('SELECT rev FROM truss.schema_head WHERE id=1')).rows;
      if(tables?.n!=='48'||head.length!==1||!Number.isSafeInteger(head[0]!.rev)||head[0]!.rev<0)
        throw new Error('Complete original layout inventory required');
      const info=Object.freeze({...marker});
      await actual.syncToFs();
      const owner=Object.freeze(Object.create(null)) as LocalOwner;
      let state:'open'|'closing'|'closed'|'fenced'='open';
      const issuer=createActionIssuer(info,()=>state==='open');
      const materializer=createMaterializer(actual,info,issuer,()=>state==='open',()=>{state='fenced';});
      const sealer=createSealer(actual,info,issuer,materializer,()=>state==='open',()=>{state='fenced';});
      const bulk=createBulk(actual,info,sealer,()=>state==='open',()=>{state='fenced';});
      const objectAccess=createObjectAccess(actual,info,()=>state==='open',()=>{state='fenced';});
      const currentCatalog=()=>readCatalog(actual).catch(error=>{state='fenced';throw error;});
      const check=(cap:LocalOwner)=>{if(cap!==owner||state!=='open')throw new Error('Current issued local owner required');};
      let queue:Promise<void>=Promise.resolve();
      const schedule=<T>(cap:LocalOwner,operation:()=>Promise<T>):Promise<T>=>{
        check(cap);
        const task=queue.then(()=>{if(state==='fenced'||state==='closed')throw Error('Store is fenced or closed');return operation();});
        queue=task.then(()=>{},()=>{});return task;
      };
      const store:BrowserStore=Object.freeze({
        info(cap:LocalOwner){check(cap);return info;},
        registerDocument(cap:LocalOwner,input:DocumentInput){
          check(cap);const captured=captureDocument(input);
          return schedule(cap,async()=>{
            const prepared=await prepareDocument(captured);
            try{const result=await registerCatalog(actual,prepared);await actual.syncToFs();return result;}
            catch(error){state='fenced';throw error;}
          });
        },
        catalog(cap:LocalOwner){return schedule(cap,async()=>{
          try{return await readCatalog(actual);}catch(error){state='fenced';throw error;}
        });},
        registerAction(cap:LocalOwner,input:ActionIdentity){
          check(cap);const captured=captureAction(input);
          return schedule(cap,async()=>issuer.register(await currentCatalog(),captured));
        },
        grantSelectionRead(cap:LocalOwner,action:LocalAction){
          return schedule(cap,async()=>issuer.grant(await currentCatalog(),action));
        },
        materialize(cap:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:MaterializeInput){
          check(cap);const captured=captureMaterialize(input);
          return schedule(cap,()=>materializer.materialize(action,grant,captured));
        },
        seal(cap:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,work:FrozenWork,input:SealRequest){
          check(cap);const captured=captureSeal(input);return schedule(cap,()=>sealer.seal(action,grant,work,captured));
        },
        recoverSeal(cap:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:SealReference){
          check(cap);const captured=captureSealReference(input);return schedule(cap,()=>sealer.recover(action,grant,captured));
        },
        loadObjects(cap:LocalOwner,input:LoadInput){check(cap);const captured=captureLoad(input);return schedule(cap,()=>objectAccess.load(captured));},
        recoverLoad(cap:LocalOwner,input:LoadInput){check(cap);const captured=captureLoad(input);return schedule(cap,()=>objectAccess.load(captured,true));},
        readObjects(cap:LocalOwner,input:RecordIdentity){check(cap);const captured=captureTarget(input);return schedule(cap,()=>objectAccess.read(captured));},
        submit(cap:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:SubmitInput){check(cap);const captured=captureSubmit(input);return schedule(cap,()=>bulk.submit(action,grant,captured));},
        recoverSubmit(cap:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:SubmitInput){check(cap);const captured=captureSubmit(input);return schedule(cap,()=>bulk.submit(action,grant,captured,true));},
        reviewJob(cap:LocalOwner,action:LocalAction,grant:import('./actions').SelectionReadGrant,input:JobRef){check(cap);const captured=captureJob(input);return schedule(cap,()=>bulk.status(action,grant,captured));},
        async close(cap:LocalOwner){
          check(cap);state='closing';
          try{await queue;if((state as string)==='fenced')throw Error('Store is fenced');await actual.syncToFs();await actual.close();release();await lockTask;state='closed';}
          catch(error){state='fenced';throw error;}
        }
      });
      ready({outcome:'available',store,owner});
      await held;
    }catch(error){
      fail(error);
      // PGlite close may hide shutdown errors. An initialization/flush failure
      // fences this worker; do not release its lock on an inferred cleanup.
      // The caller sees rejection immediately and can terminate the worker.
      if(db)await held;
    }
  });
  void lockTask.catch(fail);
  return opening;
}
