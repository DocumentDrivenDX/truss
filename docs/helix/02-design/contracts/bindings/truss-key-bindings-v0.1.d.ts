/** CONTRACT-001/003 candidate Truss binding vocabulary, not a UMF key schema. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export interface AuthoredRecordReference {
  readonly documentId: string;
  readonly moduleId: string;
  readonly recordId: string;
  readonly definitionPin: string;
}
export interface KeyPropertyReference {
  readonly authoredPropertyId: string;
  readonly definitionPin: string;
}
interface BindingIdentity {
  readonly bindingId: string;
  readonly record: AuthoredRecordReference;
}
export type TrussKeyBinding = BindingIdentity & ({
  readonly kind: 'portable_identity';
  readonly authoredKeyId: string;
  readonly tupleProfile: ProfilePin;
  readonly transportProfile: ProfilePin;
  /** Must exactly match the source key's ordered owned fields. */
  readonly components: readonly [KeyPropertyReference,...KeyPropertyReference[]];
} | {
  readonly kind: 'storage_uniqueness';
  readonly missingComponent: 'reject' | 'omit_and_report';
  readonly encodingProfile: ProfilePin;
  readonly components: readonly [{
    readonly property: KeyPropertyReference;
    readonly equalityProfile: ProfilePin;
    readonly nullPolicy: 'reject' | 'participating_null' | 'nonparticipating';
  },...{
    readonly property: KeyPropertyReference;
    readonly equalityProfile: ProfilePin;
    readonly nullPolicy: 'reject' | 'participating_null' | 'nonparticipating';
  }[]];
});
export interface TrussKeyBindings {
  readonly interfaceVersion: 'truss-key-bindings/0.1.0';
  readonly vocabularyProfile: ProfilePin;
  readonly bindings: readonly [TrussKeyBinding,...TrussKeyBinding[]];
}
