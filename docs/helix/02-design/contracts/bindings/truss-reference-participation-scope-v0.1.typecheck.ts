import type {ReferenceParticipationInventory,ReferenceParticipationOccurrence} from './truss-reference-participation-scope-v0.1';
import type {ExactArtifact} from './truss-acceptance-input-v0.1';
declare const evidence:ExactArtifact;
declare const occurrence:ReferenceParticipationOccurrence;
declare const inventory:ReferenceParticipationInventory;
const source:ReferenceParticipationOccurrence={...occurrence,side:'source',finalMaximum:'2'};
const target:ReferenceParticipationOccurrence={...occurrence,side:'target',finalMaximum:'1'};
// @ts-expect-error Reference source scopes have maximum two, not target-side one.
const swapped:ReferenceParticipationOccurrence={...occurrence,side:'source',finalMaximum:'1'};
// @ts-expect-error Native identifiers remain exact text, never JS numbers.
const numericId:ReferenceParticipationOccurrence={...occurrence,endpointId:123};
// @ts-expect-error Empty inventory requires independently admitted expected-empty evidence.
const unprovedEmpty:ReferenceParticipationInventory={originalTransactionContext:evidence,completeRegistryAndEffectEvidence:evidence,actorAuthorityEvidence:evidence,exclusionSnapshotEvidence:evidence,enclosingResourceEvidence:evidence,kind:'empty',occurrences:[],invocations:[]};
// @ts-expect-error Nonempty inventory cannot omit the count invocation set.
const noInvocations:ReferenceParticipationInventory={...inventory,kind:'nonempty',occurrences:[source],invocations:[],completeDeduplicationEvidence:evidence};
void source;void target;void swapped;void numericId;void unprovedEmpty;void noInvocations;
