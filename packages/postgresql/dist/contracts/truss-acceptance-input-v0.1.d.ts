/** Proposed complete-input binding for CONTRACT-003; not runtime validation. */
export interface ProfilePin {
  readonly identity: string;
  readonly version: string;
  readonly sha256: string;
}
export interface ExactArtifact {
  readonly identity: string;
  /** Canonical RFC 4648 base64 of exact received bytes; runtime verified. */
  readonly bytesBase64: string;
  readonly sha256: string;
}
/** Canonical trees exclude host numbers, preserving tagged numeric text. */
export type CanonicalTree = null | boolean | string |
  readonly CanonicalTree[] | {readonly [member: string]: CanonicalTree};
export interface AcceptanceDocument {
  readonly documentId: string;
  readonly documentRevision: string;
  readonly artifact: ExactArtifact;
  readonly umfProfile: ProfilePin;
  readonly ingress: {readonly kind: 'native'} | {
    readonly kind: 'converted';
    readonly adapterProfile: ProfilePin;
    readonly source: ExactArtifact;
    readonly lossReport: ExactArtifact;
  };
}
export interface TransformDeclaration {
  readonly registration: ProfilePin;
  readonly targetDefinitionIdentity: string;
  readonly parameters: CanonicalTree;
}
export interface AcceptanceInput {
  readonly interfaceVersion: 'truss-acceptance-input/0.1.0';
  readonly layoutProfile: ProfilePin;
  readonly acceptanceProfile: ProfilePin;
  readonly validatorProfile: ProfilePin;
  readonly supportProfile: ProfilePin;
  /** Verified CONTRACT-003 dependency order; duplicate identities refuse. */
  readonly documents: readonly [AcceptanceDocument, ...AcceptanceDocument[]];
  readonly binding: {readonly state: 'absent'} | {
    readonly state: 'present';
    readonly vocabulary: ProfilePin;
    readonly artifact: ExactArtifact;
  };
  readonly policy: {
    readonly unknownEndpoint: 'reject' | 'provisional' | 'skip';
    readonly loss: 'strict' | 'report';
    readonly profile: ProfilePin;
  };
  readonly transforms: readonly TransformDeclaration[];
}
/** Origin belongs to an acceptance attempt; repeat never rewrites old origin. */
export interface AcceptanceAttemptContext {
  readonly assertedOrigin: CanonicalTree;
  /** Trusted host/database context, never caller-selected scope authority. */
  readonly authorizationContextIdentity: string;
}
