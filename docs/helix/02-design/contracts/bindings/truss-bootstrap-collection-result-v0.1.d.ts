/** CONTRACT-008 draft internal dispatch carrier; not public diagnostics or qualification. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
export interface BootstrapCatalogAddress {
 readonly clusterIdentity:string;
 readonly storageScope:{readonly kind:'database';readonly databaseIdentity:string;readonly databaseOid:string} |
  {readonly kind:'shared';readonly databaseOid:'0'};
 /** Exact native oid/int4 decimal text; class OID is target-local, not a global enum. */
 readonly classOid:string;readonly objectOid:string;readonly subobjectNumber:string;
}
export interface BootstrapCollectionRequest {
 readonly interfaceVersion:'truss-bootstrap-collection-request/0.1.0';
 readonly collectionProfile:ProfilePin;
 readonly routeProfile:ProfilePin;
 readonly originalScope:ExactArtifact;
 readonly originalCut:ExactArtifact;
 readonly frontier:readonly [BootstrapCatalogAddress,...BootstrapCatalogAddress[]];
}
interface OutcomeBasis {
 readonly request:BootstrapCollectionRequest;
 /** Internal evidence retained under original observer authority. */
 readonly observationEvidence:ExactArtifact;
}
export type BootstrapCollectionResult =
 (OutcomeBasis & {readonly outcome:'complete';
  readonly rawObservations:readonly ExactArtifact[];
  /** Includes fanout membership and admitted empty parent scope, not row count alone. */
  readonly coverageEvidence:ExactArtifact;
  readonly resourceEvidence:ExactArtifact}) |
 (OutcomeBasis & {readonly outcome:'absent';
  readonly missingAddresses:readonly [BootstrapCatalogAddress,...BootstrapCatalogAddress[]]}) |
 (OutcomeBasis & {readonly outcome:'unavailable';
  readonly reason:'authority'|'cut'|'transport'|'resource'|'cancelled';
  readonly unresolvedScope:ExactArtifact}) |
 (OutcomeBasis & {readonly outcome:'unsupported';
  readonly reason:'class'|'subobject'|'meaning'|'profile';
  readonly unsupportedAddresses:readonly [BootstrapCatalogAddress,...BootstrapCatalogAddress[]]});
/** Internal runtime admits complete coverage independently before definition resolution. */
export type BootstrapCompleteCollection = Extract<BootstrapCollectionResult,{outcome:'complete'}>;
