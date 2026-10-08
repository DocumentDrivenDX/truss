import {test,expect} from 'bun:test';
import {mkdtempSync,chmodSync,readdirSync,readFileSync,statSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createFileQueryJournal} from '../packages/pg-runtime/src/journal';
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
