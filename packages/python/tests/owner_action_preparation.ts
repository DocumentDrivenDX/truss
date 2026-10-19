// SPDX-License-Identifier: MIT OR Apache-2.0
// Test-only original owner oracle. This subprocess is not a Truss runtime sidecar.
const root=process.env.UMF_OWNER_ROOT;
if(!root)throw new Error('UMF_OWNER_ROOT must point to the current UMF source');
const owner=await import(root+'/src/index.ts');
const input=JSON.parse(await Bun.stdin.text());
const preparation=owner.prepareActionPlanModel(input.pin,input.action,{registry:owner.createUmfRegistry(),models:[{pin:input.pin,artifact:input.model}],actions:[{pin:input.action,artifact:input.model}],selections:[]});
console.log(JSON.stringify(preparation));
