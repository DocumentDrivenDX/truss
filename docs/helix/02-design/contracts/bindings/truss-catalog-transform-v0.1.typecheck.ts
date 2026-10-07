/** Design-only original registration and synchronous callback boundaries. */
import type {CatalogTransformRegistration,CatalogTransformRegistrationHandle,RegisteredCatalogTransform,CatalogTransformResult} from './truss-catalog-transform-v0.1';
declare const value:CatalogTransformRegistration;
// @ts-expect-error Plain profile/function configuration cannot mint issuer registration.
const forged:CatalogTransformRegistrationHandle=value;
// @ts-expect-error Existing callback contract is synchronous; an async host bridge needs another profile/API.
const asyncTransform:RegisteredCatalogTransform=async()=>({outcome:'candidate',after:{present:false}});
// @ts-expect-error Rejected transform cannot disclose partial candidate.
const partial:CatalogTransformResult={outcome:'rejected',code:'failure',path:[],after:{present:false}};
void forged;void asyncTransform;void partial;
