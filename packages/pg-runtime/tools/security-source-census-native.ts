// SPDX-License-Identifier: MIT OR Apache-2.0
/** Installer-only native original-response census witness; credentials enter through private stdin. */
import {Client} from 'pg';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,statSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {captureSourceCensus} from '../src/security-source-census';
import {createFileQueryJournal,inspectOriginalQueryFile} from '../src/journal';
const stdin:Buffer[]=[];for await(const chunk of process.stdin)stdin.push(Buffer.from(chunk));
const input=JSON.parse(Buffer.concat(stdin).toString('utf8')),observations:unknown[]=[];
const sha=(s:string|Buffer)=>createHash('sha256').update(s).digest('hex');
const check=(id:string,expected:unknown,observed:unknown)=>{
 observations.push({id,expected,observed});if(JSON.stringify(expected)!==JSON.stringify(observed))throw Error(id);
};
const sql=readFileSync(input.source,'utf8');
const client=new Client({host:'127.0.0.1',port:input.port,user:'postgres',password:input.password,database:'postgres',connectionTimeoutMillis:5000,types:{getTypeParser:()=> (s:string)=>s}});
const capture=async(label:string)=>{
 const path=join(input.evidence,label);mkdirSync(path,{mode:0o700});
 const result=await captureSourceCensus(client as any,sql,createFileQueryJournal(path));
 writeFileSync(join(input.evidence,label+'.image.json'),result.originalText,{mode:0o600});
 const parsed=JSON.parse(result.originalText);
 check(label+':native-version','truss.security.query-source-census/0.1.0',parsed.version);
 check(label+':native-engine','170009',parsed.serverVersion);
 check(label+':complete-40-sections',40,Object.keys(parsed.sections).length);
 const files=readdirSync(path).sort(),receipts=files.map(file=>{
  const full=join(path,file),x=inspectOriginalQueryFile(full,{maxBytes:16777216});
  if(x.state!=='complete'||x.outcome!=='response_complete')throw Error('Incomplete original journal');
  return {path:join(label,file),bytes:statSync(full).size,sha256:sha(readFileSync(full)),ordinal:x.request!.custody.ordinal,lease:x.request!.custody.lease};
 });
 check(label+':every-response-journaled',result.responses,receipts.length);
 check(label+':contiguous-local-custody',Array.from({length:result.responses},(_,i)=>String(i)),receipts.map(r=>r.ordinal).sort((a,b)=>Number(a)-Number(b)));
 check(label+':one-local-lease',1,new Set(receipts.map(r=>r.lease)).size);
 check(label+':no-native-cursor-after-completion',[['0']],(await client.query({text:"SELECT count(*)::text FROM pg_cursors WHERE name LIKE 'truss_census_%'",rowMode:'array'})).rows);
 return {originalText:result.originalText,summary:{label,sha256:sha(result.originalText),imageBytes:Buffer.byteLength(result.originalText),wireBytes:result.wireBytes,responses:result.responses,chunks:result.chunks,journals:receipts}};
};
const failedCapture=async(label:string)=>{
 const path=join(input.evidence,label);mkdirSync(path,{mode:0o700});let result:unknown;
 try{result=await captureSourceCensus(client as any,sql,createFileQueryJournal(path));}catch{result='refused';}
 check(label+':no-accepted-prefix','refused',result);
 const outcomes=readdirSync(path).map(file=>inspectOriginalQueryFile(join(path,file),{maxBytes:16777216}));
 check(label+':rollback-original-complete',true,outcomes.some(x=>x.state==='complete'&&x.request?.text==='ROLLBACK'));
 check(label+':connection-usable',[['1']],(await client.query({text:'SELECT 1::text',rowMode:'array'})).rows);
 check(label+':cursor-cleaned',[['0']],(await client.query({text:"SELECT count(*)::text FROM pg_cursors WHERE name LIKE 'truss_census_%'",rowMode:'array'})).rows);
};
try{
 await client.connect();
 await client.query("CREATE SCHEMA census_probe; CREATE TABLE census_probe.facts(value text); INSERT INTO census_probe.facts VALUES ('original'); CREATE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 1::bigint';");
 const unicode='A'.repeat(32767)+'🙂é'+'B'.repeat(1000000);
 await client.query({text:'CREATE FUNCTION census_probe.unicode() RETURNS text LANGUAGE sql AS $body$ SELECT '+"'"+unicode+"'::text"+' $body$;'});
 const baseline=await capture('baseline');
 check('baseline:larger-than-one-original-response',true,baseline.summary.imageBytes>4194304);
 check('baseline:exact-original-UTF8-source',true,baseline.originalText.includes(unicode));
 await client.query("UPDATE census_probe.facts SET value='changed';");
 const data=await capture('data-update');check('faithful-data-update:same-source',baseline.summary.sha256,data.summary.sha256);
 await client.query("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 333::bigint';");
 const changed=await capture('source-change');check('same-descriptor-source-change:detected',true,changed.summary.sha256!==baseline.summary.sha256);
 await client.query("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 1::bigint';");
 const restored=await capture('restored');check('source-restoration:exact-image',baseline.summary.sha256,restored.summary.sha256);
 await client.query('CREATE FOREIGN DATA WRAPPER census_unqualified NO HANDLER;');await failedCapture('foreign-refusal');await client.query('DROP FOREIGN DATA WRAPPER census_unqualified;');
 await client.query('CREATE FUNCTION census_probe.overflow() RETURNS text LANGUAGE sql AS $body$ SELECT '+"'"+'Z'.repeat(17000000)+"'::text"+' $body$;');
 await failedCapture('overflow-refusal');await client.query('DROP FUNCTION census_probe.overflow();');
 const final=await capture('final-restoration');check('overflow-restoration:exact-image',baseline.summary.sha256,final.summary.sha256);
 // A caller-owned transaction is refused without rolling back its work/cursor.
 await client.query("BEGIN; INSERT INTO census_probe.facts VALUES ('caller-pending'); DECLARE caller_sentinel CURSOR FOR SELECT value FROM census_probe.facts ORDER BY value;");
 const path=join(input.evidence,'caller-transaction-refusal');mkdirSync(path,{mode:0o700});let result='unexpected';
 try{await captureSourceCensus(client as any,sql,createFileQueryJournal(path));}catch{result='refused';}
 check('caller-transaction:refusal','refused',result);
 check('caller-transaction:no-rollback-journal',false,readdirSync(path).some(file=>inspectOriginalQueryFile(join(path,file),{maxBytes:16777216}).request?.text==='ROLLBACK'));
 check('caller-transaction:uncommitted-work-preserved',[['1']],(await client.query({text:"SELECT count(*)::text FROM census_probe.facts WHERE value='caller-pending'",rowMode:'array'})).rows);
 check('caller-transaction:cursor-preserved',[['1']],(await client.query({text:"SELECT count(*)::text FROM pg_cursors WHERE name='caller_sentinel'",rowMode:'array'})).rows);
 check('caller-transaction:original-cursor-result',[['caller-pending'],['changed']],(await client.query({text:'FETCH ALL FROM caller_sentinel',rowMode:'array'})).rows);
 await client.query('ROLLBACK');
 check('caller-transaction:own-rollback-effects',[['0']],(await client.query({text:"SELECT count(*)::text FROM census_probe.facts WHERE value='caller-pending'",rowMode:'array'})).rows);
 check('caller-transaction:own-rollback-cursor-cleaned',[['0']],(await client.query({text:"SELECT count(*)::text FROM pg_cursors WHERE name='caller_sentinel'",rowMode:'array'})).rows);
 // Fail only after the complete original COMMIT response has been journaled.
 // No assembled image may escape a lost local completion boundary.
 const late=new Client({host:'127.0.0.1',port:input.port,user:'postgres',password:input.password,database:'postgres',connectionTimeoutMillis:5000,types:{getTypeParser:()=> (s:string)=>s}});
 late.on('error',()=>{});await late.connect();
 const latePath=join(input.evidence,'late-journal-refusal');mkdirSync(latePath,{mode:0o700});const baseJournal=createFileQueryJournal(latePath);
 let lateResult:unknown;
 try{
  await captureSourceCensus(late as any,sql,{begin(text,values,custody){
   const entry=baseJournal.begin(text,values,custody);
   return {frame:entry.frame,finish(outcome){entry.finish(outcome);if(text==='COMMIT')throw Error('Injected final journal completion loss');}};
  }});lateResult='unexpected image';
 }catch{lateResult='refused';}
 check('late-journal:no-image-release','refused',lateResult);
 check('late-journal:transport-discarded',true,(late as any).connection.stream.destroyed);
 check('late-journal:original-commit-retained',true,readdirSync(latePath).some(file=>{
  const receipt=inspectOriginalQueryFile(join(latePath,file),{maxBytes:16777216});return receipt.request?.text==='COMMIT'&&receipt.state==='complete'&&receipt.outcome==='response_complete';
 }));
 await late.end();
 writeFileSync(join(input.evidence,'native.json'),JSON.stringify({status:'component-passed',observations,captures:[baseline,data,changed,restored,final].map(x=>x.summary),scope:'Excluded installer on PostgreSQL17.9, pg8.16.3, Bun original pre-parser response journals. Complete private census transport only; no Python16.15 port, authenticated issuer/provider/expected source, graph profile, held authority cut, concurrent DDL/writer protocol or protected final disclosure.'},null,2)+'\n',{mode:0o600});
 console.log(JSON.stringify({status:'component-passed',observations:observations.length}));
}catch(error){writeFileSync(join(input.evidence,'native-failure.json'),JSON.stringify({status:'failed',observations,error:String(error)},null,2)+'\n',{mode:0o600});throw error;}
finally{await client.end();}
