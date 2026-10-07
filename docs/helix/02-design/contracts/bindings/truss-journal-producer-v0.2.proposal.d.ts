/** Private decoded proposal bodies only. These types grant no native authority. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {HistoricalRecord,TypedIdentity} from './truss-history-v0.1';
import type {ProposedEventContext,ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
export interface OriginalRowOperationContextProposal {
 readonly interfaceVersion:'truss-row-operation-context/0.1.0';
 readonly profile:ProfilePin;
 readonly installationIdentity:string;
 readonly originalInstallation:ExactArtifact;
 readonly originalLayout:ExactArtifact;
 readonly originalResourceProfile:ExactArtifact;
 readonly originalWriterXid:string;
 readonly operationOrdinal:string;
 readonly originalOperationDefinition:ExactArtifact;
 readonly originalExecutionContext:ExactArtifact;
 readonly originalActingRoleContext:ExactArtifact;
 readonly originalCatalogAuthorityCut:ExactArtifact;
 readonly originalOwnerUnion:ExactArtifact;
 readonly originalGroupAdmission:ExactArtifact;
 readonly addressDomain:'truss-row-operation-address/0.1.0';
 readonly authority:'actual-protected-native-registry-correspondence';
 readonly durability:'transaction-local-until-original-commit-observation';
}
export type CapturedRecordStateProposal =
 {readonly state:'absent';readonly absenceEvidence:ExactArtifact} |
 {readonly state:'present';readonly record:HistoricalRecord};
export interface JournalStartCaptureProposal {
 readonly interfaceVersion:'truss-journal-start-capture/0.2.0-proposal';
 readonly producerProfile:ProfilePin;
 readonly collectorProfile:ProfilePin;
 readonly originalOperationContext:OriginalRowOperationContextProposal;
 readonly affectedInventory:ExactArtifact;
 readonly entities:readonly {
  readonly identity:TypedIdentity;readonly kind:'object'|'relationship';
  readonly originalDefinitionContext:ExactArtifact;readonly originalHomeInventory:ExactArtifact;
  readonly start:CapturedRecordStateProposal;
 }[];
}
/** Forbid full event custody fields while preserving each operation-specific payload. */
type Payload<E extends ProposedHistoricalEvent> = E extends unknown ?
 Omit<E,keyof ProposedEventContext> & {readonly [K in keyof ProposedEventContext]?:never}:never;
export type PreparedSiblingPayloadProposal = Payload<ProposedHistoricalEvent>;
export type OrderedDeltaPayloadProposal = Payload<Extract<ProposedHistoricalEvent,
 {readonly operation:'property'|'transform'|'rebind'|'retain'}>>;
export interface JournalOrderedTransitionProposal {
 readonly interfaceVersion:'truss-journal-ordered-transition/0.2.0-proposal';
 readonly producerProfile:ProfilePin;
 readonly originalOperationContext:OriginalRowOperationContextProposal;
 readonly identity:TypedIdentity;readonly kind:'object'|'relationship';
 readonly targetRecordVersion:string;readonly effectOrdinal:string;
 readonly originalEffectEvidence:ExactArtifact;readonly nativeTransitionEvidence:ExactArtifact;
 readonly delta:OrderedDeltaPayloadProposal;
}
export type PreparedEntityProposal = {
 readonly identity:TypedIdentity;readonly kind:'object'|'relationship';readonly recordVersion:string;
 readonly start:CapturedRecordStateProposal;readonly candidateFinal:CapturedRecordStateProposal;
 readonly observedFinal:CapturedRecordStateProposal;
 readonly originalDefinitionContext:ExactArtifact;readonly completeNativeFinalEvidence:ExactArtifact;
} & ({readonly changed:true;readonly siblingOrdinals:readonly [string,...string[]]} |
     {readonly changed:false;readonly siblingOrdinals:readonly []});
export interface JournalFinalPreparationProposal {
 readonly interfaceVersion:'truss-journal-final-preparation/0.2.0-proposal';
 readonly producerProfile:ProfilePin;
 readonly originalOperationContext:OriginalRowOperationContextProposal;
 readonly originalStartCapture:ExactArtifact;readonly completeEffectInventory:ExactArtifact;
 readonly origin:ProposedEventContext['origin'];
 readonly entities:readonly PreparedEntityProposal[];
 readonly siblings:readonly {
  readonly ordinal:string;readonly identity:TypedIdentity;readonly kind:'object'|'relationship';
  readonly recordVersion:string;readonly catalogRevision:string;
  readonly originalSemanticEvidence:ExactArtifact;readonly payload:PreparedSiblingPayloadProposal;
 }[];
}
export interface JournalReservedPositionsProposal {
 readonly interfaceVersion:'truss-journal-reserved-positions/0.2.0-proposal';
 readonly producerProfile:ProfilePin;readonly allocationProfile:ProfilePin;
 readonly originalOperationContext:OriginalRowOperationContextProposal;
 readonly originalPrepared:ExactArtifact;
 readonly mapping:readonly {
  readonly ordinal:string;readonly identity:TypedIdentity;readonly kind:'object'|'relationship';
  readonly recordVersion:string;readonly seq:string;readonly originalAllocationEvidence:ExactArtifact;
 }[];
}
export interface JournalExactBytesProposal<C extends 'event'|'origin' = 'event'|'origin'> {
 readonly interfaceVersion:'truss-journal-exact-bytes/0.2.0-proposal';
 readonly eventInterfaceVersion:'truss-history-event/0.2.0-proposal';
 readonly component:C;readonly canonicalizationProfile:ProfilePin;
 readonly bytesBase64:string;readonly bytesSha256:string;
}
export interface JournalPendingPublicationProposal {
 readonly interfaceVersion:'truss-journal-pending-publication/0.2.0-proposal';
 readonly producerProfile:ProfilePin;readonly observationProfile:ProfilePin;
 readonly originalOperationContext:OriginalRowOperationContextProposal;
 readonly originalPrepared:ExactArtifact;readonly originalReservedMapping:ExactArtifact;
 readonly completeGroupInventory:ExactArtifact;readonly pendingPublicationEvidence:ExactArtifact;
 readonly rows:readonly {
  readonly ordinal:string;readonly event:ProposedHistoricalEvent;
  readonly physical:{
   readonly entityKind:'o'|'e';readonly entityId:string;readonly entityType:string;
   readonly recordVersion:string;readonly catalogRevision:string;readonly xid:string;readonly seq:string;
   readonly op:'create'|'update'|'delete'|'retain'|'rebind'|'transform'|'metadata';
   readonly propertyId:string|null;readonly atText:string;readonly dateStyle:string;readonly timeZone:string;
   readonly oldValue:null;readonly newValue:JournalExactBytesProposal<'event'>;
   readonly origin:JournalExactBytesProposal<'origin'>;
  };
  readonly nativeDescriptorEvidence:ExactArtifact;readonly actualAppendEvidence:ExactArtifact;
 }[];
 readonly durability:'pending-original-host-settlement';
}
