// SPDX-License-Identifier: MIT OR Apache-2.0
/** Test-only host adapter to the original UMF stage-one generator. */
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join,dirname} from 'node:path';

const [ownerRoot,fixtureRoot,destination,sourceDigest]=process.argv.slice(2);
if(!ownerRoot||!fixtureRoot||!destination||!sourceDigest||!/^[a-f0-9]{64}$/.test(sourceDigest))
 throw Error('Expected original owner source, authored fixture, fresh output and measured owner source digest');
const {generateAccessPackage}=await import(resolve(ownerRoot,'src/compilation/index.ts'));
const {validateDocument}=await import(resolve(ownerRoot,'src/validation/document.ts'));
const text=await readFile(join(fixtureRoot,'model.json'),'utf8');
const document=JSON.parse(text);
if(document.umf!=='0.10.0')throw Error('Original current-core test source required');
const validation=validateDocument(document);
if(!validation.valid)throw Error(JSON.stringify(validation));
const profile=JSON.parse(await readFile(join(fixtureRoot,'profile.json'),'utf8'));
profile.codeSha256=sourceDigest;
const request={contract:'umf-access-generate/0.1',sources:[{id:'logical',format:'json',text}],
 logical:'logical',bindings:[],records:[{module:'sales',element:'order'},{module:'sales',element:'customer'}],
 actions:[],projections:[{name:'orderIdentity',record:{module:'sales',element:'order'},fields:[{module:'sales',element:'id'}]}],
 package:'native_sales',names:[],mode:'strict',profileId:profile.id,profileVersion:profile.version,coreVersion:'0.10.0'};
const generated=generateAccessPackage(request,profile);
if(generated.outcome!=='candidate')throw Error(JSON.stringify(generated.diagnostics));
await mkdir(destination,{recursive:false});
const files:Record<string,string>={};
for(const file of generated.files){
 const path=resolve(destination,file.path);
 if(!path.startsWith(resolve(destination)+'/'))throw Error('Generated path escapes output');
 await mkdir(dirname(path),{recursive:true});await writeFile(path,file.text);
 files[file.path]=createHash('sha256').update(file.text).digest('hex');
}
await writeFile(join(destination,'stage-one-request.json'),JSON.stringify(request,null,2)+'\n');
await writeFile(join(destination,'profile.json'),JSON.stringify(profile,null,2)+'\n');
await writeFile(join(destination,'model-request.json'),JSON.stringify({binding:{modelJson:text,modelSha256:createHash('sha256').update(text).digest('hex')}})+'\n');
await writeFile(join(destination,'generation.json'),JSON.stringify({scope:'New current-core test generation; no native qualification',
 ownerSourceDigest:sourceDigest,modelSha256:createHash('sha256').update(text).digest('hex'),
 validation,inputDigest:generated.inputDigest,files},null,2)+'\n');
