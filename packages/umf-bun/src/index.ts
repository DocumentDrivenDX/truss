/** Trusted host-only original producer registration. No alternate UMF validation. */
import {resolve} from 'node:path';
export const UMF_RUNTIME_SOURCE='c45c72a2a8a3c4fba61c40c5927dd9091acf8cc3';
export async function loadUmfProducer(directory:string){
 const root=resolve(directory);const manifest=await Bun.file(root+'/producer-manifest.json').json();
 const bytes=await Bun.file(root+'/producer.js').arrayBuffer();
 const hash=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
 if(manifest.revision!==UMF_RUNTIME_SOURCE||manifest.bundleSha256!==hash)throw Error('Original UMF producer pin mismatch');
 const owner=await import(root+'/producer.js');
 const names=['readDocument','validateDocument','validateCoreRecordValues','upgradeSchemaPropertiesEnvelope','verifySchemaPropertiesUpgrade','rollbackSchemaPropertiesEnvelope'];
 const captured=Object.fromEntries(names.map(name=>{if(typeof owner[name]!=='function')throw Error('Missing original producer');return [name,owner[name].bind(owner)]}));
 return Object.freeze({sourceRevision:UMF_RUNTIME_SOURCE,bundleSha256:hash,
  inspect(originalText:string){
   if(typeof originalText!=='string'||Buffer.byteLength(originalText)>1048576)throw Error('Original document bound');
   const source=captured.readDocument(originalText,'json');const sourceValidation=captured.validateDocument(source);
   if(!sourceValidation.valid) return {originalText,source,sourceValidation,transition:null,targetValidation:null};
   let transition=null,target=source;
   if(source.umf==='0.7.0'){
    transition=captured.upgradeSchemaPropertiesEnvelope(source);captured.verifySchemaPropertiesUpgrade(transition);
    const restored=captured.rollbackSchemaPropertiesEnvelope(transition,transition.target);
    if(JSON.stringify(restored.target)!==JSON.stringify(source))throw Error('Original transition rollback mismatch');target=transition.target;
   }else if(source.umf!=='0.8.0')throw Error('Unsupported original UMF version');
   return {originalText,source,sourceValidation,transition,targetValidation:captured.validateDocument(target),target};
  },
  checkRecord(target:unknown,identity:unknown,values:unknown){return captured.validateCoreRecordValues(target,identity,values)}
 });
}
