import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
if(!process.argv[2])throw Error('Provide the installed Ajv Draft 2020-12 module path.');
const Ajv=require(process.argv[2]).default;
const ajv=new Ajv({strict:true}),root='docs/helix/02-design/contracts/';
ajv.addSchema(JSON.parse(readFileSync(root+'acceptance-input-v0.1.schema.json','utf8')));
const validate=ajv.compile(JSON.parse(readFileSync(root+'conformance-identity-paths-v0.1.proposal.schema.json','utf8')));
const pin={identity:'shape-only',version:'0.1',sha256:'0'.repeat(64)};
const base={interfaceVersion:'truss-conformance-identity-paths/0.1.0',grammarProfile:pin,
 registry:{identity:'shape-only',bytesBase64:'',sha256:'0'.repeat(64)},
 entries:[{operation:'applyInTransaction',surface:'result',surfaceProfile:pin,pointer:'/result/id',namespaceIdentity:'objects',identityProfile:pin,entityKind:'object',aliasEligible:true}]};
let count=0;
function check(name:string,wanted:boolean,change:(x:any)=>void){const x=structuredClone(base);change(x);if(Boolean(validate(x))!==wanted)throw Error(name+': '+JSON.stringify(validate.errors));count++;}
check('closed path',true,()=>{});
check('escaped occurrence',true,x=>x.entries[0].pointer='/a~1b/~0');
check('invalid escape',false,x=>x.entries[0].pointer='/a~2b');
check('missing namespace',false,x=>delete x.entries[0].namespaceIdentity);
check('missing surface profile',false,x=>delete x.entries[0].surfaceProfile);
check('not an alias domain',false,x=>x.entries[0].entityKind='journal_sequence');
check('no executable resolver',false,x=>x.entries[0].resolver='callback');
check('empty explicit inventory',true,x=>x.entries=[]);
check('duplicate requires semantic refusal',true,x=>x.entries.push(structuredClone(x.entries[0])));
check('wildcard-looking literal needs semantic resolution',true,x=>x.entries[0].pointer='/*');
console.log(count+' identity-path shape controls passed. Path eligibility, uniqueness and native identity correspondence remain unqualified.');
