import {test,expect} from 'bun:test';
import {mkdtempSync,chmodSync,readdirSync,readFileSync,statSync,rmSync,writeFileSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createFileQueryJournal,inspectOriginalQueryFile} from '../packages/pg-runtime/src/journal';
test('retains exact request, original frame and outcome across journal reconstruction',()=>{
 const directory=mkdtempSync(join(tmpdir(),'truss-journal-'));
 try{
  chmodSync(directory,0o700);const journal=createFileQueryJournal(directory);
  const custody={lease:'11111111-1111-4111-8111-111111111111',ordinal:'9007199254740993123456789'};
  const attempt=journal.begin('SELECT $1',['9007199254740993',null,''],custody);
  expect(readdirSync(directory).length).toBe(1);
  expect(()=>journal.begin('SELECT 1',[],{lease:custody.lease,ordinal:'01'})).toThrow();
  expect(readdirSync(directory).length).toBe(1);
  attempt.frame(Uint8Array.from([90,0,0,0,5,73]));attempt.finish('uncertain');
  createFileQueryJournal(directory);
  const path=join(directory,readdirSync(directory)[0]);
  expect(statSync(path).mode&0o777).toBe(0o600);
  expect(readFileSync(path,'utf8').trim().split('\n').map(x=>JSON.parse(x))).toEqual([
   {kind:'request',text:'SELECT $1',values:['9007199254740993',null,''],custody},
   {kind:'frame',hex:'5a0000000549'},{kind:'outcome',outcome:'uncertain'}]);
  expect(()=>attempt.frame(new Uint8Array())).toThrow();
  chmodSync(directory,0o755);expect(()=>createFileQueryJournal(directory)).toThrow();
 }finally{rmSync(directory,{recursive:true,force:true});}
});

test('bounded inspection retains incomplete/unknown originals without granting replay authority',()=>{
 const directory=mkdtempSync(join(tmpdir(),'truss-inspect-'));
 try{
  chmodSync(directory,0o700);const journal=createFileQueryJournal(directory);
  const custody={lease:'11111111-1111-4111-8111-111111111111',ordinal:'0'};
  const attempt=journal.begin('COMMIT',[],custody);const path=join(directory,readdirSync(directory)[0]);
  expect(inspectOriginalQueryFile(path,{maxBytes:4096}).state).toBe('incomplete');
  attempt.frame(Buffer.from('430000000b434f4d4d495400','hex'));attempt.finish('uncertain');
  const inspected=inspectOriginalQueryFile(path,{maxBytes:4096});
  expect(inspected.state).toBe('uncertain');expect(inspected.frames).toEqual(['430000000b434f4d4d495400']);
  expect(inspected.originalHex).toBe(readFileSync(path).toString('hex'));
  expect(()=>inspectOriginalQueryFile(path,{maxBytes:1})).toThrow();
  const link=join(directory,'link');symlinkSync(path,link);expect(()=>inspectOriginalQueryFile(link,{maxBytes:4096})).toThrow();
  writeFileSync(path,readFileSync(path,'utf8').replace('"kind":"request"','"unknown":true,"kind":"request"'));
  expect(inspectOriginalQueryFile(path,{maxBytes:4096}).state).toBe('invalid');
  writeFileSync(path,'{"kind":');const torn=inspectOriginalQueryFile(path,{maxBytes:4096});
  expect(torn.state).toBe('incomplete');expect(torn.originalHex).toBe(Buffer.from('{"kind":').toString('hex'));
 }finally{rmSync(directory,{recursive:true,force:true});}
});
