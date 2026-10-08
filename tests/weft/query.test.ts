import {test,expect} from 'bun:test';
import {createQueryEngine,serializeStorageBinding,WEFT_SOURCE,type Compiler,type Host,type BindingInput} from '../../packages/weft/src/index';
import {loadCompiler} from '../../packages/weft-bun/src/index';
import request from './fixtures/qualified-count.request.json';
const directory=process.env.TRUSS_WEFT_BUILD ?? '/private/tmp/truss-weft-27445317';
const compiler=await loadCompiler(directory);
const input:BindingInput={...request.target,modules:request.modules as BindingInput['modules']};
test('actual pinned Rust compiler compiles count and retains original artifact',async()=>{
 const engine=await createQueryEngine(compiler,input);const plan=await engine.compile('SELECT COUNT(*) AS total FROM Customer c');
 expect(WEFT_SOURCE).toBe('2744531735c2a771fbe7ed24a7f67e3afc851b25');
 expect(plan.artifact.backend.backendVersion).toBe('0.1.0-qualified');
 expect(plan.artifact.sql).toContain('count(*)::text');expect(Object.isFrozen(plan.artifact)).toBe(true);
 await expect(engine.execute(plan)).rejects.toThrow('Original native query host not installed');
});
test('binding and model byte substitution refuse before compiler invocation',async()=>{
 let called=false;const never:Compiler={compileJson(){called=true;throw Error('unexpected')}};
 await expect(createQueryEngine(never,{...input,bindingJson:input.bindingJson+' '})).rejects.toThrow('Binding bytes/hash mismatch');
 await expect(createQueryEngine(never,{...input,modules:[{...input.modules[0],documentJson:'{}'}]})).rejects.toThrow('Original module bytes/hash mismatch');expect(called).toBe(false);
});
test('actual compiler rejects unavailable layout/profile without executing SQL',async()=>{
 const engine=await createQueryEngine(compiler,{...input,targetProfile:'truss-reference-history/0.12'});
 await expect(engine.compile('SELECT COUNT(*) AS total FROM Customer c')).rejects.toThrow('WFT-');
});
test('unknown obligations refuse before any native acquisition',async()=>{
 let acquired=false;const host:Host={handlers:{},async withReadContext(){acquired=true;throw Error('unexpected')},async decode(){throw Error('unexpected')}};
 const engine=await createQueryEngine(compiler,input,host);const plan=await engine.compile('SELECT COUNT(*) AS total FROM Customer c');
 await expect(engine.execute(plan)).rejects.toThrow('Unknown obligation meaning');expect(acquired).toBe(false);
});
test('foreign plan and source parameter injection fail without SQL',async()=>{
 const engine=await createQueryEngine(compiler,input),other=await createQueryEngine(compiler,input);const plan=await engine.compile('SELECT COUNT(*) AS total FROM Customer c');
 await expect(other.execute(plan)).rejects.toThrow('Foreign or substituted');
 await expect(engine.compile('SELECT c.id FROM Customer c WHERE c.id > :cursor ORDER BY c.id LIMIT 2',{cursor:{family:'integer',value:'0; DROP TABLE object'}})).rejects.toThrow();
});
test('host checks precede SQL; publication recheck failure releases no result',async()=>{
 const events:string[]=[];let verifies=0;const seed=await createQueryEngine(compiler,input);const original=await seed.compile('SELECT COUNT(*) AS total FROM Customer c');
 // Unit host: this models ordering only, never claims native authorization/evidence.
 const handlers=Object.fromEntries(original.artifact.obligations.map(o=>[o.id,{accepts:(x:any)=>JSON.stringify(x)===JSON.stringify(o),async check(){events.push('check:'+o.id)}}]));
 const host:Host={handlers,async withReadContext(body){return body({async verifyContext(){events.push('context');if(++verifies===2)throw Error('context drift')},async query(){events.push('sql');return [['9007199254740993']]}})},async decode(_a,rows){events.push('decode');return rows.map(r=>({integerToken:r[0]}))}};
 const engine=await createQueryEngine(compiler,input,host);const plan=await engine.compile('SELECT COUNT(*) AS total FROM Customer c');
 await expect(engine.execute(plan)).rejects.toThrow('context drift');
 expect(events[0]).toBe('context');expect(events.indexOf('sql')).toBe(original.artifact.obligations.length+1);expect(events.at(-1)).toBe('context');
});

test('real queries exercise exact numeric, whole record, presence and logical-key parameters',async()=>{
 const engine=await createQueryEngine(compiler,input);
 const queries=[
  'SELECT c.* FROM Customer c ORDER BY c.id LIMIT 10',
  'SELECT c.id,c.nickname,c.tags,c.address FROM Customer c ORDER BY c.id LIMIT 10',
  'SELECT SUM(o.total) AS total FROM Orders o',
  'SELECT c.name,COUNT(*) AS total FROM Customer c GROUP BY c.name ORDER BY c.name LIMIT 1000'
 ];
 for(const sql of queries){const plan=await engine.compile(sql);expect(plan.artifact.sql.length).toBeGreaterThan(0)}
 const paged=await engine.compile('SELECT c.id FROM Customer c WHERE c.id > :cursor ORDER BY c.id LIMIT 2',{cursor:{family:'integer',value:'9007199254740993'}});
 expect(paged.artifact.parameters.some(p=>p.value==='9007199254740993')).toBe(true);
 const quoted=await engine.compile('SELECT c.id FROM Customer c WHERE c.name = :name ORDER BY c.id LIMIT 20',{name:{family:'string',value:"x'; DROP TABLE object; --"}});
 expect(quoted.artifact.sql).not.toContain('DROP TABLE');expect(quoted.artifact.parameters.some(p=>p.value.includes('DROP TABLE'))).toBe(true);
});

test('owner binding serializer refuses fixture catalog and altered embedded artifact',async()=>{
 const binding=JSON.parse(input.bindingJson);
 const source={binding,modules:input.modules,backendVersion:input.backendVersion,targetProfile:input.targetProfile};
 await expect(serializeStorageBinding(source)).rejects.toThrow('Positive original accepted catalog revision');
 binding.basis.catalogRevision='1';binding.basis.acceptedCatalog.bytesBase64='W10=';
 await expect(serializeStorageBinding(source)).rejects.toThrow('Original artifact hash mismatch');
});

test('unsupported aggregate filter is an explicit compiler refusal, never host rewrite',async()=>{
 const engine=await createQueryEngine(compiler,input);
 await expect(engine.compile('SELECT SUM(o.total) AS total FROM Orders o WHERE o.id < :cursor',{cursor:{family:'integer',value:'0'}})).rejects.toThrow('WFT-UNSUPPORTED');
});
