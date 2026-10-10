import type {CapturedDataCaller, AuthorityLease, AuthorityAdmission} from './truss-authority-coordinator-v0.1';
// @ts-expect-error Caller strings cannot establish captured native identity.
const caller: CapturedDataCaller = {role: 'admin'};
// @ts-expect-error JSON marker cannot construct opaque authority lease.
const lease: AuthorityLease = {leaseIdentity: 'fixture', generation: '1'};
// @ts-expect-error Unavailable admission must not reveal a successful lease.
const disclosed: AuthorityAdmission = {outcome: 'unavailable', reason: 'authority', lease};
void [caller, lease, disclosed];
