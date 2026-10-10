import type {BootstrapCollectionRequest,BootstrapCollectionResult,BootstrapCompleteCollection,BootstrapCatalogAddress} from './truss-bootstrap-collection-result-v0.1';
import type {ExactArtifact} from './truss-acceptance-input-v0.1';
declare const request:BootstrapCollectionRequest;
declare const evidence:ExactArtifact;
declare const address:BootstrapCatalogAddress;
declare function resolveDefinitions(input:BootstrapCompleteCollection):void;
const empty:BootstrapCompleteCollection={request,observationEvidence:evidence,outcome:'complete',rawObservations:[],coverageEvidence:evidence,resourceEvidence:evidence};
resolveDefinitions(empty);
const unsupported:BootstrapCollectionResult={request,observationEvidence:evidence,outcome:'unsupported',reason:'class',unsupportedAddresses:[address]};
// @ts-expect-error Unsupported collection cannot enter complete definition resolution.
resolveDefinitions(unsupported);
// @ts-expect-error Empty raw rows cannot claim completion without coverage/resource evidence.
const missingProof:BootstrapCollectionResult={request,observationEvidence:evidence,outcome:'complete',rawObservations:[]};
// @ts-expect-error Absence requires at least one actual missing address.
const noMissingAddress:BootstrapCollectionResult={request,observationEvidence:evidence,outcome:'absent',missingAddresses:[]};
// @ts-expect-error Transport failure cannot masquerade as absent evidence.
const falseAbsence:BootstrapCollectionResult={request,observationEvidence:evidence,outcome:'absent',reason:'transport',missingAddresses:[address]};
// @ts-expect-error Frontier custody requires a nonempty original address list.
const emptyFrontier:BootstrapCollectionRequest={...request,frontier:[]};
void [missingProof,noMissingAddress,falseAbsence,emptyFrontier];

const sharedAddress:BootstrapCatalogAddress={clusterIdentity:'original-cluster',storageScope:{kind:'shared',databaseOid:'0'},classOid:'1260',objectOid:'20000',subobjectNumber:'0'};
const localAddress:BootstrapCatalogAddress={clusterIdentity:'original-cluster',storageScope:{kind:'database',databaseIdentity:'original-database',databaseOid:'16384'},classOid:'1259',objectOid:'20000',subobjectNumber:'1'};
// @ts-expect-error Shared scope cannot carry a nonzero database OID.
const wrongShared:BootstrapCatalogAddress={...sharedAddress,storageScope:{kind:'shared',databaseOid:'16384'}};
// @ts-expect-error Local scope requires original deployment database identity.
const missingDatabase:BootstrapCatalogAddress={...localAddress,storageScope:{kind:'database',databaseOid:'16384'}};
// @ts-expect-error Shared scope cannot impersonate a named database scope.
const falseDatabase:BootstrapCatalogAddress={...sharedAddress,storageScope:{kind:'shared',databaseOid:'0',databaseIdentity:'original-database'}};
void [sharedAddress,localAddress,wrongShared,missingDatabase,falseDatabase];
