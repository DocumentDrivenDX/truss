/** Private design data, not a public callable/native registration or authority permit. */
import type {ExactArtifact} from './truss-acceptance-input-v0.1';
type ScopeIdentity = {
 readonly relationshipId:string;
 readonly endpointType:string;
 readonly endpointId:string;
} & ({readonly side:'source';readonly finalMaximum:'2'} |
     {readonly side:'target';readonly finalMaximum:'1'});
export type ReferenceParticipationOccurrence = ScopeIdentity & {
 readonly originalWriterXid:string;
 readonly operationOrdinal:string;
 readonly effectGeneration:string;
 readonly originalOperation:ExactArtifact;
 readonly acceptedRelationshipDefinition:ExactArtifact;
 readonly provenance:{readonly kind:'old_effect'|'new_effect'|'catalog_population';readonly evidence:ExactArtifact};
};
export type ReferenceParticipationInvocation = ScopeIdentity & {
 /** Complete original occurrence membership and definition agreement require admission. */
 readonly occurrenceEvidence:ExactArtifact;
};
export type ReferenceParticipationInventory = {
 readonly originalTransactionContext:ExactArtifact;
 readonly completeRegistryAndEffectEvidence:ExactArtifact;
 readonly actorAuthorityEvidence:ExactArtifact;
 readonly exclusionSnapshotEvidence:ExactArtifact;
 readonly enclosingResourceEvidence:ExactArtifact;
} & ({
 readonly kind:'empty';
 readonly expectedEmptyEvidence:ExactArtifact;
 readonly occurrences:readonly [];
 readonly invocations:readonly [];
} | {
 readonly kind:'nonempty';
 readonly occurrences:readonly [ReferenceParticipationOccurrence,...ReferenceParticipationOccurrence[]];
 readonly invocations:readonly [ReferenceParticipationInvocation,...ReferenceParticipationInvocation[]];
 readonly completeDeduplicationEvidence:ExactArtifact;
});
