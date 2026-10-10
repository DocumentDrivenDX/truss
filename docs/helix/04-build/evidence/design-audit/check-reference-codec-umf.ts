import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
const receipt=JSON.parse(readFileSync(new URL('./reference-codec-umf-compatibility.json',import.meta.url),'utf8'));
const root=process.argv[2]??'/Users/erik/Projects/umf';
const hash=(bytes:Uint8Array)=>createHash('sha256').update(bytes).digest('hex');
if(hash(readFileSync(new URL(import.meta.url)))!==receipt.checkerSha256)throw Error('Checker source pin mismatch');
if(execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim()!==receipt.umfCommit)throw Error('UMF commit pin mismatch');
for(const [path,expected] of Object.entries(receipt.sourceSha256))if(hash(readFileSync(root+'/'+path))!==expected)throw Error('UMF source pin mismatch: '+path);
const {schemaCoefficient}=await import(pathToFileURL(root+'/src/model/schema-literals.ts').href);
const valid: [string,string][]=[['9007199254740993.000','9007199254740993000'],['0.00','0'],['-0.01','-10'],['1e2','100000'],['100.00','100000'],['1.2300','1230'],['-0.000','0']];
for(const [token, expected] of valid) if(schemaCoefficient(token,3,21).toString()!==expected) throw Error(token);
const invalid=['+1','01','.1','1.','NaN','Infinity','1e','1\n','1e-4','1e18'];
for(const token of invalid){let refused=false;try{schemaCoefficient(token,3,21)}catch{refused=true}if(!refused)throw Error('unexpected admission: '+token)}
if(JSON.stringify(valid.map(([token,coefficient])=>({token,coefficient})))!==JSON.stringify(receipt.accepted)||JSON.stringify(invalid)!==JSON.stringify(receipt.refused))throw Error('Original vector receipt mismatch');
console.log(JSON.stringify({scope:'Existing UMF schemaCoefficient compatibility for proposed reference decimal vectors; no native, public-package, resource or compiler qualification',accepted:valid.map(([token,coefficient])=>({token,coefficient})),refused:invalid},null,2));
