/** Payload shape proposal only; not native retained prestate or event adoption. */
import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const path = process.argv[2];
if (!path) throw Error('Pass installed Ajv Draft 2020-12 module path');
const {default: Ajv} = await import(path);
const root = new URL('../../../02-design/contracts/', import.meta.url);
const read = (name: string) => JSON.parse(readFileSync(new URL(name, root), 'utf8'));
const ajv = new Ajv({strict: true});
ajv.addSchema(read('exact-value-v0.1.schema.json'));
const validate = ajv.compile(read('history-retain-payload-v0.1.proposal.schema.json'));
const member = {retainedName:'a/b',before:{present:false},after:{present:true,value:{kind:'null'}},beforeDefinitionContext:'original-before',afterDefinitionContext:'original-after',sourceContext:'original-source'};
const base = {interfaceVersion:'truss-history-retain-payload/0.1.0',operation:'retain',retainedChanges:[member]};
const cases: readonly [string, unknown, boolean][] = [
 ['addition',base,true],
 ['two names one payload',{...base,retainedChanges:[member,{...member,retainedName:'b'}]},true],
 ['empty literal name needs selected carrier',{...base,retainedChanges:[{...member,retainedName:''}]},true],
 ['empty inventory',{...base,retainedChanges:[]},false],
 ['replacement',{...base,retainedChanges:[{...member,before:member.after}]},false],
 ['removal',{...base,retainedChanges:[{...member,after:{present:false}}]},false],
 ['missing after value',{...base,retainedChanges:[{...member,after:{present:true}}]},false],
 ['absent with stray value',{...base,retainedChanges:[{...member,before:{present:false,value:{kind:'null'}}}]},false],
 ['empty source context',{...base,retainedChanges:[{...member,sourceContext:''}]},false],
 ['unknown field',{...base,extra:true},false],
 ['duplicate names need semantic refusal',{...base,retainedChanges:[member,member]},true],
 ['forged context needs original admission',{...base,retainedChanges:[{...member,sourceContext:'forged'}]},true],
];
const outcomes=cases.map(([name,input,expected])=>{const actual=Boolean(validate(input));if(actual!==expected)throw Error(name);return {name,expected,actual};});
const hash=(bytes: string | Buffer)=>createHash('sha256').update(bytes).digest('hex');
const validatorPackage=JSON.parse(readFileSync(new URL('../package.json',pathToFileURL(path)),'utf8'));
const sourceNames=['history-retain-payload-v0.1.proposal.schema.json','exact-value-v0.1.schema.json'];
const sourceSha256=Object.fromEntries(sourceNames.map(name=>[name,hash(readFileSync(new URL(name,root)))]));
const receipt={validator:{name:validatorPackage.name,version:validatorPackage.version},runtime:{bun:process.versions.bun ?? null,nodeCompatibility:process.versions.node},sourceSha256,helperSha256:hash(readFileSync(new URL(import.meta.url))),scope:'Proposed retained-addition payload shape only; no complete event/identity/context/prestate/native/profile qualification',cases:outcomes.length,outcomes,nativeEvidence:false,profileAdopted:false};
writeFileSync(new URL('history-retain-payload-audit.json',import.meta.url),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({passed:outcomes.length,nativeEvidence:false}));
