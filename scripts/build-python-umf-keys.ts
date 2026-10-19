// SPDX-License-Identifier: MIT OR Apache-2.0
/** Keys and catalog validation share the single pinned current UMF producer. */
const repository=process.argv[2];if(!repository)throw Error('UMF repository required');
if(process.argv[3]!==undefined&&process.argv[3]!=='core10')throw Error('Only current UMF core10 key production is supported');
const built=Bun.spawnSync(['python3',new URL('./build-core10-catalog-producer.py',import.meta.url).pathname,repository],{stdout:'inherit',stderr:'inherit'});
if(built.exitCode!==0)throw Error('Current catalog/key producer build failed');
