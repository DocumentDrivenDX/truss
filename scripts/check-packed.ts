/** Empty packed consumer; no driver, network, database, bootstrap or compiler startup. */
import {mkdtemp, mkdir, readFile, writeFile, readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve, join} from 'node:path';
const root = resolve(import.meta.dir, '..');
const arg = process.argv.indexOf('--tsc');
const compiler = arg >= 0 ? process.argv[arg + 1] : Bun.resolveSync('typescript/bin/tsc', root);
if (!compiler) throw Error('Explicit compiler required');
const temporary = await mkdtemp(join(tmpdir(), 'truss-inert-packed-'));
const pkg = resolve(root, 'packages/postgresql');
const archive = resolve(temporary, 'truss-postgresql.tgz');
const run = (args: string[], cwd: string) => {
  const result = Bun.spawnSync(args, {cwd});
  return {status: result.exitCode, output: new TextDecoder().decode(result.stdout) + new TextDecoder().decode(result.stderr)};
};
let result = run(['/usr/bin/tar', '-czf', archive, '-C', pkg, 'package.json', 'dist'], root);
if (result.status !== 0) throw Error(result.output);
const installed = resolve(temporary, 'node_modules/@documentdrivendx/truss-postgresql');
await mkdir(installed, {recursive: true});
result = run(['/usr/bin/tar', '-xzf', archive, '-C', installed], root);
if (result.status !== 0) throw Error(result.output);
await writeFile(resolve(temporary, 'package.json'), '{"type":"module"}\n');
const consumer = `import {createReferenceAssembly,INERT_ASSEMBLY_PROFILE} from '@documentdrivendx/truss-postgresql';
import type {Executor,TransactionHandle,ReferenceAssembly,ProfilePin} from '@documentdrivendx/truss-postgresql';
const p:ProfilePin={identity:'fixture-unqualified',version:'0.12',sha256:'a'.repeat(64)};
let calls=0;const fail=async():Promise<never>=>{calls++;throw Error('Unexpected native call')};
const executor:Executor<unknown>={withTransaction:fail,adoptTransaction:fail,execute:fail,savepoint:fail,rollbackToSavepoint:fail,releaseSavepoint:fail};
const selection={family:'direct_read' as const,capabilityProfile:p,layoutProfile:p,adapterProfile:p,valueProfile:p,policyProfile:p};
const result=createReferenceAssembly({interfaceVersion:'truss-reference-assembly/0.1.0',assemblyId:'packed-fixture',assemblyProfile:INERT_ASSEMBLY_PROFILE,recovery:{registryProfile:p,retention:'process_lifetime'},databaseIdentity:'uninstalled-fixture',schema:'truss',capabilities:[selection]},executor,{recoveryRegistry:{profile:p,retention:'process_lifetime',register:fail,append:fail,inspect:fail}});
if(result.status!=='ok')throw Error('Inert construction failed');
const assembly:ReferenceAssembly=result.value;
// The adapter's and public assembly's transaction parameter share one brand.
type Direct=Extract<ReturnType<ReferenceAssembly['directReads']>,{status:'ok'}>['capability'];
function useAdapterTransaction(transaction:TransactionHandle,request:Parameters<Direct['lookup']>[1]){const direct=assembly.directReads(selection);if(direct.status==='ok'){return direct.capability.lookup(transaction,request)}};
void useAdapterTransaction;
const readiness=await assembly.observeReadiness(selection);
if(readiness.status!=='ok'||readiness.value.state!=='unverified')throw Error('Fabricated readiness');
await assembly.dispose({});if(calls!==0)throw Error('Construction invoked host services');
console.log('Packed inert consumer passed; native calls='+calls);
`;
await writeFile(resolve(temporary, 'consumer.ts'), consumer);
const args = [process.execPath, compiler, '--strict', '--noEmit', '--target', 'ES2022', '--module', 'ESNext', '--moduleResolution', 'Bundler', '--lib', 'ES2022,DOM'];
result = run([...args, 'consumer.ts'], temporary);
if (result.status !== 0) throw Error(result.output);
result = run([process.execPath, 'consumer.ts'], temporary);
if (result.status !== 0) throw Error(result.output);
const executed = result.output;
await writeFile(resolve(temporary, 'forged.ts'), `import type {TransactionHandle} from '@documentdrivendx/truss-postgresql';
declare const counterfeit:unique symbol;
declare const copied:{readonly [counterfeit]:true;readonly ownership:'engine';readonly isolation:'serializable';readonly accessMode:'read_write'};
const original:TransactionHandle=copied;void original;\n`);
result = run([...args, 'forged.ts'], temporary);
if (result.status === 0 || !result.output.includes('transactionBrand')) throw Error('Counterfeit transaction brand was admitted or wrong refusal');
const declared = await readdir(resolve(installed, 'dist/contracts'));
const brandDeclarations = (await Promise.all(declared.map(name => readFile(resolve(installed, 'dist/contracts', name), 'utf8')))).join('\n').match(/declare const transactionBrand: unique symbol/g) ?? [];
if (brandDeclarations.length !== 1) throw Error('Transaction brand declaration duplicated');
const hash = (value: Uint8Array | string) => new Bun.CryptoHasher('sha256').update(value).digest('hex');
const evidence = {interfaceVersion: 'truss-packed-inert-check/0.1.0', loader: 'bun/' + Bun.version, archiveSha256: hash(await Bun.file(archive).bytes()),
  declarationFiles: declared.length, transactionBrandDeclarations: brandDeclarations.length,
  cleanConsumerTypecheck: true, cleanConsumerRuntime: true, counterfeitBrandRefused: true, nativeCalls: 0,
  qualification: 'Private experimental inert assembly only. No native installation, UMF interpretation, schema/data mutation/feed, Node/browser or release support.'};
await mkdir(resolve(root, 'docs/helix/04-build/evidence/inert-assembly'), {recursive: true});
await writeFile(resolve(root, 'docs/helix/04-build/evidence/inert-assembly/packed-consumer.ts'), consumer);
await writeFile(resolve(root, 'docs/helix/04-build/evidence/inert-assembly/packed-check.json'), JSON.stringify(evidence, null, 2) + '\n');
console.log(executed.trim());console.log('Canonical brand counterfeit refused; '+declared.length+' public declaration chunks verified.');
