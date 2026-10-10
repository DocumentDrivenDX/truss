import {createFeedLifecycleTooling} from './truss-feed-tooling-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'feed'};
const result=createFeedLifecycleTooling(assembly,selection);
if(result.status==='ok'){
 void result.value.registration.registerInTransaction;
 void result.value.extraction.extract;
 void result.value.restart.observeRestart;
 // @ts-expect-error Source tooling does not own the downstream host adapter.
 void result.value.apply;
 // @ts-expect-error Construction does not begin a transaction or commit pending work.
 void result.value.commit;
}
// @ts-expect-error A compiler capability cannot select source feed lifecycle tooling.
createFeedLifecycleTooling(assembly,{...selection,family:'weft_execution'});
