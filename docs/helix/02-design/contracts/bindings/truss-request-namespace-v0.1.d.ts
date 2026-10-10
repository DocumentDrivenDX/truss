/** CONTRACT-009 host namespace authority candidate; no runtime qualification. */
import type {ProfilePin,ExactArtifact} from './truss-acceptance-input-v0.1';
import type {CapturedDataCaller} from './truss-authority-coordinator-v0.1';
declare const requestNamespaceGrant:unique symbol;
export type RequestNamespaceGrant={
 readonly [requestNamespaceGrant]:true;
 readonly caller:CapturedDataCaller;readonly authorizedScopeIdentity:string;
 readonly namespaceProfile:ProfilePin;readonly generation:string;
 readonly originalAdmission:ExactArtifact;
 /** Lookup existence and full replay payload are separately admitted permissions. */
 readonly lookupAllowed:boolean;readonly replayAllowed:boolean;
} & ({readonly state:'active';readonly newRequestsAllowed:boolean} |
 {readonly state:'retired';readonly newRequestsAllowed:false});
export type RequestNamespaceAdmission={readonly outcome:'admitted';readonly grant:RequestNamespaceGrant} |
 {readonly outcome:'unavailable';readonly reason:'authority'|'context'|'profile'|'observation'|'resource';readonly grant?:never};
export interface HostRequestNamespaceAuthority {
 readonly profile:ProfilePin;
 /** Asserting scope text cannot create or rotate a native trusted namespace. */
 admit(caller:CapturedDataCaller,assertedScopeIdentity:string):Promise<RequestNamespaceAdmission>;
 /** Check original issuer/caller/full immutable grant custody, never a JSON marker. */
 recognizes(grant:RequestNamespaceGrant):boolean;
 /** Fresh current namespace/caller/lifecycle observation under selected exclusions. */
 validate(grant:RequestNamespaceGrant):Promise<{readonly outcome:'current'} | {readonly outcome:'unavailable'}>;
}
