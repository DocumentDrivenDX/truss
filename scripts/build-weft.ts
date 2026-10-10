import {mkdir} from 'node:fs/promises';
const tsc=process.env.TRUSS_TSC ?? '/Users/erik/Projects/umf/node_modules/.bin/tsc';
await mkdir('packages/weft/dist',{recursive:true});
const result=Bun.spawnSync([tsc,'--ignoreConfig','--strict','--declaration','--emitDeclarationOnly','--target','ES2022','--module','ESNext','--moduleResolution','bundler','--outDir','packages/weft/dist','packages/weft/src/index.ts']);
if(result.exitCode)throw Error(new TextDecoder().decode(result.stdout)+new TextDecoder().decode(result.stderr));
const build=await Bun.build({entrypoints:['packages/weft/src/index.ts'],outdir:'packages/weft/dist',format:'esm',target:'browser'});
if(!build.success)throw Error('Portable package build failed');
console.log('Built portable Truss–Weft JS and declarations');
