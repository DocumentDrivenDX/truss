import {test,expect} from 'bun:test';
import {verifyExactArtifacts} from '../packages/postgresql/src/index';
const limits={maxArtifacts:2,maxSingleBytes:1024,maxTotalBytes:1024};
function artifact(text:string){return {identity:'original',bytesBase64:Buffer.from(text).toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(text).digest('hex')};}
test('original opaque UMF and unknown numeric meaning stay exact across asynchronous snapshot',async()=>{
 const original='{"umf":"0.7.0","unknown":{"number":9007199254740993123456789}}';
 const input=artifact(original);const pending=verifyExactArtifacts([input],limits);input.bytesBase64='';
 const result=await pending;expect(result[0].bytesBase64).toBe(Buffer.from(original).toString('base64'));
 expect(Object.isFrozen(result)).toBe(true);expect(Object.isFrozen(result[0])).toBe(true);
});
test('original digest/canonical encoding and complete shared byte bounds refuse before success',async()=>{
 const source=artifact('abcd');
 expect(await verifyExactArtifacts([source],{...limits,maxSingleBytes:4,maxTotalBytes:4})).toEqual([source]);
 await expect(verifyExactArtifacts([source],{...limits,maxSingleBytes:3})).rejects.toThrow();
 await expect(verifyExactArtifacts([source,source],{...limits,maxTotalBytes:7})).rejects.toThrow();
 await expect(verifyExactArtifacts([{...source,sha256:'0'.repeat(64)}],limits)).rejects.toThrow();
 await expect(verifyExactArtifacts([{...artifact('a'),bytesBase64:'YR=='}],limits)).rejects.toThrow();
 let getters=0;const getter=Object.defineProperty({...source},'sha256',{get(){getters++;return source.sha256;}});
 await expect(verifyExactArtifacts([getter],limits)).rejects.toThrow();expect(getters).toBe(0);
 await expect(verifyExactArtifacts([{...source,unknown:true} as any],limits)).rejects.toThrow();
});
