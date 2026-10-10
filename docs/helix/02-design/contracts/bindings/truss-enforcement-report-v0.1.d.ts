/** CONTRACT-004/011 candidate; evidence authority is host-established. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
/** Document-level assertions have no fictitious module owner. Module/element
 * assertions retain the existing document-qualified module identity. */
export type AssertionOwner = QualifiedOwner |
  {readonly scope:'document';readonly documentId:string;readonly moduleId?:never};
interface AssertionSourceIdentity {
  readonly sourceKind: 'umf_document' | 'truss_binding';
  readonly owner: AssertionOwner;
  readonly definitionPin: string; readonly sourcePointer: string;
}
export type AssertionIdentity = AssertionSourceIdentity & ({
  readonly kind: 'authored'; readonly authoredIdentity: string;
} | {
  readonly kind: 'source'; readonly sourceIdentityProfile: ProfilePin;
});
interface AssertionEntry {
  readonly assertion: AssertionIdentity; readonly source: ExactArtifact;
  readonly ruleName: string;
  readonly ruleNameOrigin: 'authored' | 'profile_generated';
}
export type EnforcementEntry = AssertionEntry & ({
  readonly enforcement: 'database'; readonly procedureProfile: ProfilePin;
  readonly qualificationReceiptSha256: string; readonly installedInventorySha256: string;
  readonly currentObservationEvidenceSha256: string;
  readonly qualifiedWritePaths: readonly [string, ...string[]];
} | {
  readonly enforcement: 'engine'; readonly validatorProfile: ProfilePin;
  readonly qualificationReceiptSha256: string;
} | {
  readonly enforcement: 'none'; readonly reason: 'opaque' | 'unsupported' | 'unqualified' | 'drift';
});
export interface EnforcementReport {
  readonly interfaceVersion: 'truss-enforcement-report/0.1.0'; readonly catalogRevision: string;
  readonly reportProfile: ProfilePin; readonly layoutProfile: ProfilePin;
  readonly scope: {readonly kind: 'complete'} |
    {readonly kind: 'authorized_projection'; readonly authorizedScopeIdentity: string};
  readonly assertionInventorySha256: string; readonly entries: readonly EnforcementEntry[];
}
