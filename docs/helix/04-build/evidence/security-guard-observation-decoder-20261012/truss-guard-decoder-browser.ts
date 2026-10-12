import {decodeCandidateAuthorityGuard} from '/private/tmp/truss-security-main-integration/packages/postgresql/src/security-guard-observation';
(globalThis as any).guardDecode=(input:unknown)=>decodeCandidateAuthorityGuard(input);
