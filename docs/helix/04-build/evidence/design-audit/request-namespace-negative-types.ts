/** Opaque namespace/caller boundaries only; actual issuer/current native admission required. */
import type {RequestNamespaceGrant,RequestNamespaceAdmission} from '../../../02-design/contracts/bindings/truss-request-namespace-v0.1';
declare const grant:RequestNamespaceGrant;
// @ts-expect-error Retired namespace cannot permit new request execution.
const retired:RequestNamespaceGrant={...grant,state:'retired',newRequestsAllowed:true};
// @ts-expect-error Admission failure cannot expose a usable grant.
const refused:RequestNamespaceAdmission={outcome:'unavailable',reason:'authority',grant};
// @ts-expect-error Copying visible metadata cannot mint opaque issuer custody.
const fabricated:RequestNamespaceGrant={caller:grant.caller,authorizedScopeIdentity:grant.authorizedScopeIdentity,namespaceProfile:grant.namespaceProfile,generation:grant.generation,originalAdmission:grant.originalAdmission,lookupAllowed:true,replayAllowed:true,state:'active',newRequestsAllowed:true};
