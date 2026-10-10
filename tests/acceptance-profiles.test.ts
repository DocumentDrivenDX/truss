import {test,expect} from 'bun:test';
import {createAcceptanceProfileResolver,requireOriginalAcceptanceProfileResolver,type AcceptanceProfileRegistration,type AcceptanceProfileRole} from '../packages/umf-bun/src/acceptance-profiles';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
function setup(){const input=structuredClone(fixture.input);const registrations:AcceptanceProfileRegistration[]=[];function pin(role:AcceptanceProfileRole){const bytes=new TextEncoder().encode('original '+role);const profile={identity:role,version:'v1',sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};registrations.push({role,profile,artifactIdentity:role+'-artifact',bytes});return profile}
 input.layoutProfile=pin('layout');input.acceptanceProfile=pin('acceptance');input.validatorProfile=pin('validator');input.supportProfile=pin('support');input.policy.profile=pin('policy');const umf=pin('umf'),adapter=pin('adapter');for(const document of input.documents){document.umfProfile=umf;if(document.ingress.kind==='converted')document.ingress.adapterProfile=adapter}if(input.binding.state==='present')input.binding.vocabulary=pin('binding');for(const transform of input.transforms)transform.registration=pin('transform');return {input,registrations}}
test('every complete input profile occurrence resolves to original bytes by role',()=>{const {input,registrations}=setup();const result=createAcceptanceProfileResolver(registrations).resolve(input);expect(result.profiles.map(item=>item.pointer)).toContain('/policy/profile');expect(result.profiles.some(item=>item.role==='adapter')).toBe(true);expect(result.profiles.some(item=>item.role==='binding')).toBe(true);expect(result.profiles.some(item=>item.role==='transform')).toBe(true);for(const item of result.profiles)expect(Buffer.from(item.artifact.bytesBase64,'base64').toString()).toBe('original '+item.role)});
test('changed hash and borrowed role cannot use same-name registration',()=>{const {input,registrations}=setup();const resolver=createAcceptanceProfileResolver(registrations);input.layoutProfile=input.supportProfile;expect(()=>resolver.resolve(input)).toThrow('/layoutProfile');input.layoutProfile={...registrations[0].profile,sha256:'0'.repeat(64)};expect(()=>resolver.resolve(input)).toThrow('/layoutProfile')});
test('original registration snapshots cannot be changed after startup',()=>{const {input,registrations}=setup();const resolver=createAcceptanceProfileResolver(registrations);input.layoutProfile={...input.layoutProfile};registrations[0].bytes.fill(0);(registrations[0].profile as any).identity='changed';expect(Buffer.from(resolver.resolve(input).profiles[0].artifact.bytesBase64,'base64').toString()).toBe('original layout')});
test('duplicate and hash-mismatched registration refuse startup',()=>{const {registrations}=setup();expect(()=>createAcceptanceProfileResolver([...registrations,registrations[0]])).toThrow('Duplicate');registrations[0].bytes.fill(0);expect(()=>createAcceptanceProfileResolver(registrations)).toThrow('hash mismatch')});
test('borrowed resolver method cannot impersonate original startup byte custody',async()=>{
 const {registrations}=setup(),original=createAcceptanceProfileResolver(registrations);
 expect(()=>requireOriginalAcceptanceProfileResolver(original)).not.toThrow();
 expect(()=>requireOriginalAcceptanceProfileResolver({...original})).toThrow('byte-custody resolver');
 let called=false;const forged={resolve(){called=true;return {profiles:Object.freeze([]),scope:'original_registered_pin_resolution_only' as const}}};
 await expect(createCatalogInputPreparation('/missing-owner','/missing-dependencies',forged)).rejects.toThrow('byte-custody resolver');
 expect(called).toBe(false);
});


test('report profile resolves in its own role and cannot borrow acceptance bytes',()=>{
 const {input,registrations}=setup();const bytes=new TextEncoder().encode('registered report procedure bytes only');
 const pin={identity:'report',version:'test',sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};
 registrations.push({role:'report',profile:pin,artifactIdentity:'report-artifact',bytes});
 const resolver=createAcceptanceProfileResolver(registrations),result=resolver.resolveReport(pin);
 expect(Buffer.from(result.artifact.bytesBase64,'base64').toString()).toBe('registered report procedure bytes only');
 expect(result.scope).toBe('original_registered_report_bytes_only');
 expect(()=>resolver.resolveReport(input.acceptanceProfile)).toThrow('report profile unavailable');
 expect(()=>resolver.resolveReport({...pin,sha256:'0'.repeat(64)})).toThrow('report profile unavailable');
 expect(resolver.resolve(input).profiles.every(item=>item.role!=='report')).toBe(true);
});

test('report startup bytes are frozen independently and duplicate report registrations refuse',()=>{
 const bytes=new TextEncoder().encode('original report'),profile={identity:'report',version:'test',sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};
 const registration={role:'report' as const,profile,artifactIdentity:'report-artifact',bytes};
 const resolver=createAcceptanceProfileResolver([registration]);bytes.fill(0);
 expect(Buffer.from(resolver.resolveReport(profile).artifact.bytesBase64,'base64').toString()).toBe('original report');
 const original={...registration,bytes:new TextEncoder().encode('original report')};
 expect(()=>createAcceptanceProfileResolver([original,original])).toThrow('Duplicate');
});
