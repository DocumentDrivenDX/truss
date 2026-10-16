import {KEY_RECEIPT_ENCODING,compactKeyReceipts,sealIntentUtf8} from './key-receipt-storage';
import {openBrowserStore,type StoreOpen} from './store';
import {PGlite} from '@electric-sql/pglite';
import {createFrozenBatchApplier} from './batch';
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
      }else if(event.data.command==='previousStore'){
        const previous=await import(new URL('previous/store.js',import.meta.url).href),name='previous-preserved';
        const oldLayout=await(await fetch(new URL('previous/layout.sql',import.meta.url))).text();
        let old=await previous.openBrowserStore({name,layoutSql:oldLayout});if(old.outcome!=='available')throw Error('Previous provider unavailable');
        const sourceUtf8=await(await fetch(new URL('model.json',import.meta.url))).text();
        const document={documentId:'product-local-action-demo',documentRevision:'b8ce3cfe76eeda7c1531b2bbf8aba121c9d9614800ff1f3301f853c048516f27',sourceUtf8};
        if((await old.store.registerDocument(old.owner,document)).outcome!=='registered')throw Error('Previous catalog unavailable');
        const target={documentId:document.documentId,module:'sales',record:'products'},input={target,rows:[{fields:[{module:'sales',field:'product-id',value:'legacy'},{module:'sales',field:'product-name',value:'Keep'}]}],request:{requestKey:'previous-load',attempt:'previous-1'}};
        if((await old.store.loadObjects(old.owner,input)).outcome!=='loaded')throw Error('Previous data unavailable');
        const before=await old.store.readObjects(old.owner,target),info=old.store.info(old.owner);if(info.profile!=='truss-browser-layout/0.1')throw Error('Previous profile required');
        await old.store.close(old.owner);
        let refused=false;try{const next=await openBrowserStore({name,layoutSql:await(await fetch(new URL('layout.sql',import.meta.url))).text()});if(next.outcome==='available')await next.store.close(next.owner);}
        catch(error){if(!String(error).includes('Original store incarnation marker required'))throw error;refused=true;}
        if(!refused)throw Error('Previous store silently adopted');
        self.postMessage({outcome:'previous_store_refused',info,before});
      }else if(event.data.command==='recoverPreviousStore'){
        const previous=await import(new URL('previous/store.js',import.meta.url).href),name='previous-preserved';
        const old=await previous.openBrowserStore({name,layoutSql:await(await fetch(new URL('previous/layout.sql',import.meta.url))).text()});if(old.outcome!=='available')throw Error('Previous store cannot reopen');
        const target={documentId:'product-local-action-demo',module:'sales',record:'products'},expected=event.data.expected;
        if(JSON.stringify(await old.store.readObjects(old.owner,target))!==JSON.stringify(expected.before)||JSON.stringify(old.store.info(old.owner))!==JSON.stringify(expected.info))throw Error('Previous store changed');
        await old.store.close(old.owner);self.postMessage({outcome:'previous_store_preserved'});
      }else if(event.data.command==='forgedPage'||event.data.command==='closedPage'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const forged=event.data.command==='forgedPage',owner=forged?{} as any:current.owner;
        try{await current.store.readObjectPage(owner,{target:{documentId:'product-local-action-demo',module:'sales',record:'products'},limit:1,afterId:null});throw Error('Invalid page owner admitted');}
        catch(error){if(String(error).includes('Invalid page owner admitted'))throw error;}
        self.postMessage({outcome:'refused'});
      }else if(event.data.command==='pageObjects'){
        if(current?.outcome!=='available')throw Error('Available store required');
        self.postMessage(await current.store.readObjectPage(current.owner,{target:{documentId:'product-local-action-demo',module:'sales',record:'products'},limit:event.data.limit,afterId:event.data.afterId}));
      }else if(event.data.command==='seedBulk'){
        if(current?.outcome!=='available')throw Error('Available store required');
        const count=event.data.count;if(!Number.isInteger(count)||count<1||count>1024)throw Error('Bounded fixture count required');
        const ids:string[]=[],started=performance.now();
        for(let start=0;start<count;start+=100){
          const rows=Array.from({length:Math.min(100,count-start)},(_,i)=>({fields:[{module:'sales',field:'product-id',value:start+i===0&&event.data.firstKey==='bar'?'bar':'p'+String(start+i).padStart(4,'0')},{module:'sales',field:'product-name',value:'Sample'}]}));
          const input={target:{documentId:'product-local-action-demo',module:'sales',record:'products'},rows,request:{requestKey:'bulk-load-'+start,attempt:'bulk-seed-'+start}};
          const loaded=await current.store.loadObjects(current.owner,input);if(loaded.outcome!=='loaded')throw Error(JSON.stringify(loaded));
          ids.push(...loaded.objects.map(o=>o.id));
          if(start===0&&JSON.stringify(await current.store.loadObjects(current.owner,input))!==JSON.stringify(loaded))throw Error('Bulk seed load replay changed');
        }
        self.postMessage({outcome:'bulk_loaded',ids,elapsedMs:performance.now()-started});
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
      }else if(event.data.command==='jobCustodyFault'){
        const info=event.data.info,job=event.data.job;
        const original=await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          try{
            const key='browser:bulk-job:0.1:'+job.namespace+':'+job.id,record=(await db.query<any>('SELECT value FROM truss.setting WHERE key=$1',[key])).rows[0].value;
            const altered=event.data.restore??structuredClone(record);
            if(!event.data.restore){
              if(record.profile!=='truss-browser-bulk-job/0.2')throw Error('Compact original job required');
              if(event.data.mode==='missingSeal')altered.reference.requestKey='absent-custody-'+job.id;
              else if(event.data.mode==='sourceDigest')altered.sourceSha256=(record.sourceSha256[0]==='0'?'1':'0')+record.sourceSha256.slice(1);
              else throw Error('Unknown custody fault');
            }
            await db.query('UPDATE truss.setting SET value=$2::jsonb WHERE key=$1',[key,JSON.stringify(altered)]);await db.syncToFs();return record;
          }finally{await db.close();}
        });
        self.postMessage({outcome:'custody_fault_written',original});
      }else if(event.data.command==='compactSealFixture'){
        // Test-only transport fixture: preserve an actual old provider's source,
        // replacing only its private encoding/control. This does not issue authority.
        const info=event.data.info;let reference:any;
        await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          const hash=async(text:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),b=>b.toString(16).padStart(2,'0')).join('');
          const key=(request:string)=>'browser:seal:0.1:'+Array.from(new TextEncoder().encode(request),b=>b.toString(16).padStart(2,'0')).join('');
          try{
            const stored=(await db.query<any>('SELECT value FROM truss.setting WHERE key=$1',[key(event.data.originalRequest)])).rows[0].value;
            const source=JSON.parse(stored.inputUtf8),outcome=JSON.parse(stored.outcomeUtf8);
            if(source.profile!=='truss-browser-seal/0.1')throw Error('Actual old full-source seal required');
            reference={...source.reference,requestKey:event.data.requestKey};
            const input={...source,profile:'truss-browser-seal/0.2',reference,keyReceipts:compactKeyReceipts(source.keyReceipts,JSON.parse(source.model.utf8)),keyReceiptEncoding:KEY_RECEIPT_ENCODING};
            const inputUtf8=JSON.stringify(input),inputSha256=await hash(inputUtf8);
            const receiptUtf8=JSON.stringify({...JSON.parse(outcome.receipt.utf8),reference,inputSha256});
            const outcomeUtf8=JSON.stringify({...outcome,reference,receipt:{...outcome.receipt,utf8:receiptUtf8,sha256:await hash(receiptUtf8)}});
            await db.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[key(event.data.requestKey),JSON.stringify({...stored,inputUtf8,inputSha256,outcomeUtf8,outcomeSha256:await hash(outcomeUtf8)})]);await db.syncToFs();
          }finally{await db.close();}
        });
        self.postMessage({outcome:'compact_transport_fixture',reference});
      }else if(event.data.command==='legacyJob'){
        const info=event.data.info,job=event.data.job;let profileBefore='';
        await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          try{
            const jobKey='browser:bulk-job:0.1:'+job.namespace+':'+job.id;
            const record=(await db.query<any>('SELECT value FROM truss.setting WHERE key=$1',[jobKey])).rows[0].value;
            profileBefore=record.profile;
            if(record.profile==='truss-browser-bulk-job/0.2'){
              if('sourceUtf8'in record||'intentUtf8'in record)throw Error('Compact job duplicated source');
              const sealKey='browser:seal:0.1:'+Array.from(new TextEncoder().encode(record.reference.requestKey),b=>b.toString(16).padStart(2,'0')).join('');
              const source=JSON.parse((await db.query<any>('SELECT value FROM truss.setting WHERE key=$1',[sealKey])).rows[0].value.inputUtf8);
              delete record.reference;delete record.intentEncoding;record.profile='truss-browser-bulk-job/0.1';record.sourceUtf8=JSON.stringify(source);record.intentUtf8=sealIntentUtf8(source,false);record.intentSha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(record.intentUtf8))),b=>b.toString(16).padStart(2,'0')).join('');
              await db.query('UPDATE truss.setting SET value=$2::jsonb WHERE key=$1',[jobKey,JSON.stringify(record)]);
            }
            const admissions=(await db.query<any>('SELECT key,value FROM truss.setting WHERE key LIKE $1',['browser:bulk-admission:0.1:'+job.namespace+':'+job.id+':%'])).rows;
            for(const row of admissions){if(row.value.profile==='truss-browser-effect-admission/0.2'){if('sourceUtf8'in row.value)throw Error('Compact admission duplicated source');row.value.profile='truss-browser-effect-admission/0.1';row.value.sourceUtf8=record.sourceUtf8;await db.query('UPDATE truss.setting SET value=$2::jsonb WHERE key=$1',[row.key,JSON.stringify(row.value)]);}}
            await db.syncToFs();
          }finally{await db.close();}
        });
        self.postMessage({outcome:'legacy_job_retained',profileBefore});
      }else if(event.data.command==='cacheBoundary'){
        const info=event.data.info,job=event.data.job;
        // Read the actual retained source after the public owner has closed.
        const sourceUtf8=await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          try{
            const record=(await db.query<any>('SELECT value FROM truss.setting WHERE key=$1',['browser:bulk-job:0.1:'+job.namespace+':'+job.id])).rows[0].value;
            if(record.profile==='truss-browser-bulk-job/0.1')return record.sourceUtf8 as string;
            const key='browser:seal:0.1:'+Array.from(new TextEncoder().encode(record.reference.requestKey),b=>b.toString(16).padStart(2,'0')).join('');
            return JSON.stringify(JSON.parse((await db.query<any>('SELECT value FROM truss.setting WHERE key=$1',[key])).rows[0].value.inputUtf8));
          }finally{await db.close();}
        });
        const apply=createFrozenBatchApplier(info),sentinel=new Error('fresh native catalog boundary');let reads=0;
        const tx={query:async()=>{reads++;throw sentinel;},exec:async()=>{throw Error('Unexpected native effect');}};
        async function reachesNative(){const before=reads;try{await apply(tx as any,sourceUtf8,job,1);throw Error('Native boundary not reached');}catch(error){if(error!==sentinel)throw error;}if(reads!==before+1)throw Error('Native catalog not read fresh');}
        await reachesNative();await reachesNative();
        const malformed=JSON.parse(sourceUtf8);malformed.preparation.utf8='{}';const invalid=JSON.stringify(malformed),before=reads;
        for(let i=0;i<2;i++){let refused=false;try{await apply(tx as any,invalid,job,1);}catch(error){if(error===sentinel)throw Error('Malformed source reused warm admission');refused=true;}if(!refused||reads!==before)throw Error('Malformed source reached native reads');}
        await reachesNative();
        self.postMessage({outcome:'cache_boundary_passed',freshNativeReads:reads,changedSourceRefusals:2,originalStillUsable:true,scope:'Pure admission boundary with throwing native sentinel; real effects covered separately'});
      }else if(event.data.command==='sealStorage'){
        const info=event.data.info;const seals:any[]=[];
        await navigator.locks.request(info.namespace,async()=>{
          const db=new PGlite('idb://'+info.namespace,{relaxedDurability:false});
          try{
            const records=(await db.query<any>("SELECT value FROM truss.setting WHERE key LIKE 'browser:seal:0.1:%'")).rows;
            for(const record of records){const source=JSON.parse(record.value.inputUtf8);
              const sourceCopies=source.keyReceipts.filter((receipt:any)=>Object.hasOwn(receipt,'source')).length;
              if(source.profile!=='truss-browser-seal/0.2'||source.keyReceiptEncoding!==KEY_RECEIPT_ENCODING||sourceCopies)throw Error('Seal duplicated per-item model source');
              seals.push({profile:source.profile,receipts:source.keyReceipts.length,perReceiptSourceCopies:sourceCopies,inputBytes:new TextEncoder().encode(record.value.inputUtf8).length});
            }
          }finally{await db.close();}
        });self.postMessage({outcome:'seal_storage',seals});
      }else if(event.data.command==='compactStorage'){
        const report=await navigator.locks.request(event.data.info.namespace,async()=>{
          const db=new PGlite('idb://'+event.data.info.namespace,{relaxedDurability:false});
          try{const rows=(await db.query<any>("SELECT value FROM truss.setting WHERE value->>'profile' IN ('truss-browser-bulk-job/0.2','truss-browser-effect-admission/0.2')")).rows;
            if(!rows.length||rows.some(row=>'sourceUtf8'in row.value||'intentUtf8'in row.value))throw Error('Normalized control storage duplicated complete source');
            return {outcome:'compact_storage',records:rows.length,completeSourceCopies:0};
          }finally{await db.close();}
        });
        self.postMessage(report);
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
            else if(event.data.corruptId){
              const corrupt=event.data.corruptId;if(typeof corrupt!=='string'||!/^[1-9][0-9]{0,18}$/.test(corrupt))throw Error('Exact corrupt identity required');
              await db.exec(`CREATE FUNCTION truss.test_batch_fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF OLD.id=${corrupt}::bigint THEN NEW.props=NEW.props||'{"testUnexpected":{"kind":"string","text":"fault"}}'::jsonb; END IF; IF OLD.id=${id}::bigint THEN RAISE EXCEPTION 'test later-item update failure'; END IF; RETURN NEW; END $$; CREATE TRIGGER test_batch_fault BEFORE UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION truss.test_batch_fault()`);
            }
            else if(event.data.laterId){
              const later=event.data.laterId;if(typeof later!=='string'||!/^[1-9][0-9]{0,18}$/.test(later))throw Error('Exact later identity required');
              await db.exec(`CREATE FUNCTION truss.test_batch_fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF OLD.id=${id}::bigint THEN UPDATE truss.object SET ver=ver+1 WHERE id=${later}::bigint; END IF; RETURN NEW; END $$; CREATE TRIGGER test_batch_fault BEFORE UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION truss.test_batch_fault()`);
            }else await db.exec(`CREATE FUNCTION truss.test_batch_fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF OLD.id=${id}::bigint THEN RAISE EXCEPTION 'test second-item update failure'; END IF; RETURN NEW; END $$; CREATE TRIGGER test_batch_fault BEFORE UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION truss.test_batch_fault()`);
            await db.syncToFs();
          }finally{await db.close();}
        });
        current=await openBrowserStore({name:'lifecycle-basic',layoutSql:await(await fetch(new URL('layout.sql',import.meta.url))).text()});
        self.postMessage({outcome:event.data.remove?'fault_removed':'fault_installed'});
      }else if(event.data.command==='materialize'){
        if(current?.outcome!=='available')throw Error('Available test store required');
        materialized=await current.store.materialize(current.owner,registeredAction,readGrant,{sql:event.data.sql??"UPDATE products SET name='Bulk' WHERE name='Sample'",parameters:{},batchSize:event.data.batchSize??2,maxItems:event.data.maxItems??10});
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
      }else if(event.data.command==='invalidExecution'){
        if(current?.outcome!=='available')throw Error('Available store required');
        self.postMessage(await current.store.executeBatch(current.owner,registeredAction,{} as any,event.data.input));
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
