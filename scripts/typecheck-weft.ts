const tsc=process.env.TRUSS_TSC ?? '/Users/erik/Projects/umf/node_modules/.bin/tsc';
const run=Bun.spawnSync([tsc,'--ignoreConfig','--noEmit','--strict','--target','ES2022','--module','ESNext','--moduleResolution','bundler','packages/weft/src/index.ts']);
process.stdout.write(run.stdout);process.stderr.write(run.stderr);process.exit(run.exitCode);
