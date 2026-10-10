/** CONTRACT-005 read-only authority candidate; host trust/native profile required. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
declare const dataCallerBrand: unique symbol;
declare const authorityLeaseBrand: unique symbol;
export interface CapturedDataCaller {
  readonly [dataCallerBrand]: true;
  readonly installationId: string;
  readonly dataConnectionIdentity: string;
  readonly transactionIdentity: string;
  readonly scopeIdentity: string;
  readonly captureEvidenceSha256: string;
}
export interface AuthorityLease {
  readonly [authorityLeaseBrand]: true;
  readonly leaseIdentity: string;
  readonly caller: CapturedDataCaller;
  readonly profile: ProfilePin;
  readonly generation: string;
  readonly requiredOwners: readonly [QualifiedOwner, ...QualifiedOwner[]];
  readonly ownerContextSha256: string;
  readonly admissionEvidenceSha256: string;
}
export type AuthorityAdmission = {
  readonly outcome: 'admitted'; readonly lease: AuthorityLease;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'authority' | 'context' | 'profile' | 'observation' | 'exclusion';
};
export interface AuthorityCoordinator {
  readonly profile: ProfilePin;
  admit(caller: CapturedDataCaller, owners: readonly [QualifiedOwner, ...QualifiedOwner[]]): Promise<AuthorityAdmission>;
  validateDisclosure(lease: AuthorityLease, ownerContextSha256: string): Promise<
    {readonly outcome: 'valid'} | {readonly outcome: 'unavailable'}>;
  /** Releases only coordinator exclusion; never commits/rolls back data work. */
  release(lease: AuthorityLease): Promise<
    {readonly outcome: 'released'} | {readonly outcome: 'unresolved'}>;
}
