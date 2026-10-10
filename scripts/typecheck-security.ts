/** Check private security components independently of the ordinary Weft build. */
import {readdir} from 'node:fs/promises';
const directory='packages/postgresql/src';
const files=(await readdir(directory)).filter(name=>name.startsWith('security-')&&name.endsWith('.ts')).sort().map(name=>directory+'/'+name);
if(files.length===0)throw Error('Security sources required');
const tsc=process.env.TRUSS_TSC??new URL('../node_modules/.bin/tsc',import.meta.url).pathname;
const run=Bun.spawnSync([tsc,'--ignoreConfig','--noEmit','--strict','--target','ES2022','--module','ESNext','--moduleResolution','bundler',...files]);
process.stdout.write(run.stdout);process.stderr.write(run.stderr);process.exit(run.exitCode);
